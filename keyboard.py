from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QVBoxLayout
from PySide6.QtCore import Qt
from pynput.keyboard import Controller, Key
import sys

keyboard_controller = Controller()

class VirtualKeyboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clavier Virtuel AZERTY")
        self.setGeometry(100, 100, 950, 400)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.shift_on = False
        self.caps_on = False

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Clavier AZERTY complet
        self.keys_rows = [
            ['&','é','"','\'','(','-','è','_','ç','à',')','=','Backspace'],
            ['A','Z','E','R','T','Y','U','I','O','P','^','$','Enter'],
            ['Q','S','D','F','G','H','J','K','L','M','ù','*'],
            ['Shift','W','X','C','V','B','N',',',';','!',':','Caps'],
            ['Space']
        ]

        # Symboles alternatifs pour Shift
        self.symbols_shift = {
            '&':'1','é':'2','"':'3','\'':'4','(':'5','-':'6','è':'7','_':'8','ç':'9','à':'0',
            ')':'°','=':'+','^':'¨','$':'£','*':'µ',
            ',':'?',';':'.','!':'§',':':'/'
        }

        self.grid_layout = QGridLayout()
        self.create_buttons()
        layout.addLayout(self.grid_layout)
        self.setLayout(layout)

        self.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                border-radius: 5px;
                background-color: #f0f0f0;
                padding: 10px;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)

    def create_buttons(self):
        self.buttons = {}
        for row_index, row_keys in enumerate(self.keys_rows):
            col_index = 0
            for key in row_keys:
                btn = QPushButton(key)
                width = 50
                span = 1

                if key == "Space":
                    width = 400
                    span = 8
                    btn.clicked.connect(lambda _, k=' ': self.press_key(k))
                elif key == "Backspace":
                    width = 100
                    btn.clicked.connect(lambda: self.press_special(Key.backspace))
                elif key == "Enter":
                    width = 100
                    btn.clicked.connect(lambda: self.press_special(Key.enter))
                elif key == "Shift":
                    width = 80
                    btn.clicked.connect(self.toggle_shift)
                elif key == "Caps":
                    width = 80
                    btn.clicked.connect(self.toggle_caps)
                else:
                    btn.clicked.connect(lambda _, k=key: self.press_key(k))

                btn.setFixedWidth(width)
                btn.setFixedHeight(50)
                self.grid_layout.addWidget(btn, row_index, col_index, 1, span)
                col_index += span
                self.buttons[key] = btn

    def press_key(self, key):
        # Déterminer la bonne touche selon Shift/Caps
        if self.shift_on:
            char = self.symbols_shift.get(key, key.upper())
        else:
            if self.caps_on and key.isalpha():
                char = key.upper()
            else:
                char = key.lower()

        keyboard_controller.press(char)
        keyboard_controller.release(char)

        # Si Shift activé, désactiver après frappe
        if self.shift_on and key not in ['Shift','Caps']:
            self.shift_on = False
            self.update_shift_button()

    def press_special(self, key):
        keyboard_controller.press(key)
        keyboard_controller.release(key)

    def toggle_shift(self):
        self.shift_on = not self.shift_on
        self.update_shift_button()

    def toggle_caps(self):
        self.caps_on = not self.caps_on
        self.update_caps_button()

    def update_shift_button(self):
        color = "#a0a0ff" if self.shift_on else "#f0f0f0"
        self.buttons['Shift'].setStyleSheet(f"background-color: {color}; font-size:16px; border-radius:5px;")

    def update_caps_button(self):
        color = "#ffa0a0" if self.caps_on else "#f0f0f0"
        self.buttons['Caps'].setStyleSheet(f"background-color: {color}; font-size:16px; border-radius:5px;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    keyboard = VirtualKeyboard()
    keyboard.show()
    sys.exit(app.exec())
