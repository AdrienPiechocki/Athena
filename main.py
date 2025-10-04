
import configparser
import os
import sys 
import __main__
from PySide6.QtWidgets import QApplication

def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(getattr(__main__, '__file__', sys.argv[0])))
    return os.path.join(base_path, relative_path)


config_path = resource_path("settings/config.cfg")
config = configparser.ConfigParser()
config.read(config_path)

if config.get("General", "wizard", fallback=False) == "true":
    if config.get("Modules", "voice", fallback=False) == "true":
        from modules.voice.listener import *
        app = QApplication(sys.argv)
        window = ListenerUI()
        window.show()
        sys.exit(app.exec())

else:
    from wizard import *
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
