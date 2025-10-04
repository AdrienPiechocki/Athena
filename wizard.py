import sys
import os
import platform
import subprocess
import shutil
import time
import configparser
import json
import requests
import zipfile
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QSizePolicy, QScrollArea, QGridLayout, QStackedWidget,
    QCheckBox, QMessageBox, QProgressBar, QLineEdit, QTextEdit
)
from PySide6.QtCore import QThread, Signal, QSize, Qt, QTimer
from PySide6.QtGui import QFont, QIcon
import __main__

def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(getattr(__main__, '__file__', sys.argv[0])))
    return os.path.join(base_path, relative_path)

config_path = resource_path("settings/config.cfg")
lang_dir = resource_path("lang")
data_dir = resource_path("data")

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

# --- Worker pour installation ---
class InstallerThread(QThread):
    finished_signal = Signal(bool)
    log_signal = Signal(str)
    progress_signal = Signal(int)

    def __init__(self, config, lang, parent=None, vosk_url=None):
        super().__init__(parent)
        self.config = config
        self.lang = lang
        self.system = platform.system().lower()
        self.vosk_url = vosk_url
        
    def run_command(self, cmd, silent=False):
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
        self.log_signal.emit(f"➡️ {self.lang['executing']} : {cmd_str}")
        try:
            # Remplace sudo par pkexec pour la GUI
            if "sudo" in cmd:
                cmd[0] = "pkexec"
            if silent:
                subprocess.check_call(cmd, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.check_call(cmd, shell=False)
        except subprocess.CalledProcessError:
            self.log_signal.emit(f"❌ {self.lang['exec error']} : {cmd_str}")

    def progress_step(self, description, duration=2):
        steps = duration * 20
        for i in range(steps):
            self.progress_signal.emit(int((i+1)/steps*100))
            time.sleep(0.05)
        self.progress_signal.emit(0)

    def install_vosk_model(self):
        if not self.vosk_url:
            self.log_signal.emit(f"⚠️ {self.lang['ignore vosk']}")
            return

        local_zip = self.vosk_url.split("/")[-1]
        filename = local_zip[:-4]
        extract_folder = os.path.join(BASE_DIR, "vosk")
        model_path = os.path.join(extract_folder, filename)

        if os.path.exists(model_path):
            self.config.set("Voice", "vosk", model_path)
            with open(config_path, "w") as configfile:
                self.config.write(configfile)
            self.log_signal.emit(f"✅ {self.lang['vosk already here']} : {model_path}")
            return

        os.makedirs(extract_folder, exist_ok=True)
        self.log_signal.emit(f"⬇️ {self.lang['downloading vosk']} {self.vosk_url}")

        with requests.get(self.vosk_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(local_zip, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = int(downloaded * 100 / total_size)
                        self.progress_signal.emit(percent)
                        QApplication.processEvents()

        self.log_signal.emit(f"📦 {self.lang['vosk extraction']}...")
        with zipfile.ZipFile(local_zip, "r") as zip_ref:
            zip_ref.extractall(extract_folder)

        self.config.set("Voice", "vosk", model_path)
        with open(config_path, "w") as configfile:
            self.config.write(configfile)

        os.remove(local_zip)
        self.log_signal.emit(f"✅ {self.lang['vosk installed']} : {model_path}")
        self.progress_signal.emit(100)


    def install_requirements_venv(self):
        venv_dir = os.path.join(BASE_DIR, ".venv")
        venv_python = os.path.join(venv_dir, "bin", "python") if os.name != "nt" else os.path.join(venv_dir, "Scripts", "python.exe")
        venv_pip = [venv_python, "-m", "pip"]

        if not os.path.exists(venv_dir):
            self.log_signal.emit(f"🧩 {self.lang['venv creation']}")
            self.run_command([sys.executable, "-m", "venv", venv_dir])
        else:
            self.log_signal.emit(f"🔄 {self.lang['venv update']}")

        self.run_command(venv_pip + ["install", "--upgrade", "pip"])

        requirements = os.path.join(BASE_DIR, "requirements.txt")
        if os.path.exists(requirements):
            self.progress_step(self.lang["python install"], 2)
            self.run_command(venv_pip + ["install", "--upgrade", "-r", requirements])
        else:
            self.log_signal.emit(f"⚠️ {self.lang['no requirements found']}")

    def install_ollama_model(self):
        if shutil.which("ollama"):
            self.progress_step(self.lang["qwen3 install"], 3)
            self.run_command(["ollama", "pull", "qwen3"])
        else:
            self.log_signal.emit(f"⚠️ {self.lang['ollama not found']}")

    def install_linux(self):
        self.log_signal.emit(f"🐧 {self.lang['linux install']}")
        if shutil.which("apt"):
            pkg_manager = "apt"
        elif shutil.which("pacman"):
            pkg_manager = "pacman"
        elif shutil.which("dnf"):
            pkg_manager = "dnf"
        else:
            self.log_signal.emit(f"❌ {self.lang['no package manager']}")
            return

        self.progress_step(self.lang["package update"], 2)
        if pkg_manager == "apt":
            self.run_command(["sudo", "apt", "update"])
        elif pkg_manager == "pacman":
            self.run_command(["sudo", "pacman", "-Sy"])
        elif pkg_manager == "dnf":
            self.run_command(["sudo", "dnf", "makecache"])

        self.progress_step(self.lang["packages installation"], 3)
        packages = ["flameshot", "wmctrl", "espeak-ng", "curl"]
        if pkg_manager == "apt":
            self.run_command(["sudo", "apt", "install", "-y"] + packages)
        elif pkg_manager == "pacman":
            self.run_command(["sudo", "pacman", "-S", "--noconfirm"] + packages)
        elif pkg_manager == "dnf":
            self.run_command(["sudo", "dnf", "install", "-y"] + packages)

        if not shutil.which("ollama"):
            self.run_command("curl -fsSL https://ollama.com/install.sh | sh", shell=True)

        self.install_ollama_model()

    def install_windows(self):
        self.log_signal.emit(f"🪟 {self.lang['windows install']}")
        if not shutil.which("espeak-ng"):
            self.progress_step(self.ang["espeak install"], 2)
            self.run_command(["winget", "install", "-e", "--id", "espeak-ng.espeak-ng"])
        if not shutil.which("ollama"):
            self.progress_step(self.lang["ollama install"], 2)
            self.run_command(["winget", "install", "-e", "--id", "Ollama.Ollama"])
        self.install_ollama_model()

    def run(self):
        try:
            if "linux" in self.system:
                self.install_linux()
            elif "windows" in self.system:
                self.install_windows()
            else:
                self.log_signal.emit(f"❌ {self.lang['wrong system']} : {self.system}")
                return

            self.install_requirements_venv()
            if self.config.get("General", "lang", fallback="en_US") == "en_US":
                self.vosk_url = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"

            elif self.config.get("General", "lang", fallback="en_US") == "fr_FR":
                self.vosk_url = "https://alphacephei.com/vosk/models/vosk-model-fr-0.22.zip"
            self.install_vosk_model()
            self.progress_step(self.lang["finish install"], 2)
            self.log_signal.emit(f"✅ {self.lang['install success']}")

            self.finished_signal.emit(True) 

        except Exception as e:
            self.log_signal.emit(f"❌ {str(e)}")
            self.finished_signal.emit(False)

# --- UI principale ---
class InstallerUI(QWidget):
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.lang = {}

        layout = QVBoxLayout()

        self.label = QLabel("")
        self.label.setFocusPolicy(Qt.StrongFocus)
        layout.addWidget(self.label)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.log)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.button_layout = QVBoxLayout()

        self.start_button = QPushButton("")
        self.start_button.setFocusPolicy(Qt.StrongFocus)
        self.start_button.clicked.connect(self.start_installation)
        self.button_layout.addWidget(self.start_button)

        self.back_button = QPushButton("")
        self.back_button.setFocusPolicy(Qt.StrongFocus)
        self.back_button.clicked.connect(self.on_back_clicked)
        self.button_layout.addWidget(self.back_button)

        layout.addLayout(self.button_layout)
        self.setLayout(layout)

        self.log.setTabChangesFocus(True)
        self.setTabOrder(self.label, self.log)
        self.setTabOrder(self.log, self.progress)
        self.setTabOrder(self.progress, self.start_button)
        self.setTabOrder(self.start_button, self.back_button)

        QTimer.singleShot(0, self.start_button.setFocus)

    def start_installation(self):
        self.thread = InstallerThread(self.config, self.lang)
        self.thread.finished_signal.connect(self.on_installation_finished)
        self.thread.log_signal.connect(self.append_log)
        self.thread.progress_signal.connect(self.progress.setValue)
        self.thread.start()
        self.start_button.setEnabled(False)
        self.back_button.setEnabled(False)

    def append_log(self, text):
        self.log.append(text)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def load_language(self):
        self.config.read(config_path)
        lang_code = self.config.get("General", "lang", fallback="en_US")
        lang_file = os.path.join(lang_dir, f"{lang_code}.json")
        with open(lang_file, "r", encoding="utf-8") as f:
            self.lang = json.load(f)

        self.label.setText(f"<h2>{self.lang['auto-install title']}</h2>")
        self.label.setAccessibleDescription(self.lang['auto-install title'])
        self.start_button.setText(self.lang["start install"])
        self.start_button.setAccessibleDescription(self.lang["start install"])

        self.back_button.setText(self.lang["back button"])
        self.back_button.setAccessibleDescription(self.lang["back button"])

    def on_back_clicked(self):
        self.back_clicked.emit()

    def on_installation_finished(self, success):
        msg = QMessageBox(self)
        if success:
            msg.setWindowTitle(self.lang["install success"])
            msg.setText(self.lang["please restart"])
            msg.setIcon(QMessageBox.Information)
        else:
            msg.setWindowTitle(self.lang["install failed"])
            msg.setText(self.lang["please restart"])
            msg.setIcon(QMessageBox.Critical)

        msg.setStandardButtons(QMessageBox.Ok)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #000000;
                color: #FFFF00;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #0000FF;
                color: #FFFFFF;
                border: 3px solid #FFFFFF;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
        """)
        msg.exec()

        self.config.set("General", "wizard", "true")
        with open(config_path, "w") as configfile:
            self.config.write(configfile)
        sys.exit(0)



class SelectLanguage(QWidget):
    language_selected = Signal(str)

    config = configparser.ConfigParser()
    config.read(config_path)

    def __init__(self):
        super().__init__()

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        # ScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFocusPolicy(Qt.NoFocus)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.layout.addWidget(self.scroll_area)

        # Inner Widget
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)

        # Inner vertical layout
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(20)

        # Label
        text = "Welcome to Athena's installation process. Please select a Language."
        self.label = QLabel(text)
        self.label.setAccessibleDescription(text)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFocusPolicy(Qt.StrongFocus)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_layout.addWidget(self.label)

        # Buttons grid
        self.grid_widget = QWidget()
        self.button_grid = QGridLayout()
        self.button_grid.setSpacing(10)
        self.grid_widget.setLayout(self.button_grid)
        self.scroll_layout.addWidget(self.grid_widget)

        self.languages = {
            "Français": {
                "icon": os.path.join(data_dir, "flags", "fr.svg"),
                "lang": "fr_FR"
            },
            "English": {
                "icon": os.path.join(data_dir, "flags", "us.svg"),
                "lang": "en_US"
            }
        }
        self.min_button_width = 150
        self.buttons = []

        # Initial buttons creation
        self.create_buttons(columns=3)



    def create_buttons(self, columns: int):
        for btn in self.buttons:
            self.button_grid.removeWidget(btn)
            btn.deleteLater()
        self.buttons.clear()

        for index, lang in enumerate(self.languages.keys()):
            button = QPushButton(lang)
            button.setAccessibleDescription(lang)
            button.setFocusPolicy(Qt.StrongFocus)
            # Add flag if available
            if "icon" in self.languages[lang]:
                button.setIcon(QIcon(self.languages[lang]["icon"]))
                button.setIconSize(QSize(64, 64))  # flag size

            button.clicked.connect(lambda checked, l=lang: self.on_button_clicked(l))
            self.button_grid.addWidget(button, index // columns, index % columns)
            self.buttons.append(button)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self.scroll_area.height() // 15
        font = QFont("Arial", size)
        if not font.exactMatch():
            font = QFont("Sans Serif", size)
        self.label.setFont(font)
        for btn in self.buttons:
            btn.setFont(font)

    def on_button_clicked(self, language: str):
        self.config.set("General", "lang", self.languages[language]["lang"])
        with open(config_path, "w") as configfile:
            self.config.write(configfile)
        self.language_selected.emit(language)

class SelectModules(QWidget):
    
    modules_validated = Signal(list)
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.lang = {}

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        # ScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFocusPolicy(Qt.NoFocus)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.layout.addWidget(self.scroll_area)

        # Inner Widget
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)

        # Inner vertical layout
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(20)

        # Label
        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFocusPolicy(Qt.StrongFocus)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_layout.addWidget(self.label)

        # Checkboxes
        self.checkboxes = []
        
        # Back button
        self.back_button = QPushButton("")
        self.back_button.setFocusPolicy(Qt.StrongFocus)
        self.back_button.clicked.connect(self.on_back_clicked)
        self.scroll_layout.addWidget(self.back_button)

        # Next button
        self.next_button = QPushButton("")
        self.next_button.setFocusPolicy(Qt.StrongFocus)
        self.next_button.clicked.connect(self.on_next_clicked)
        self.scroll_layout.addWidget(self.next_button)

    def load_language(self):
        self.config.read(config_path)
        lang_code = self.config.get("General", "lang", fallback="en_US")
        lang_file = os.path.join(lang_dir, f"{lang_code}.json")
        with open(lang_file, "r", encoding="utf-8") as f:
            self.lang = json.load(f)

        self.label.setText(self.lang["module selection"])
        self.label.setAccessibleDescription(self.lang["module selection"])

        for cb in self.checkboxes:
            self.scroll_layout.removeWidget(cb)
            cb.deleteLater()
        self.checkboxes.clear()

        self.modules = [self.lang["voice module"], self.lang["slider module"]]
        for mod in self.modules:
            checkbox = QCheckBox(mod)
            checkbox.setAccessibleDescription(mod)
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 2, checkbox)  
            self.checkboxes.append(checkbox)

        self.back_button.setText(self.lang["back button"])
        self.back_button.setAccessibleDescription(self.lang["back button"])
        self.next_button.setText(self.lang["next button"])
        self.next_button.setAccessibleDescription(self.lang["next button"])
        
        self.update_tab_order()
    
    def update_tab_order(self):
        if not self.checkboxes:
            return
        previous = self.label
        for cb in self.checkboxes:
            self.setTabOrder(previous, cb)
            previous = cb
        self.setTabOrder(previous, self.back_button)
        self.setTabOrder(self.back_button, self.next_button)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self.scroll_area.height() // 15
        font = QFont("Arial", size)
        if not font.exactMatch():
            font = QFont("Sans Serif", size)
        self.label.setFont(font)
        for cb in self.checkboxes:
            cb.setFont(font)
        self.next_button.setFont(font)
        self.back_button.setFont(font)

    def get_selected_modules(self):
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]


    def on_next_clicked(self):
        selected = self.get_selected_modules()
        if self.lang["voice module"] in selected:
            self.config.set("Modules", "voice", "true")
        else:
            self.config.set("Modules", "voice", "false")
        
        if self.lang["slider module"] in selected:
            self.config.set("Modules", "slider", "true")
        else:
            self.config.set("Modules", "slider", "false")
        with open(config_path, "w") as configfile:
            self.config.write(configfile)
        self.modules_validated.emit(selected)

    def on_back_clicked(self):
        self.back_clicked.emit()

class SelectUsername(QWidget):
    
    username_validated = Signal(str)
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.lang = {}
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        # ScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFocusPolicy(Qt.NoFocus)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.layout.addWidget(self.scroll_area)

        # Inner Widget
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)

        # Inner vertical layout
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(20)

        # Label
        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFocusPolicy(Qt.StrongFocus)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_layout.addWidget(self.label)

        # Input
        self.username_input = QLineEdit("")
        self.username_input.setPlaceholderText("...")  
        self.username_input.setFocusPolicy(Qt.StrongFocus)
        self.scroll_layout.addWidget(self.username_input)        

        # Back button
        self.back_button = QPushButton("")
        self.back_button.setFocusPolicy(Qt.StrongFocus)
        self.back_button.clicked.connect(self.on_back_clicked)
        self.scroll_layout.addWidget(self.back_button)

        # Next button
        self.next_button = QPushButton("")
        self.next_button.setFocusPolicy(Qt.StrongFocus)
        self.next_button.clicked.connect(self.on_next_clicked)
        self.scroll_layout.addWidget(self.next_button)

    def load_language(self):
        self.config.read(config_path)
        lang_code = self.config.get("General", "lang", fallback="en_US")
        lang_file = os.path.join(lang_dir, f"{lang_code}.json")
        with open(lang_file, "r", encoding="utf-8") as f:
            self.lang = json.load(f)

        self.label.setText(self.lang["ask username"])
        self.label.setAccessibleDescription(self.lang["ask username"])
        self.back_button.setText(self.lang["back button"])
        self.back_button.setAccessibleDescription(self.lang["back button"])
        self.next_button.setText(self.lang["next button"])
        self.next_button.setAccessibleDescription(self.lang["next button"])
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self.scroll_area.height() // 15
        font = QFont("Arial", size)
        if not font.exactMatch():
            font = QFont("Sans Serif", size)
        self.label.setFont(font)
        self.username_input.setFont(font)
        self.next_button.setFont(font)
        self.back_button.setFont(font)
        
    def on_next_clicked(self):
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "Error", self.lang["no username error"])
            return

        self.config.set("General", "username", username)
        with open(config_path, "w") as configfile:
            self.config.write(configfile)

        self.username_validated.emit(username)

    def on_back_clicked(self):
        self.back_clicked.emit()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Athena")
        self.resize(800, 600)

        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.lang = {}

        # Layout principal
        self.layout = QVBoxLayout(self)

        # Page 1 : Language selection
        self.language_selection = SelectLanguage()
        self.language_selection.language_selected.connect(self.show_username_selection)

        # Page 2 : Username selection
        self.username_selection = SelectUsername()
        self.username_selection.username_validated.connect(self.show_option_selection)
        self.username_selection.back_clicked.connect(self.show_language_selection)

        # Page 3 : Modules selection
        self.modules_selection = SelectModules()
        self.modules_selection.modules_validated.connect(self.show_installer)
        self.modules_selection.back_clicked.connect(self.show_username_selection)

        # Page 4 : installation
        self.installer = InstallerUI()
        self.installer.back_clicked.connect(self.show_option_selection)

        self.pages = [self.language_selection, self.username_selection ,self.modules_selection, self.installer]
        for page in self.pages:
            self.layout.addWidget(page)

        self.show_page(self.language_selection)
    
        # Styles
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
                color: #FFFF00;
                font-family: Arial, sans-serif;
            }
            QLabel {
                padding: 15px;
            }
            QLabel:focus {
                border: 4px solid #FFA500;
                outline: none;
            }
            QPushButton {
                background-color: #0000FF;
                color: #FFFFFF;
                border: 3px solid #FFFFFF;
                border-radius: 8px;
                padding: 15px;
            }
            QPushButton:focus {
                border: 4px solid #FFA500;
                outline: none;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
            QCheckBox {
                spacing: 12px;
                padding: 8px;
            }
            QCheckBox:focus {
                border: 2px solid #FFA500;
                outline: none;
            }
            QCheckBox::indicator {
                width: 32px;
                height: 32px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #FFFFFF;
                background-color: #000000;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #FFFFFF;
                background-color: #FFA500;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #FFA500;
            }
            QLineEdit {
                padding: 15px;
                border: 4px solid #0000FF;
            }
            QLineEdit:focus {
                border: 4px solid #FFA500;
                outline: none;
            }
            QTextEdit {
                background-color: #111111;
                color: #FFFF00;
                border: 2px solid #FFFFFF;
            }
            QProgressBar {
                border: 2px solid #FFFFFF;
                border-radius: 5px;
                text-align: center;
                color: #FFFF00;
            }
            QProgressBar::chunk {
                background-color: #1E90FF;
            }
        """)

    def show_page(self, page: QWidget):
        for p in self.pages:
            p.setVisible(p is page)

    def show_language_selection(self):
        self.show_page(self.language_selection)

    def show_option_selection(self):
        self.modules_selection.load_language()
        self.show_page(self.modules_selection)
    
    def show_username_selection(self):
        self.username_selection.load_language()
        self.show_page(self.username_selection)

    def show_installer(self):
        self.installer.load_language()
        self.show_page(self.installer)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
