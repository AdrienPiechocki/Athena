import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Athéna")
        self.resize(800, 500)

        # Layout principal
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        # Label
        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFocusPolicy(Qt.StrongFocus)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.label)

        # Stretch pour pousser le bouton en bas
        self.layout.addStretch()

        # Bouton
        self.button = QPushButton("Commencer")
        self.button.setFocusPolicy(Qt.StrongFocus)
        self.layout.addWidget(self.button)

        self.setLayout(self.layout)

        # Styles accessibles
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
                border: 3px solid #FFFF00;
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

        # Action du bouton
        self.button.clicked.connect(self.on_button_clicked)

        # Annonce initiale
        self.announce("Bienvenue dans l'installation d'Athéna, votre assistant accessible sous Linux.")

        # Ajustement initial de la taille du texte

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Ajuste la taille du texte selon la largeur du label
        size = self.label.height() // 5
        font = QFont("Arial", size)
        self.label.setFont(font)
        self.button.setFont(font)

    def announce(self, text: str):
        self.label.setText(text)
        self.label.setAccessibleDescription(text)

    def on_button_clicked(self):
        self.announce("Bouton cliqué !")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
