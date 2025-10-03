
import configparser

config = configparser.ConfigParser()
config.read("settings/config.cfg")

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
