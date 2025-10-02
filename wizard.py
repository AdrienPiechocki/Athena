from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QSizePolicy, QScrollArea, QGridLayout, QStackedWidget, QCheckBox
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QIcon
import sys
import configparser


class SelectLanguage(QWidget):

    language_selected = Signal(str)

    config = configparser.ConfigParser()
    config.read("settings/config.cfg")

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
        self.label = QLabel("")
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

        # Initial buttons creation
        self.create_buttons(columns=3)

        # Initial message
        self.announce("Welcome to Athena's installation process. Please select a Language.")

    def create_buttons(self, columns: int):
        for btn in self.buttons:
            self.button_grid.removeWidget(btn)
            btn.deleteLater()
        self.buttons.clear()

        for index, lang in enumerate(self.languages.keys()):
            button = QPushButton(lang)
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
        self.label.setFont(font)
        for btn in self.buttons:
            btn.setFont(font)

    def announce(self, text: str):
        self.label.setText(text)
        self.label.setAccessibleDescription(text)

    def on_button_clicked(self, language: str):
        self.announce(f"{language}")
        self.config.set("General", "lang", self.languages[language]["lang"])
        with open("settings/config.cfg", "w") as configfile:
            self.config.write(configfile)
        self.language_selected.emit(language)

class SelectOptions(QWidget):
    
    options_validated = Signal(list)

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
        self.label = QLabel("How do you want to access Athena?")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFocusPolicy(Qt.StrongFocus)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_layout.addWidget(self.label)

        # Checkboxes
        self.checkboxes = []
        options = ["Keyboard", "Mouse", "Voice", "Push button"]

        for opt in options:
            checkbox = QCheckBox(opt)
            checkbox.setFocusPolicy(Qt.StrongFocus)
            self.scroll_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

        # Button "Next"
        self.next_button = QPushButton("Next")
        self.next_button.setFocusPolicy(Qt.StrongFocus)
        self.next_button.clicked.connect(self.on_next_clicked)
        self.scroll_layout.addWidget(self.next_button)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self.scroll_area.height() // 15
        font = QFont("Arial", size)
        self.label.setFont(font)
        for cb in self.checkboxes:
            cb.setFont(font)
        self.next_button.setFont(font)
        
    def get_selected_options(self):
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]


    def on_next_clicked(self):
        selected = self.get_selected_options()
        self.options_validated.emit(selected)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Athena")
        self.resize(800, 600)

        self.stacked = QStackedWidget(self)

        # Page 1 : Language selection
        self.language_selection = SelectLanguage()
        self.language_selection.language_selected.connect(self.show_option_selection)

        # Page 2 : Options selection
        self.options_selection = SelectOptions()
        self.options_selection.options_validated.connect(self.next)

        # Add to stacked
        self.stacked.addWidget(self.language_selection)  # index 0
        self.stacked.addWidget(self.options_selection)   # index 1

        layout = QVBoxLayout(self)
        layout.addWidget(self.stacked)

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
                width: 24px;
                height: 24px;
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

    def show_option_selection(self, language):
        print(language)
        self.stacked.setCurrentWidget(self.options_selection)
    
    def next(self, selected_options):
        print(selected_options)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
