
import configparser
import os
import sys 

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

config_path = resource_path("settings/config.cfg")
config = configparser.ConfigParser()
config.read(config_path)

if config.get("General", "wizard", fallback=False) == "true":
    if config.get("Modules", "voice", fallback=False) == "true":
        from modules.voice.listener import Listener
        Listener()
else:
    from wizard import *
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
