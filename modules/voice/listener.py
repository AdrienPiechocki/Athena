import os
import sys
import json
import time
import queue
import configparser
import sounddevice as sd
from vosk import Model, KaldiRecognizer, SetLogLevel
from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox
from PySide6.QtGui import QFont
from .brain import Brain
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
log_dir = resource_path("logs")

class ListenerThread(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(bool)

    def __init__(self, lang):
        super().__init__()
        self.lang = lang

    def run(self):
        try:
            SetLogLevel(-1)
            config = configparser.ConfigParser()
            config.read(config_path)
            model_path = config.get("Voice", "vosk", fallback=False)

            if not model_path or not os.path.exists(model_path):
                self.log_signal.emit(f"❌ {self.lang['no vosk']}")
                self.finished_signal.emit(False)
                return

            self.brain = Brain(log_signal=self.log_signal)
            self.hotword = self.brain.hotword
            self.speaker = self.brain.speaker
            self.q = queue.Queue()

            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, 48000)

            if not self.brain.cancel:
                self.log_signal.emit(self.lang["say Athena"])
                self.stream = sd.RawInputStream(
                    samplerate=48000,
                    blocksize=8000,
                    dtype="int16",
                    channels=1,
                    callback=self.audio_callback
                )
                self.stream.start()

                self.recognize_loop()

        except Exception as e:
            self.log_signal.emit(f"❌ {str(e)}")
            self.finished_signal.emit(False)

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            self.log_signal.emit(f"⚠️ {status}")
        if not self.brain.cancel:
            self.q.put(bytes(indata))

    def recognize_loop(self):
        while not self.brain.cancel:
            try:
                data = self.q.get(timeout=0.1)
            except queue.Empty:
                continue

            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "").strip().lower()
                if text:
                    if self.hotword and self.hotword in text:
                        self.log_signal.emit(f"🗣️ {text}")
                        self.speaker.stop()
                        self.brain.agent_loop(text)

        self.end()

    def end(self):
        self.speaker.stop()
        if hasattr(self, "stream") and self.stream:
            self.stream.stop()
            self.stream.close()
        self.finished_signal.emit(True)


class ListenerUI(QWidget):

    def __init__(self):
        super().__init__()

        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.lang = {}
        self.load_language()

        layout = QVBoxLayout()
        self.resize(600, 800)


        self.label = QLabel(f"<h2>{self.lang['listener title']}</h2>")
        self.label.setAccessibleDescription(self.lang["listener title"])
        self.label.setFocusPolicy(Qt.StrongFocus)
        layout.addWidget(self.label)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setAccessibleName(self.lang["text logs"])
        self.log.setFocusPolicy(Qt.StrongFocus)
        layout.addWidget(self.log)

        self.start_button = QPushButton(self.lang["start listening"])
        self.start_button.setAccessibleDescription(self.lang["start listening"])
        self.start_button.clicked.connect(self.start_listening)
        self.start_button.setFocusPolicy(Qt.StrongFocus)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton(self.lang["stop listening"])
        self.stop_button.setAccessibleDescription(self.lang["stop listening"])
        self.stop_button.clicked.connect(self.stop_listening)
        self.stop_button.setFocusPolicy(Qt.StrongFocus)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)

        self.listener_thread = None

        # Style
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
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
            QTextEdit {
                background-color: #111111;
                color: #00FF00;
                border: 2px solid #FFFFFF;
            }
            QTextEdit:focus {
                border: 4px solid #FFA500;
            }
        """)

    def load_language(self):
        lang_code = self.config.get("General", "lang", fallback="en_US")
        lang_file = os.path.join(lang_dir, f"{lang_code}.json")
        with open(lang_file, "r", encoding="utf-8") as f:
            self.lang = json.load(f)

    def append_log(self, message):
        self.log.append(message)
        self.log.ensureCursorVisible()

    def start_listening(self):
        self.start_button.setEnabled(False)
        self.log.clear()
        self.append_log(self.lang["starting"])

        self.listener_thread = ListenerThread(self.lang)
        self.listener_thread.log_signal.connect(self.append_log)
        self.listener_thread.finished_signal.connect(self.on_listening_finished)
        self.listener_thread.start()

    def stop_listening(self):
        if self.listener_thread and self.listener_thread.isRunning():
            self.listener_thread.brain.cancel = True
            self.listener_thread.speaker.stop()
            self.append_log(self.lang["stop Athena"])
            self.listener_thread.wait()
            self.start_button.setEnabled(True)

    def closeEvent(self, event):
        self.stop_listening()

    def on_listening_finished(self, success):
        self.start_button.setEnabled(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self.height() // 15
        font = QFont("Arial", size)
        if not font.exactMatch():
            font = QFont("Sans Serif", size)
        self.label.setFont(font)
        self.log.setFont(font)
        self.start_button.setFont(font)
        self.stop_button.setFont(font)
