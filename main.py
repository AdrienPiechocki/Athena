import sounddevice as sd
import queue
import json
import threading
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
thread = None

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
                if not called and hotword in text and len(text.split()) <= 3:
                    answer = f"Oui {name}?"
                    print(f"🟢 {answer}")
                    speaker.say(answer)
                    called = True
                elif called:
                    print(f"🗣️ {text}")
                    brain.analyze_question(text)

def run_session():
    global stream, thread, called
    recognizer = KaldiRecognizer(model, vosk_rate)
    called = False
    brain.cancel = False

    print("🎙️ Dites Athéna (Ctrl+C pour arrêter)...")

    stream = sd.RawInputStream(samplerate=vosk_rate, blocksize=16000, dtype='int16',
                               channels=1, callback=audio_callback)
    stream.start()

    thread = threading.Thread(target=recognize_loop, args=(recognizer, q))
    thread.start()

    while not brain.cancel:
        time.sleep(0.1)

    stream.stop()
    stream.close()
    thread.join()

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
        if thread and thread.is_alive():
            brain.cancel = True
            thread.join()
        sys.exit(0)

if __name__ == "__main__":
    main()
