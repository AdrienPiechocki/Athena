import json
import subprocess
import os
import re
from .Speaker import Speaker
from datetime import datetime
from .Press import Press
import configparser
import ollama
import shlex
import signal
import difflib

class Brain():
    name = os.getlogin()
    cancel = False
    speaker = Speaker()
    config = configparser.ConfigParser()
    config.read("settings/config.cfg")
    def __init__(self):
        self.use_logging = self.config.getboolean("Modules", "logging", fallback=False)
        self.use_ollama = self.config.getboolean("Modules", "ollama", fallback=False)
        self.use_speaker = self.config.getboolean("Modules", "speaker", fallback=False)
        with open(f"./lang/{self.config.get("General", "lang", fallback=False)}.json", 'r', encoding='utf-8') as f:
            self.lang = json.load(f)
        self.hotword = self.lang["hotword"]
        if self.use_ollama:
            self.ALLOWED_ACTIONS = self.config.get("Ollama", "actions", fallback=False)
            self.SYSTEM_PROMPT = f"""
                Tu es un assistant IA par commande vocale répondant au nom d'Athéna. Ton utilisateur s'appelle {self.name} et parle {self.lang["language"]}.
                - Si l'utilisateur te demande d'ouvrir ou de lancer une application (classique ou flatpak), réponds UNIQUEMENT avec :
                ACTION: open <nom_application_ou_alias>
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
            with open("modules/AI_voice_control/history.log", 'a') as h:
                h.write(f"{datetime.now()} [NEW SESSIONS STARTED] \n")

        with open("settings/apps.json", 'r', encoding='utf-8') as f:
            self.apps = json.load(f)
        self.ALLOWED_APPS = self.apps["ALLOWED_APPS"]

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
            return self.lang["ollama error"], e


    def parse_desktop_file(self, path):
        """Lit un fichier .desktop et retourne la commande Exec nettoyée"""
        config = configparser.ConfigParser(interpolation=None)
        config.read(path)

        if "Desktop Entry" not in config or "Exec" not in config["Desktop Entry"]:
            raise ValueError(f"{path} {self.lang["no exec"]}")

        exec_cmd = config["Desktop Entry"]["Exec"]
        # Nettoyage des placeholders (%u, %f, %U, %F, etc.)
        for placeholder in ("%u", "%U", "%f", "%F", "%i", "%c", "%k"):
            exec_cmd = exec_cmd.replace(placeholder, "")
        return exec_cmd.strip()

    def find_real_binary(self, exec_cmd):
        """Essaie de deviner le vrai binaire à partir de la commande Exec"""
        parts = shlex.split(exec_cmd)

        if not parts:
            return None

        # Cas 1 : flatpak run org.foo.Bar
        if parts[0].endswith("flatpak") and "run" in parts:
            # L'ID Flatpak est le dernier argument qui ne commence pas par --
            # et n'est pas un placeholder @@ ou %f
            for part in reversed(parts):
                if not part.startswith("--") and not part.startswith("@@") and not part.startswith("%"):
                    app_id = part
                    return ("flatpak", app_id)



        # Cas 2 : env FOO=bar myapp
        if parts[0] == "env":
            for i, token in enumerate(parts[1:], start=1):
                if "=" not in token:  # premier qui n'est pas une variable d'env
                    return ("binary", token)

        # Cas 3 : sh -c "commande ..."
        if parts[0] in ("sh", "bash") and "-c" in parts:
            idx = parts.index("-c")
            if idx + 1 < len(parts):
                inner_cmd = parts[idx + 1]
                inner_parts = shlex.split(inner_cmd)
                if inner_parts:
                    return ("binary", inner_parts[0])

        # Cas 4 : AppImage (fichier qui finit par .AppImage)
        if parts[0].endswith(".AppImage") and os.path.isfile(parts[0]):
            return ("binary", os.path.basename(parts[0]))  # ex: MyApp.AppImage

        # Cas 5 : KDE / Qt executables (kf5-xxx, qt5-xxx)
        if parts[0].startswith(("kf5", "qt5")):
            return ("binary", parts[0])

        # Cas par défaut : premier mot
        return ("binary", parts[0])



    def run_application(self, app_name):
        app_name = app_name.lower()

       # Recherche exacte ou partielle
        desktop_file = None
        best_match = None
        for file, aliases in self.ALLOWED_APPS.items():
            # Recherche exacte
            if app_name in aliases:
                desktop_file = file
                break
            # Recherche partielle / similaire
            for alias in aliases:
                if app_name in alias or alias in app_name:
                    desktop_file = file
                    best_match = alias
                    break
            if desktop_file:
                break

        # Si pas de correspondance, recherche floue (fuzzy matching)
        if not desktop_file:
            all_aliases = [(alias, file) for file, aliases in self.ALLOWED_APPS.items() for alias in aliases]
            matches = difflib.get_close_matches(app_name, [a for a, f in all_aliases], n=1, cutoff=0.8)
            if matches:
                match_alias = matches[0]
                desktop_file = next(f for a, f in all_aliases if a == match_alias)
                best_match = match_alias
        
        if desktop_file:
            try:
                exec_cmd = self.parse_desktop_file(desktop_file)
                cmd = shlex.split(exec_cmd)
                subprocess.Popen(cmd, 
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                stdin=subprocess.DEVNULL,
                                close_fds=True,
                                start_new_session=True
                                )
                return f"{self.lang["app"]} {app_name} {self.lang["lauched"]}."
            except Exception as e:
                return f"{self.lang["launch error"]} {app_name} : {e}."
        else:
            return f"{self.lang["app"]} {app_name} {self.lang["not authorized"]}."
            
    def close_application(self, app_name):
        app_name = app_name.lower()

        # Recherche exacte, partielle et fuzzy comme pour run_application
        desktop_file = None
        best_match = None
        for file, aliases in self.ALLOWED_APPS.items():
            if app_name in aliases:
                desktop_file = file
                break
            for alias in aliases:
                if app_name in alias or alias in app_name:
                    desktop_file = file
                    best_match = alias
                    break
            if desktop_file:
                break

        if not desktop_file:
            # Fuzzy matching
            all_aliases = [(alias, file) for file, aliases in self.ALLOWED_APPS.items() for alias in aliases]
            matches = difflib.get_close_matches(app_name, [a for a, f in all_aliases], n=1, cutoff=0.8)
            if matches:
                match_alias = matches[0]
                desktop_file = next(f for a, f in all_aliases if a == match_alias)
                best_match = match_alias

        if desktop_file:
            try:
                exec_cmd = self.parse_desktop_file(desktop_file)
                target = self.find_real_binary(exec_cmd)

                if not target:
                    return f"{self.lang["binary not found"]}."

                mode, value = target
                try: 
                    if mode == "flatpak":
                        subprocess.run(["flatpak", "kill", value], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, check=False)
                    else:  # mode == "binary"
                        if len(value) > 15:
                            subprocess.run(["pkill", "-f", value], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, check=False)
                        else:
                            subprocess.run(["pkill", "-TERM", value], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, check=False)
                    return f"{self.lang["app"]} {app_name} {self.lang["closed"]}."
                except subprocess.CalledProcessError:
                    return f"{self.lang["process"]} '{app_name}' {self.lang["not found"]}."

            except Exception as e:
                return f"{self.lang["close error"]} {app_name} : {e}."
        else:
            return f"{self.lang["app"]} {app_name} {self.lang["not authorized"]}."

    def get_time(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        return f"{self.lang["time"]} {current_time}."

    def get_day(self):
        now = datetime.today()
        current_time = now.strftime("%A %d %B %Y")
        return f"{self.lang["day"]} {current_time}."

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
        Transforme *texte* en texte gras avec ANSI et enlève la date du message.
        """
        pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?'
        no_datetime_text = re.sub(pattern, '', text).strip()
        return re.sub(r"\*(.*?)\*", r"\033[1m\1\033[0m", no_datetime_text)

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
                    if "open" in action and "open" in self.ALLOWED_ACTIONS:
                        app_name = " ".join(action.strip().split()[1:])
                        ai_response = ai_response.replace(f'ACTION: open {app_name}', self.run_application(app_name))
                    elif "close" in action and "close" in self.ALLOWED_ACTIONS:
                        app_name = " ".join(action.strip().split()[1:])
                        ai_response = ai_response.replace(f'ACTION: close {app_name}', self.close_application(app_name))
                    elif "time" in action and "time" in self.ALLOWED_ACTIONS:
                        ai_response = ai_response.replace('ACTION: time', self.get_time())
                    elif "day" in action and "day" in self.ALLOWED_ACTIONS:
                        ai_response = ai_response.replace('ACTION: day', self.get_day())
                    elif "press" in action and "press" in self.ALLOWED_ACTIONS:
                        endroit =  " ".join(action.strip().split()[1:])
                        ai_response = ai_response.replace(f'ACTION: press {endroit}', Press(endroit))
                    elif "terminate" in action and "terminate" in self.ALLOWED_ACTIONS:
                        ai_response = ai_response.replace('ACTION: terminate', f"{self.lang["goodbye"]} {self.name}")
                        self.cancel = True
                    else: 
                        ai_response = self.lang["non authorized action"]

            result = self.format_markdown(ai_response)
            self.log(result)
        else:
            result = self.lang["no AI"]
            self.cancel = True
            self.log(result)

    def log(self, result):
        if self.use_logging:
            print(f"🤖 {result}")
            if self.use_speaker:
                self.speaker.say(result)
