import requests
import json
import subprocess
import os
import re
from .Speaker import Speaker
from datetime import datetime
import locale
from .Press import Press
import configparser
import ollama

class Brain():
    name = os.getlogin()
    hotword = "athéna"
    cancel = False
    speaker = Speaker()
    config = configparser.ConfigParser()

    def __init__(self):
        locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
        
        self.config.read("settings/config.cfg")
        self.use_logging = self.config.getboolean("Modules", "logging", fallback=False)
        self.use_ollama = self.config.getboolean("Modules", "ollama", fallback=False)
        self.use_speaker = self.config.getboolean("Modules", "speaker", fallback=False)
        if self.use_ollama:
            self.ALLOWED_ACTIONS = self.config.get("ollama", "actions", fallback=False)
            self.SYSTEM_PROMPT = f"""
                Tu es un assistant IA par commande vocale répondant au nom d'Athéna. Ton utilisateur s'appelle {self.name}.
                - Si l'utilisateur te demande d'ouvrir ou de lancer une application (classique ou flatpak), réponds UNIQUEMENT avec :
                ACTION: run <nom_application_ou_alias>
                - Si l'utilisateur te demande de fermer une application (classique ou flatpak), réponds UNIQUEMENT avec :
                ACTION: close <nom_application_ou_alias>
                - Si l'utilisateur te demande l'heure qu'il est, réponds UNIQUEMENT avec :
                ACTION: time
                - Si l'utilisateur te demande la date du jour, réponds UNIQUEMENT avec :
                ACTION: day
                - Si l'utilisateur te demande de t'arrêter, réponds UNIQUEMENT avec :
                ACTION: terminate
                - Si l'utilisateur te demande d'appuyer quelque part, réponds UNIQUEMENT avec :
                ACTION: press <endroit>
                Si l'utilisateur demande plusieurs actions à la fois, réponds UNIQUEMENT avec :
                ACTION: <action_1> ACTION: <action_2> ACTION: ...
                Sinon, réponds normalement et simplement (une phrase ou deux max).
                N'utilise pas d'emojis.
                /no_think
                """
            self.conversation_history = [{"role": "system", "content": (self.SYSTEM_PROMPT)}]
            
        with open("settings/apps.json", 'r', encoding='utf-8') as f:
            self.apps = json.load(f)
        self.ALLOWED_APPS = self.apps["ALLOWED_APPS"]
        self.ALLOWED_FLATPAKS = self.apps["ALLOWED_FLATPAKS"]


    # ---------------------- FONCTIONS ----------------------

    def update_history(self, prompt, response): 
        path = "modules/AI_voice_control/history.log"

        # add new info (from current session)
        with open(path, 'a') as h:
            h.write(f"{datetime.now()} PROMPT: {prompt} \n{datetime.now()} RESPONSE: {self.clean_think(response)} \n")

        self.conversation_history.append({
                "role": "user",
                "content": prompt
            })
            
        self.conversation_history.append({
                "role": "assistant",
                "content": response
            })

    def query_ollama(self, prompt):
        try:
            self.conversation_history.append({"role": "user", "content": prompt})
            
            response = ollama.chat(
                model="qwen3",
                messages=self.conversation_history,
                stream=True  # <-- important
            )

            full_response = ""
            for chunk in response:
                if hasattr(chunk, "message") and hasattr(chunk.message, "content"):
                    full_response += chunk.message.content

            self.update_history(prompt, full_response)
            return full_response


        except requests.exceptions.RequestException as e:
            print("Erreur de connexion à Ollama:", e)
            return "Erreur de connexion à Ollama"


    def run_application(self, app_name):
        app_name = app_name.lower()

        if app_name in self.ALLOWED_APPS.keys():
            try:
                subprocess.Popen(
                    [self.ALLOWED_APPS[app_name]],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    preexec_fn=os.setpgrp
                )
                return f"Application {app_name} lancée."
            except Exception as e:
                return f"Erreur lors du lancement de {app_name} : {e}."

        elif app_name in self.ALLOWED_FLATPAKS.keys():
            try:
                subprocess.Popen(
                    ["flatpak", "run", self.ALLOWED_FLATPAKS[app_name]],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    preexec_fn=os.setpgrp
                )
                return f"Flatpak {app_name} lancé."
            except Exception as e:
                return f"Erreur lors du lancement de {app_name} : {e}."

        else:
            return f"Application {app_name} non autorisée."

    def close_application(self, app_name):
        app_name = app_name.lower()

        if app_name in self.ALLOWED_APPS.keys():
            try:
                subprocess.run(["pkill", "-f", self.ALLOWED_APPS[app_name]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Application {app_name} fermée."
            except Exception as e:
                return f"Erreur lors de la fermeture de {app_name} : {e}."

        elif app_name in self.ALLOWED_FLATPAKS.keys():
            try:
                subprocess.run(["flatpak", "kill", self.ALLOWED_FLATPAKS[app_name]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Flatpak {app_name} fermé."
            except Exception as e:
                return f"Erreur lors de la fermeture de {app_name} : {e}."

        else:
            return f"Application {app_name} non autorisée."

    def get_time(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        return f"Il est actuellement {current_time}."

    def get_day(self):
        now = datetime.today()
        current_time = now.strftime("%A %d %B %Y")
        return f"Nous sommes le {current_time}."

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
        pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?'
        texte_sans_datetime = re.sub(pattern, '', text).strip()
        return re.sub(r"\*(.*?)\*", r"\033[1m\1\033[0m", texte_sans_datetime)

    # ---------------------- BOUCLE PRINCIPALE ----------------------
    def agent_loop(self, user_input:str):
        if self.use_ollama:
            ai_response_raw = self.query_ollama(user_input)
            ai_response = self.clean_think(ai_response_raw)
            if "ACTION:" in ai_response:
                ai_action = "ACTION:" + ai_response.split("ACTION:", 1)[-1]
                actions = re.findall(r"ACTION:\s*(.*?)(?=\s*ACTION:|$)", ai_action)
                actions = [a.strip() for a in actions]
                for action in actions:
                    if "run" in action:
                        app_name = " ".join(action.strip().split()[1:])
                        ai_response = ai_response.replace(f'ACTION: run {app_name}', self.run_application(app_name))
                    elif "close" in action:
                        app_name = " ".join(action.strip().split()[1:])
                        ai_response = ai_response.replace(f'ACTION: close {app_name}', self.close_application(app_name))
                    elif "time" in action:
                        ai_response = ai_response.replace('ACTION: time', self.get_time())
                    elif "day" in action:
                        ai_response = ai_response.replace('ACTION: day', self.get_day())
                    elif "press" in action:
                        endroit =  " ".join(action.strip().split()[1:])
                        ai_response = ai_response.replace(f'ACTION: press {endroit}', Press(endroit))
                    elif "terminate" in action:
                        ai_response = ai_response.replace('ACTION: terminate', f"Aurevoir {self.name}")
                        self.cancel = True
                    else: 
                        ai_response = f"Action {action} non autorisée"

            result = self.format_markdown(ai_response)
            self.log(result)
        else:
            result = "Le module d'IA n'est pas utilisé."
            self.cancel = True
            self.log(result)

    def log(self, result):
        if self.use_logging:
            print(f"🤖 {result}")
            if self.use_speaker:
                self.speaker.say(result)
