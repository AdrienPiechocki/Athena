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
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QProgressBar
)
from PySide6.QtCore import QThread, Signal

# --- Config et langue ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

config_path = resource_path("settings/config.cfg")
config = configparser.ConfigParser()
config.read(config_path)
lang_dir = resource_path("lang")
lang_file = os.path.join(lang_dir, f"{config.get('General', 'lang', fallback='en_US')}.json")
with open(lang_file, 'r', encoding='utf-8') as f:
    lang = json.load(f)

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

# --- Worker pour installation ---
class InstallerThread(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)

    def __init__(self, parent=None, vosk_url=None):
        super().__init__(parent)
        self.system = platform.system().lower()
        self.vosk_url = vosk_url
        
    def run_command(self, cmd, silent=False):
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
        self.log_signal.emit(f"➡️ {lang['executing']} : {cmd_str}")
        try:
            # Remplace sudo par pkexec pour la GUI
            if "sudo" in cmd:
                cmd[0] = "pkexec"
            if silent:
                subprocess.check_call(cmd, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.check_call(cmd, shell=False)
        except subprocess.CalledProcessError:
            self.log_signal.emit(f"❌ {lang['exec error']} : {cmd_str}")

    def progress_step(self, description, duration=2):
        steps = duration * 20
        for i in range(steps):
            self.progress_signal.emit(int((i+1)/steps*100))
            time.sleep(0.05)
        self.progress_signal.emit(0)

    def install_vosk_model(self):
        if not self.vosk_url:
            self.log_signal.emit("⚠️ Aucun URL Vosk fourni, étape ignorée")
            return

        local_zip = self.vosk_url.split("/")[-1]
        filename = local_zip[:-4]
        extract_folder = os.path.join(BASE_DIR, "vosk")
        model_path = os.path.join(extract_folder, filename)

        if os.path.exists(model_path):
            config.set("Voice", "vosk", model_path)
            with open(config_path, "w") as configfile:
                config.write(configfile)
            self.log_signal.emit(f"✅ Modèle Vosk déjà présent : {model_path}")
            return

        os.makedirs(extract_folder, exist_ok=True)
        self.log_signal.emit(f"⬇️ Téléchargement du modèle Vosk depuis {self.vosk_url}")

        # Téléchargement
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

        # Extraction
        self.log_signal.emit(f"📦 Extraction du modèle Vosk...")
        with zipfile.ZipFile(local_zip, "r") as zip_ref:
            zip_ref.extractall(extract_folder)

        # Enregistrement du chemin dans config
        self.config.set("Voice", "vosk", model_path)
        with open(config_path, "w") as configfile:
            self.config.write(configfile)

        os.remove(local_zip)
        self.log_signal.emit(f"✅ Modèle Vosk installé : {model_path}")
        self.progress_signal.emit(100)


    def install_requirements_venv(self):
        venv_dir = os.path.join(BASE_DIR, ".venv")
        venv_python = os.path.join(venv_dir, "bin", "python") if os.name != "nt" else os.path.join(venv_dir, "Scripts", "python.exe")
        venv_pip = [venv_python, "-m", "pip"]

        if not os.path.exists(venv_dir):
            self.log_signal.emit(f"🧩 {lang['venv creation']}")
            self.run_command([sys.executable, "-m", "venv", venv_dir])
        else:
            self.log_signal.emit(f"🔄 {lang['venv update']}")

        self.run_command(venv_pip + ["install", "--upgrade", "pip"])

        requirements = os.path.join(BASE_DIR, "requirements.txt")
        if os.path.exists(requirements):
            self.progress_step(lang["python install"], 2)
            self.run_command(venv_pip + ["install", "--upgrade", "-r", requirements])
        else:
            self.log_signal.emit(f"⚠️ {lang['no requirements found']}")

    def install_ollama_model(self):
        if shutil.which("ollama"):
            self.progress_step(lang["qwen3 install"], 3)
            self.run_command(["ollama", "pull", "qwen3"])
        else:
            self.log_signal.emit(f"⚠️ {lang['ollama not found']}")

    def install_linux(self):
        self.log_signal.emit(f"🐧 {lang['linux install']}")
        if shutil.which("apt"):
            pkg_manager = "apt"
        elif shutil.which("pacman"):
            pkg_manager = "pacman"
        elif shutil.which("dnf"):
            pkg_manager = "dnf"
        else:
            self.log_signal.emit(f"❌ {lang['no package manager']}")
            return

        self.progress_step(lang["package update"], 2)
        if pkg_manager == "apt":
            self.run_command(["sudo", "apt", "update"])
        elif pkg_manager == "pacman":
            self.run_command(["sudo", "pacman", "-Sy"])
        elif pkg_manager == "dnf":
            self.run_command(["sudo", "dnf", "makecache"])

        self.progress_step(lang["packages installation"], 3)
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
        self.log_signal.emit(f"🪟 {lang['windows install']}")
        if not shutil.which("espeak-ng"):
            self.progress_step(lang["espeak install"], 2)
            self.run_command(["winget", "install", "-e", "--id", "espeak-ng.espeak-ng"])
        if not shutil.which("ollama"):
            self.progress_step(lang["ollama install"], 2)
            self.run_command(["winget", "install", "-e", "--id", "Ollama.Ollama"])
        self.install_ollama_model()

    def run(self):
        try:
            if "linux" in self.system:
                self.install_linux()
            elif "windows" in self.system:
                self.install_windows()
            else:
                self.log_signal.emit(f"❌ {lang['wrong system']} : {self.system}")
                return

            self.install_requirements_venv()
            if config.get("General", "lang", fallback="en_US") == "en_US":
                self.vosk_url = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"

            elif config.get("General", "lang", fallback="en_US") == "fr_FR":
                self.vosk_url = "https://alphacephei.com/vosk/models/vosk-model-fr-0.22.zip"
            self.install_vosk_model()
            self.progress_step(lang["finish install"], 2)
            self.log_signal.emit(f"✅ {lang['install success']}")
        except KeyboardInterrupt:
            self.log_signal.emit(f"{lang['install interupted']}")

# --- UI principale ---
class InstallerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(lang['auto-install title'])
        self.setGeometry(100, 100, 700, 500)

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

        layout = QVBoxLayout()

        self.label = QLabel(f"<h2>{lang['auto-install title']}</h2>")
        layout.addWidget(self.label)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.start_button = QPushButton(lang["start install"])
        self.start_button.clicked.connect(self.start_installation)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def start_installation(self):
        self.thread = InstallerThread()
        self.thread.log_signal.connect(self.append_log)
        self.thread.progress_signal.connect(self.progress.setValue)
        self.thread.start()
        self.start_button.setEnabled(False)

    def append_log(self, text):
        self.log.append(text)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

# --- Lancement ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InstallerUI()
    window.show()
    sys.exit(app.exec())
