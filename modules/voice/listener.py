import sounddevice as sd
import queue
import json
import time
import sys
from .brain import Brain
from vosk import Model, KaldiRecognizer, SetLogLevel
import configparser
import os

class Listener():
    BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
    config_path = os.path.join(BASE_DIR, "settings", "config.cfg")
    SetLogLevel(-1)

    config = configparser.ConfigParser()
    config.read(config_path)

    lang_dir = os.path.join(BASE_DIR, "lang")
    lang_file = os.path.join(lang_dir, f"{config.get('General', 'lang', fallback='en_US')}.json")
    with open(lang_file, 'r', encoding='utf-8') as f:
        lang = json.load(f)

    def __init__(self):
        
        print(f"{self.lang['starting']}...")

        self.model = Model(self.config.get("Voice", "vosk", fallback=False))
        self.vosk_rate = 48000
        self.q = queue.Queue()

        self.brain = Brain()

        self.name = self.brain.name
        self.hotword = self.brain.hotword
        self.speaker = self.brain.speaker

        self.stream = None
        self.main()
        
    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"⚠️ {status}")
        if not self.brain.cancel:
            self.q.put(bytes(indata))

    def recognize_loop(self, recognizer, q):
        while not self.brain.cancel:
            try:
                data = q.get(timeout=0.1)
            except queue.Empty:
                continue
            result_ok = recognizer.AcceptWaveform(data)
            if result_ok:
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip().lower()
                if text:
                    if self.hotword in text:
                        self.speaker.stop()
                        print(f"🗣️ {text}")
                        self.brain.agent_loop(text)

    def run_session(self):
        self.recognizer = KaldiRecognizer(self.model, self.vosk_rate)
        self.brain.cancel = False

        print(self.lang["say Athena"])

        self.stream = sd.RawInputStream(samplerate=self.vosk_rate, blocksize=8000, dtype='int16',
                                channels=1, callback=self.audio_callback)
        self.stream.start()

        self.recognize_loop(self.recognizer, self.q)

        if self.brain.cancel:
            self.end()
        else:
            time.sleep(0.1)

    def end(self):
        print(self.lang["stop Athena"])
        if self.stream:
            self.stream.stop()
            self.stream.close()
        sys.exit(0)

    def main(self):
        try:
            while True:
                if self.hotword:
                    self.run_session()
                else:
                    print(self.lang["no AI"])
                    sys.exit(0)
        except KeyboardInterrupt:
            self.end()
