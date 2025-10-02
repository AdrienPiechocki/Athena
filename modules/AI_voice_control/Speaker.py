import subprocess
import configparser
import json

class Speaker:
    config = configparser.ConfigParser()
    config.read("settings/config.cfg")

    with open(f"./lang/{config.get("General", "lang", fallback=False)}.json", 'r', encoding='utf-8') as f:
        lang = json.load(f)

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

        cmd = [
            "espeak-ng",
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
