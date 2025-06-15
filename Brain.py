import json
import os
import datetime
from Speaker import Speaker

class Brain:

    speaker = Speaker()
    name = "Maitre"
    hotword = "athéna"
    cancel = False

    def __init__(self, actions="actions.json", subjects="subjects.json"):
        with open(actions, 'r', encoding='utf-8') as f:
            self.actions = json.load(f)
        with open(subjects, 'r', encoding='utf-8') as f:
            self.subjects = json.load(f)

    def commander(self, command:str, text:str):
        answer = "je n'ai pas compris"
        if command == "stop":
            answer = f"aurevoir {self.name}"
            self.cancel = True
        
        if command == "time":
            t = datetime.datetime.now()
            answer = f"il est {t.strftime("%H")} heure {t.strftime("%M")}"
        
        if command == "search":
            searches = self.actions.get("search").keys()
            words = text.split()
            #get search type:
            action = "duck"
            for search in searches:
                s = self.actions.get("search").get(search)
                for word in words:
                    if word in s:
                        action = word
            #remove ask for search part in sentence:
            index = 0 
            for word in words:
                if word in self.actions.get("commands").get("search"):
                    index = words.index(word)+1
            l = []
            for word in words: 
                if words.index(word) < index:
                    l.append(word)
            text = text.replace(" ".join(l), "")

            #remove search type from sentence:
            for search in searches:
                if f"sur {search}" in text:
                    text = text.replace(f"sur {search}", "")

            subject = text
            self.execute(action, subject)
            return

        print(f"🟢 {answer}")
        self.speaker.say(answer)

    def execute(self, action:str, subject:str):
        answer = "je n'ai pas compris"

        if action == "open":
            os.system(self.subjects.get("app").get(subject).get("open") + " &")
            answer = f"j'ouvre {self.subjects.get("app").get(subject).get("call")}"
        if action == "close":
            os.system(self.subjects.get("app").get(subject).get("close"))
            answer = f"je ferme {self.subjects.get("app").get(subject).get("call")}"
        
        if action == "youtube":
            os.system(f'firefox https://www.youtube.com/results?search_query="{subject}"')
            answer = f"je recherche {subject} sur youtube"
        if action == "twitch":
            os.system(f'firefox https://www.twitch.tv/search?term="{subject}"')
            answer = f"je recherche {subject} sur twitch"
        if action == "nexus":
            os.system(f'firefox https://www.nexusmods.com/search?keyword="{subject}"')
            answer = f"je recherche {subject} sur nexus"
        if action == "duck":
            os.system(f'firefox --search "{subject}"')
            answer = f"je recherche {subject} sur internet"

        print(f"🟢 {answer}")
        self.speaker.say(answer)

    def analyze_question(self, input_text:str):
        
        words = input_text.split()
        action = ""
        subject = ""
        action_keys = self.actions.keys()
        commands = self.actions.get("commands").keys()
        flag = True

        for command in commands:
            c = self.actions.get("commands").get(command)
            for x in c:
                if x in input_text:
                    self.commander(command, input_text)
                    flag = False
                    return
        if flag:
            for word in words:
                if word in self.actions.get("open"):
                    action = "open"
                    index = words.index(word)
                    words = words[index:]
                if word in self.actions.get("close"):
                    action = "close"
                    index = words.index(word)
                    words = words[index:]
            
            for word in words:
                if word in self.subjects.get("app").keys():
                    subject = word

            if action != "" and subject != "":
                self.execute(action, subject)

