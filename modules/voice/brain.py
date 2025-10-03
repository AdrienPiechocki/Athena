import json
import os
import re
from .speaker import Speaker
import configparser
import ollama
import pwd 
import textwrap
from datetime import datetime
import sys
sys.path.append(os.path.dirname(__file__))
from .functions import *

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
            actions_str = self.config.get("Voice", "actions", fallback="")
            self.ALLOWED_ACTIONS = [a.strip() for a in actions_str.split(",")]
            self.SYSTEM_PROMPT = textwrap.dedent(f"""
                You are an voice commanded AI assistant called {self.lang["hotword"].capitalize()}. 
                Your user is called {self.name} and speaks {self.lang["language"]}.
                """)
                
            for action in self.ALLOWED_ACTIONS:
                    text = self.config.get("Voice", f"action_{action}", fallback="")
                    self.SYSTEM_PROMPT += text.replace("\\n", "\n")

            self.SYSTEM_PROMPT += textwrap.dedent("""
                If the user asks multiple actions at once, ONLY answer with :
                ACTION: <action_1> ACTION: <action_2> ACTION: ...
                Else, answer normaly and simply (one sentence or two).
                Don't use emojis.
                /no_think
                """)
            self.conversation_history = [{"role": "system", "content": (self.SYSTEM_PROMPT)}]
            with open("modules/voice/history.log", 'a') as h:
                h.write(f"{datetime.now()} [NEW SESSIONS STARTED] \n")

            with open("settings/apps.json", 'r', encoding='utf-8') as f:
                self.ALLOWED_APPS = json.load(f)

    # ---------------------- FUNCTIONS ----------------------

    def update_history(self, prompt, response): 
        path = "modules/voice/history.log"

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
                for full_action in actions:
                    params = " ".join(full_action.strip().split()[1:])
                    action = full_action.replace(params, "").strip()
                    if action in self.ALLOWED_ACTIONS:
                        import functions
                        func_name = self.config.get("Voice", f"function_{action}", fallback="")
                        call = functions.functions_registry.get(func_name)
                        if call:
                            if action == "terminate":
                                func_result = call(cancel_callback=lambda: setattr(self, "cancel", True))
                            elif params:
                                func_result = call(params)
                            else:
                                func_result = call()
                            ai_response = ai_response.replace(f'ACTION: {full_action}', func_result)
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
