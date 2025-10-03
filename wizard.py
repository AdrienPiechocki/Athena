from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QSizePolicy, QScrollArea, QGridLayout, QStackedWidget,
    QCheckBox, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QIcon
import sys
import configparser
import json
import os
import requests
import zipfile
import pathlib
import subprocess
import platform

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
config_path = os.path.join(BASE_DIR, "settings", "config.cfg")
system = platform.system()

class SelectLanguage(QWidget):
    global config_path
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
                "icon": os.path.join("data", "flags", "fr.svg"),
                "lang": "fr_FR"
            },
            "English": {
                "icon": os.path.join("data", "flags", "us.svg"),
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

        global config_path
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
        global BASE_DIR, config_path
        self.config.read(config_path)
        lang_code = self.config.get("General", "lang", fallback="en_US")
        lang_file = os.path.join(BASE_DIR, "lang", f"{lang_code}.json")
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


class InstallVosk(QWidget):
    def __init__(self):
        super().__init__()
        global config_path
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

    def load_language(self):
        global BASE_DIR, config_path
        self.config.read(config_path)
        lang_code = self.config.get("General", "lang", fallback="en_US")
        lang_file = os.path.join(BASE_DIR, "lang", f"{lang_code}.json")
        with open(lang_file, "r", encoding="utf-8") as f:
            self.lang = json.load(f)

        self.label.setText(self.lang["downloading vosk"])
        self.label.setAccessibleDescription(self.lang["downloading vosk"])
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self.scroll_area.height() // 15
        font = QFont("Arial", size)
        if not font.exactMatch():
            font = QFont("Sans Serif", size)
        self.label.setFont(font)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        global config_path
        self.setWindowTitle("Athena")
        self.resize(800, 600)

        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.lang = {}

        # Layout principal
        self.layout = QVBoxLayout(self)

        # Page 1 : Language selection
        self.language_selection = SelectLanguage()
        self.language_selection.language_selected.connect(self.show_option_selection)

        # Page 2 : Modules selection
        self.modules_selection = SelectModules()
        self.modules_selection.modules_validated.connect(self.next)
        self.modules_selection.back_clicked.connect(self.show_language_selection)

        # Page 3 : Vosk installation
        self.vosk_installation = InstallVosk()

        self.pages = [self.language_selection, self.modules_selection, self.vosk_installation]
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
        """)

    def show_page(self, page: QWidget):
        for p in self.pages:
            p.setVisible(p is page)

    def show_language_selection(self):
        self.show_page(self.language_selection)

    def show_option_selection(self, language):
        print(language)
        self.modules_selection.load_language()
        self.show_page(self.modules_selection)
    
    def load_language(self):
        global BASE_DIR, config_path
        self.config.read(config_path)
        lang_code = self.config.get("General", "lang", fallback="en_US")
        lang_file = os.path.join(BASE_DIR, "lang", f"{lang_code}.json")
        with open(lang_file, "r", encoding="utf-8") as f:
            self.lang = json.load(f)

    def next(self, selected_modules):
        global system
        print(selected_modules)
        self.load_language()
        if self.lang["voice module"] in selected_modules:
            if self.config.get("General", "lang", fallback="en_US") == "en_US":
                url = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"

            elif self.config.get("General", "lang", fallback="en_US") == "fr_FR":
                url = "https://alphacephei.com/vosk/models/vosk-model-fr-0.22.zip"
            
            else:
                return
            self.download_vosk_model(url)
            
        print("done")
        self.config.set("General", "wizard", "true")
        with open(config_path, "w") as configfile:
            self.config.write(configfile)
        if system == "Windows":
            subprocess.Popen([sys.executable] + sys.argv, close_fds=True, creationflags=subprocess.DETACHED_PROCESS)
        else:
            subprocess.Popen([sys.executable] + sys.argv, close_fds=True)
        sys.exit()

    
    def download_vosk_model(self, url):

        local_zip = url.split("/")[-1]
        filename = local_zip[:-4]
        extract_folder = os.path.join(BASE_DIR, "vosk")

        if os.path.exists(os.path.join(extract_folder, filename)):
            self.config.set("Voice", "vosk", os.path.join(extract_folder, filename))
            with open(config_path, "w") as configfile:
                self.config.write(configfile)
            return

        self.vosk_installation.load_language()
        self.show_page(self.vosk_installation)

        # Progress bar creation
        progress = QProgressBar(self)
        progress.setRange(0, 100)
        self.layout.addWidget(progress)
        progress.show()

        # Download
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(local_zip, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = int(downloaded * 100 / total_size)
                        progress.setValue(percent)
                        QApplication.processEvents()  # update progress bar

        # Unzip
        with zipfile.ZipFile(local_zip, "r") as zip_ref:
            zip_ref.extractall(extract_folder)

        self.config.set("Voice", "vosk", os.path.join(extract_folder, filename))
        with open(config_path, "w") as configfile:
            self.config.write(configfile)
        os.remove(local_zip)
        progress.setValue(100)
        QMessageBox.information(self, "Vosk", self.lang["downloaded vosk"])
        progress.deleteLater()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
