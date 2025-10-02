
import configparser

config = configparser.ConfigParser()
config.read("settings/config.cfg")

if config.get("General", "wizard", fallback=False) == "true":
    from modules.AI_voice_control import listener
    listener.main()
else:
    from wizard import *
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
