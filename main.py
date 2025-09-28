import sounddevice as sd
import queue
import json
import time
import sys
from Brain import Brain
from vosk import Model, KaldiRecognizer, SetLogLevel
SetLogLevel(-1)

print("Démarrage...")

model = Model("vosk-model-fr-0.22")
vosk_rate = 48000
q = queue.Queue()
called = False

brain = Brain()

name = brain.name
hotword = brain.hotword
speaker = brain.speaker

stream = None

def audio_callback(indata, frames, time_info, status):
    if status:
        print(f"⚠️ {status}")
    if not brain.cancel:
        q.put(bytes(indata))

def recognize_loop(recognizer, q):
    global called
    while not brain.cancel:
        try:
            data = q.get(timeout=0.1)
        except queue.Empty:
            continue
        result_ok = recognizer.AcceptWaveform(data)
        if result_ok:
            result = json.loads(recognizer.Result())
            text = result.get("text", "").strip().lower()
            if text:
                if not called and hotword in text:
                    speaker.stop()
                    print(f"🗣️ {text}")
                    brain.agent_loop(text)
                    called = True
                elif called:
                    speaker.stop()
                    print(f"🗣️ {text}")
                    brain.agent_loop(text)

def run_session():
    global stream, called
    recognizer = KaldiRecognizer(model, vosk_rate)
    called = False
    brain.cancel = False

    print("🎙️ Dites Athéna (Ctrl+C pour arrêter)...")

    stream = sd.RawInputStream(samplerate=vosk_rate, blocksize=8000, dtype='int16',
                               channels=1, callback=audio_callback)
    stream.start()

    recognize_loop(recognizer, q)

    while not brain.cancel:
        time.sleep(0.1)

    stream.stop()
    stream.close()

def main():
    try:
        while True:
            run_session()
            print("🔁 Redémarrage de l'écoute...")
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l’utilisateur (Ctrl+C).")
        if stream:
            stream.stop()
            stream.close()
        sys.exit(0)

if __name__ == "__main__":
    main()
