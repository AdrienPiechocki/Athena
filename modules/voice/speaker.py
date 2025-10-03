import subprocess
import configparser
import json
import os
import sys
import platform

class Speaker():
    BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
    config_path = os.path.join(BASE_DIR, "settings", "config.cfg")

    config = configparser.ConfigParser()
    config.read(config_path)

    lang_dir = os.path.join(BASE_DIR, "lang")
    lang_file = os.path.join(lang_dir, f"{config.get('General', 'lang', fallback='en_US')}.json")
    with open(lang_file, 'r', encoding='utf-8') as f:
        lang = json.load(f)
    
    system = platform.system()

    def __init__(self, voice=lang["lang"], speed=130, pitch=50, volume=100, gap=0):
        self.voice = voice
        self.speed = str(speed)
        self.pitch = str(pitch)
        self.volume = str(volume)
        self.gap = str(gap)
        self.process = None  # to stock ongoing process

    def say(self, text):
        # If a process in ongoing, wait for it to finish
        if self.process and self.process.poll() is None:
            self.process.wait()
        if self.system == "Linux":
            cmd = [
                "espeak-ng",
                "-v", self.voice,
                "-s", self.speed,
                "-p", self.pitch,
                "-a", self.volume,
                "-g", self.gap,
                text
            ]
        else:
            cmd = [
                "c:\Program Files\eSpeak NG\espeak-ng.exe",
                "-v", self.voice,
                "-s", self.speed,
                "-p", self.pitch,
                "-a", self.volume,
                "-g", self.gap,
                text
            ]

        self.process = subprocess.Popen(cmd)

    def stop(self):
        if self.process and self.process.poll() is None:
            # process still active
            self.process.terminate()
            try:
                self.process.wait(timeout=1) 
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
