
import configparser
import os
import sys 

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
config_path = os.path.join(BASE_DIR, "settings", "config.cfg")

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
