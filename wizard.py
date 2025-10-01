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
        self.update_font_size()

    def resizeEvent(self, event):
        """Réajuste la taille de la police à chaque redimensionnement"""
        self.update_font_size()
        super().resizeEvent(event)

    def update_font_size(self):
        """Adapte la taille du texte pour qu'il remplisse tout l'espace disponible"""
        min_label_font = 24
        min_button_font = 18

        label_width = self.label.width()
        label_height = self.label.height()

        text = self.label.text()
        if not text:
            return

        # Commencer avec une grosse taille et réduire si nécessaire
        font_size = max(label_height, label_width)  # taille initiale approximative
        font = QFont("Arial", font_size)
        self.label.setFont(font)
        self.button.setFont(QFont("Arial", max(min_button_font, int(font_size * 0.6))))

        # Ajuster la taille pour que le texte tienne dans largeur et hauteur
        metrics = self.label.fontMetrics()
        lines = text.split('\n')
        total_text_height = metrics.lineSpacing() * len(lines)

        while (total_text_height > label_height or any(metrics.horizontalAdvance(line) > label_width for line in lines)) and font_size > min_label_font:
            font_size -= 1
            font.setPointSize(font_size)
            self.label.setFont(font)
            self.button.setFont(QFont("Arial", max(min_button_font, int(font_size * 0.6))))
            metrics = self.label.fontMetrics()
            total_text_height = metrics.lineSpacing() * len(lines)
        
    def announce(self, text: str):
        self.label.setText(text)
        self.label.setAccessibleDescription(text)

        # Déplacer le focus pour Orca
        self.label.setFocus()

    def on_button_clicked(self):
        self.announce("Bouton cliqué !")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
