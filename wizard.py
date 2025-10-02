import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QSizePolicy, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
import math


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Athéna")
        self.resize(800, 500)

        # Layout principal
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        # ScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFocusPolicy(Qt.NoFocus)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.layout.addWidget(self.scroll_area)

        # Widget interne qui contient tout (label + boutons)
        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)

        # Layout vertical interne
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(20)

        # Label
        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFocusPolicy(Qt.StrongFocus)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_layout.addWidget(self.label)

        # Grille des boutons
        self.grid_widget = QWidget()
        self.button_grid = QGridLayout()
        self.button_grid.setSpacing(10)
        self.grid_widget.setLayout(self.button_grid)
        self.scroll_layout.addWidget(self.grid_widget)

        # Définir les langues
        self.languages = {
            "Français": {
                "icon": "./data/flags/fr.svg",
                "lang": "fr_FR"
            },
            "English": {
                "icon": "./data/flags/us.svg",
                "lang": "en_UK"   
            }
        }
        self.min_button_width = 150
        self.buttons = []

        # Création initiale des boutons
        self.create_buttons(columns=3)

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
        """)

        # Message initial
        self.announce("Welcome to Athena's installation process. Please select a Language.")

    def create_buttons(self, columns: int):
        for btn in self.buttons:
            self.button_grid.removeWidget(btn)
            btn.deleteLater()
        self.buttons.clear()

        for index, lang in enumerate(self.languages.keys()):
            button = QPushButton(lang)
            button.setFocusPolicy(Qt.StrongFocus)

            # Ajouter l'icône du drapeau si disponible
            if "icon" in self.languages[lang]:
                button.setIcon(QIcon(self.languages[lang]["icon"]))
                button.setIconSize(QSize(64, 64))  # taille du drapeau

            button.clicked.connect(lambda checked, l=lang: self.on_button_clicked(l))
            self.button_grid.addWidget(button, index // columns, index % columns)
            self.buttons.append(button)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self.scroll_area.height() // 15
        font = QFont("Arial", size)
        self.label.setFont(font)
        for btn in self.buttons:
            btn.setFont(font)

    def announce(self, text: str):
        self.label.setText(text)
        self.label.setAccessibleDescription(text)

    def on_button_clicked(self, language: str):
        self.announce(f"{language}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
