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

    def commander(self, command:str, remaining_text:str):
        answer = "je n'ai pas compris"
        if command == "stop":
            answer = f"aurevoir {self.name}"
            self.cancel = True
        
        if command == "time":
            t = datetime.datetime.now()
            answer = f"il est {t.strftime("%H")} heure {t.strftime("%M")}"

        if command == "search":
            os.system(f'firefox -search "{remaining_text}"')
            answer = f"je recherche sur internet: {remaining_text}"

        print(f"🟢 {answer}")
        self.speaker.say(answer)

    def execute(self, action, subject):
        answer = "je n'ai pas compris"

        if action == "open":
            os.system(self.subjects.get("app").get(subject)[0] + " &")
            answer = f"j'ouvre {subject}"
        if action == "close":
            os.system(self.subjects.get("app").get(subject)[1])
            answer = f"je ferme {subject}"
        
        print(f"🟢 {answer}")
        self.speaker.say(answer)

    def analyze_question(self, input_text:str):
        
        words = input_text.split()
        
        action_keys = self.actions.keys()
        commands = self.actions.get("commands").keys()

        for command in commands:
            c = self.actions.get("commands").get(command)
            for x in c:
                if x in input_text:
                    for word in words:
                        if word == "recherche":
                            index = words.index(word)+1
                            words = words[index:]
                    self.commander(command, " ".join(words))
                    break

        action = ""
        for word in words:
            for key in action_keys:
                if word in self.actions.get(key):
                    action = key
                    index = words.index(word)
                    words = words[index:]


        subject = ""
        for word in words:
            if word in self.subjects.get("app"):
                subject = word

        if action != "" and subject != "":
            self.execute(action, subject)

