import requests
import json
import subprocess
import os
import re
from Speaker import Speaker
from datetime import datetime
import locale

class Brain():
    name = os.getlogin()
    hotword = "athéna"
    cancel = False
    speaker = Speaker()
    OLLAMA_API = "http://localhost:11434/api/generate"
    MODEL = "qwen3"

    # ---------------------- CONFIGURATION ----------------------

    ALLOWED_ACTIONS = ["run", "close", "list_apps", "time", "day", "terminate"]

    SYSTEM_PROMPT = """Tu es un assistant IA par commande vocale répondant au nom d'Athéna.
    - Si l'utilisateur te demande d'ouvrir ou de lancer une application (classique ou flatpak), réponds UNIQUEMENT avec :
    ACTION: run <nom_application_ou_alias>
    - Si l'utilisateur te demande de fermer une application (classique ou flatpak), réponds UNIQUEMENT avec :
    ACTION: close <nom_application_ou_alias>
    - Si l'utilisateur te demanque l'heure qu'il est, réponds UNIQUEMENT avec :
    ACTION: time
    - Si l'utilisateur te demanque la date du jour, réponds UNIQUEMENT avec :
    ACTION: day
    - Si l'utilisateur te demanque de t'arrêter, réponds UNIQUEMENT avec :
    ACTION: terminate
    Si l'utilisateur demande plusieurs actions à la fois, réponds UNIQUEMENT avec :
    <action_1> <action_2>
    Sinon, réponds normalement et simplement (une phrase ou deux max).
    N'utilise pas d'emojis.
    """

    def __init__(self, apps="apps.json"):
        locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
        with open(apps, 'r', encoding='utf-8') as f:
            self.apps = json.load(f)
        self.ALLOWED_APPS = self.apps["ALLOWED_APPS"]
        self.ALLOWED_FLATPAKS = self.apps["ALLOWED_FLATPAKS"]
        self.ALIASES = self.apps["ALIASES"]

    # ---------------------- FONCTIONS ----------------------

    def query_ollama(self, prompt):
        try:
            response = requests.post(
                self.OLLAMA_API,
                json={
                    "model": self.MODEL,
                    "prompt": self.SYSTEM_PROMPT + "\n\n" + prompt,
                    "think": False
                },
                stream=True  # <-- important
            )

            if response.status_code != 200:
                print("Erreur API Ollama :", response.status_code, response.text)
                return "Erreur lors de la génération de la réponse."

            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if "response" in data:
                            full_response += data["response"]
                    except json.JSONDecodeError:
                        continue  # ignore les morceaux non JSON valides

            return full_response.strip()

        except requests.exceptions.RequestException as e:
            print("Erreur de connexion à Ollama:", e)
            return "Erreur de connexion à Ollama."


    def run_application(self, app_name):
        called = app_name
        # Vérifie alias
        app_name = self.ALIASES.get(app_name.lower(), app_name)

        if app_name in self.ALLOWED_APPS:
            try:
                subprocess.Popen(
                    [app_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    preexec_fn=os.setpgrp
                )
                return f"Application {called} lancée."
            except Exception as e:
                return f"Erreur lors du lancement de {called} : {e}"

        elif app_name in self.ALLOWED_FLATPAKS:
            try:
                subprocess.Popen(
                    ["flatpak", "run", app_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    preexec_fn=os.setpgrp
                )
                return f"Flatpak {called} lancé."
            except Exception as e:
                return f"Erreur lors du lancement de {called} : {e}"

        else:
            return f"Application {called} non autorisée."

    def close_application(self, app_name):
        called = app_name
        # Vérifie alias
        app_name = self.ALIASES.get(app_name.lower(), app_name)

        if app_name in self.ALLOWED_APPS:
            try:
                subprocess.run(["pkill", "-f", app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Application {called} fermée."
            except Exception as e:
                return f"Erreur lors de la fermeture de {called} : {e}"

        elif app_name in self.ALLOWED_FLATPAKS:
            try:
                subprocess.run(["flatpak", "kill", app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Flatpak {called} fermé."
            except Exception as e:
                return f"Erreur lors de la fermeture de {called} : {e}"

        else:
            return f"Application {called} non autorisée."

    def get_time(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        return f"Il est actuellement {current_time}"

    def get_day(self):
        now = datetime.today()
        current_time = now.strftime("%A %d %B %Y")
        return f"Nous sommes le {current_time}"

    def clean_think(self, ai_response_raw):
        """
        Supprime tout le bloc <think>...</think> du texte.
        Retourne le texte nettoyé.
        """
        # Supprime tous les <think>...</think> (multilignes)
        cleaned = re.sub(r"<think>.*?</think>", "", ai_response_raw, flags=re.DOTALL)
        return cleaned.strip()

    def format_markdown(self, text: str) -> str:
        """
        Transforme *texte* en texte gras avec ANSI.
        """
        return re.sub(r"\*(.*?)\*", r"\033[1m\1\033[0m", text)

    # ---------------------- BOUCLE PRINCIPALE ----------------------
    def agent_loop(self, user_input:str):
        result = ""  
        ai_response_raw = self.query_ollama(user_input)
        ai_response = self.clean_think(ai_response_raw)
        results = []
        if ai_response.startswith("ACTION:"):
            parts = ai_response.replace("ACTION:", "").strip().split()
            actions = []
            for part in parts:
                if part in self.ALLOWED_ACTIONS:
                    actions.append(part)
                else:
                    actions[-1] = actions[-1]+f" {part}"

            for action in actions:
                if "run" in action:
                    app_name = " ".join(action.strip().split()[1:])
                    results.append(self.run_application(app_name))
                elif "close" in action:
                    app_name = " ".join(action.strip().split()[1:])
                    results.append(self.close_application(app_name))
                elif "time" in action:
                    results.append(self.get_time())
                elif "day" in action:
                    results.append(self.get_day())
                elif "terminate" in action:
                    results.append(f"Aurevoir {self.name}")
                    self.cancel = True
                else: 
                    results.append(f"Action {action} non autorisée.")
        else:
            results.append(ai_response)  

        for result in results:
            result = self.format_markdown(result)
            print(f"🤖 {result}")
            self.speaker.say(result)