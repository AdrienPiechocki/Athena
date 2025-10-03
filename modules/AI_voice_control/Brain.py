import json
import subprocess
import os
import re
from .Speaker import Speaker
from datetime import datetime
from .Press import Press
import configparser
import ollama
import difflib
import pwd 

class Brain():
    name = pwd.getpwuid(os.geteuid())[0].capitalize()
    cancel = False
    speaker = Speaker()
    config = configparser.ConfigParser()
    config.read("settings/config.cfg")
    def __init__(self):
        self.use_logging = False
        self.use_speaker = False
        self.hotword = ""
        self.use_ollama = self.config.getboolean("Modules", "voice", fallback=False)
        if self.use_ollama:
            with open(f"./lang/{self.config.get("General", "lang", fallback="en_US")}.json", 'r', encoding='utf-8') as f:
                self.lang = json.load(f)
            self.hotword = self.lang["hotword"]
            self.use_logging = self.config.getboolean("Voice", "logging", fallback=False)
            self.use_speaker = self.config.getboolean("Voice", "speaker", fallback=False)
            self.ALLOWED_ACTIONS = self.config.get("Voice", "actions", fallback=[])
            self.SYSTEM_PROMPT = f"""
                You are an voice commanded AI assistant called {self.lang["hotword"].capitalize()}. 
                Your user is called {self.name} and speaks {self.lang["language"]}.
                - If the user asks you to open an app, ONLY answer with :
                ACTION: open <app_name>
                - If the user asks you to close an app, ONLY answer with :
                ACTION: close <app_name>
                - If the user asks for what time it is, ONLY answer with :
                ACTION: time
                - If the user asks you the date, ONLY answer with :
                ACTION: day
                - If the user asks you to stop yourself, ONLY answer with :
                ACTION: terminate
                - If the user asks you to click somewhere, ONLY answer with :
                ACTION: press <somewhere>
                If the user asks multiple actions at once, ONLY answer with :
                ACTION: <action_1> ACTION: <action_2> ACTION: ...
                Else, answer normaly and simply (one sentence or two).
                Don't use emojis.
                /no_think
                """
            self.conversation_history = [{"role": "system", "content": (self.SYSTEM_PROMPT)}]
            with open("modules/AI_voice_control/history.log", 'a') as h:
                h.write(f"{datetime.now()} [NEW SESSIONS STARTED] \n")

            with open("settings/apps.json", 'r', encoding='utf-8') as f:
                self.apps = json.load(f)
            self.ALLOWED_APPS = self.apps["ALLOWED_APPS"]

    # ---------------------- FUNCTIONS ----------------------

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
                stream=True
            )

            full_response = ""
            
            for chunk in response:
                if hasattr(chunk, "message") and hasattr(chunk.message, "content"):
                    full_response += chunk.message.content

            self.update_history(prompt, full_response)
            return full_response

        except Exception as e:
            print(self.lang["ollama error"], e)
            self.cancel = True

    def run_application(self, app_name):
        app_name = app_name.lower()

        # Exact or partial search
        cmd = None
        best_match = None
        for command, data in self.ALLOWED_APPS.items():
            # exact search
            if app_name in data["aliases"]:
                cmd = command
                break
            # partial search
            for alias in data["aliases"]:
                if app_name in alias or alias in app_name:
                    cmd = command
                    best_match = alias
                    break
            if cmd:
                break

        # With no correspondence, fuzzy matching
        if not cmd:
            all_aliases = [(alias, command) for command, data in self.ALLOWED_APPS.items() for alias in data["aliases"]]
            matches = difflib.get_close_matches(app_name, [a for a, f in all_aliases], n=1, cutoff=0.8)
            if matches:
                match_alias = matches[0]
                cmd = next(f for a, f in all_aliases if a == match_alias)
                best_match = match_alias
        
        
        if cmd:
            try:
                # Base command
                exec_cmd = [cmd]

                # Add args if any
                if data and "args" in data and data["args"].strip():
                    exec_cmd.extend(data["args"].split())
                
                # Launch
                subprocess.Popen(
                    exec_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True
                )
                return f"{self.lang['app']} {app_name} {self.lang['lauched']}."
            except Exception as e:
                return f"{self.lang['launch error']} {app_name} : {e}."
        else:
            return f"{self.lang['app']} {app_name} {self.lang['not authorized']}."

    def close_application(self, app_name):
        app_name = app_name.lower()

        # Exact or partial search
        cmd = None
        best_match = None
        for command, data in self.ALLOWED_APPS.items():
            # exact search
            if app_name in data["aliases"]:
                cmd = command
                break
            # partial search
            for alias in data["aliases"]:
                if app_name in alias or alias in app_name:
                    cmd = command
                    best_match = alias
                    break
            if cmd:
                break

        # With no correspondence, fuzzy matching
        if not cmd:
            all_aliases = [(alias, command) for command, data in self.ALLOWED_APPS.items() for alias in data["aliases"]]
            matches = difflib.get_close_matches(app_name, [a for a, f in all_aliases], n=1, cutoff=0.8)
            if matches:
                match_alias = matches[0]
                desktop_file = next(f for a, f in all_aliases if a == match_alias)
                best_match = match_alias
        

        if cmd:
            try:
                command = f"pkill -TERM {cmd}"
                executables = ["bin", "deb", "rpm", "etc", "sh", "AppImage"]
                if len(cmd) > 15:
                    command = f"pkill -f {cmd}"
                if len(cmd.split(".")) >= 3:
                    command = f"flatpak kill {cmd}"
                    if cmd.split(".")[-1] in executables:
                        command = f"pkill -TERM {cmd}"
                
                exec_cmd = command.split(" ") 
                try: 
                    subprocess.run(exec_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, check=True)
                    return f"{self.lang["app"]} {app_name} {self.lang["closed"]}."
                except subprocess.CalledProcessError:
                    return f"{self.lang["process"]} {app_name} {self.lang["not found"]}."

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
        # Deletes all the <think>...</think> (multiline)
        cleaned = re.sub(r"<think>.*?</think>", "", ai_response_raw, flags=re.DOTALL)
        return cleaned.strip()

    def format_markdown(self, text: str) -> str:
        """
        Transforme *texte* en texte gras avec ANSI et enlève la date du message.
        """
        pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?'
        no_datetime_text = re.sub(pattern, '', text).strip()
        return re.sub(r"\*(.*?)\*", r"\033[1m\1\033[0m", no_datetime_text)

    # ---------------------- MAIN LOOP ----------------------
    def agent_loop(self, user_input:str):
        if self.use_ollama:
            ai_response_raw = self.query_ollama(user_input)
            if not ai_response_raw:
                return
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
