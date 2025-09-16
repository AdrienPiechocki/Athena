import subprocess

class Speaker:
    def __init__(self, voice="fr", speed=130, pitch=50, volume=100, gap=0):
        self.voice = voice
        self.speed = str(speed)
        self.pitch = str(pitch)
        self.volume = str(volume)
        self.gap = str(gap)
        self.process = None  # pour stocker le process en cours

    def say(self, text):
        # Si un processus est déjà en cours, on le stoppe avant d’en lancer un nouveau
        self.stop()

        cmd = [
            "espeak-ng",
            "-v", self.voice,
            "-s", self.speed,
            "-p", self.pitch,
            "-a", self.volume,
            "-g", self.gap,
            text
        ]
        # Popen au lieu de run (non bloquant)
        self.process = subprocess.Popen(cmd)

    def stop(self):
        if self.process and self.process.poll() is None:
            # process encore actif
            self.process.terminate()
            try:
                self.process.wait(timeout=1)  # attendre l’arrêt
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
