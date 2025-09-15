import subprocess

class Speaker:
    def __init__(self, voice="fr", speed=130, pitch=50, volume=100, gap=0):
        self.voice = voice
        self.speed = str(speed)    # Vitesse (mots/min)
        self.pitch = str(pitch)    # Hauteur de voix
        self.volume = str(volume)  # Volume (0–200)
        self.gap = str(gap)        # Pause entre les mots

    def say(self, text):
        cmd = [
            "espeak-ng",
            "-v", self.voice,
            "-s", self.speed,
            "-p", self.pitch,
            "-a", self.volume,
            "-g", self.gap,
            text
        ]
        subprocess.run(cmd)
