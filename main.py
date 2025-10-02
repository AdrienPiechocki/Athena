from modules.AI_voice_control import listener
from wizard import *
import configparser

config = configparser.ConfigParser()
config.read("settings/config.cfg")

if config.get("General", "wizard", fallback=False) == "true":
    listener.main()
else:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
