import configparser
import subprocess
import cv2
import numpy as np
import pyautogui
import time
import json
from datetime import datetime
import difflib
import os
import pwd

class MyFunctions():
    
    name = pwd.getpwuid(os.geteuid())[0].capitalize()
    config = configparser.ConfigParser()
    config.read("settings/config.cfg")
    
    def __init__(self):
        with open(f"./lang/{self.config.get("General", "lang", fallback="en_US")}.json", 'r', encoding='utf-8') as f:
                self.lang = json.load(f)
        with open("settings/apps.json", 'r', encoding='utf-8') as f:
                self.ALLOWED_APPS = json.load(f)


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
            matches = difflib.get_close_matches(app_name, [a for a, f in all_aliases], n=1, cutoff=0.7)
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
            matches = difflib.get_close_matches(app_name, [a for a, f in all_aliases], n=1, cutoff=0.7)
            if matches:
                match_alias = matches[0]
                cmd = next(f for a, f in all_aliases if a == match_alias)
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

    def terminate(self, cancel_callback):
        cancel_callback()
        return f"{self.lang["goodbye"]} {self.name}"
    

    def clean(path):
        try:
            os.remove(path)
        except:
            pass

    def press(place):
        # -----------------------------
        # Take screenshot with flameshot
        # -----------------------------
        screenshot_path = "/tmp/screen.png"
        clean(screenshot_path)
        try:
            subprocess.run(["flameshot", "full", "--path", screenshot_path], check=True)
        except subprocess.CalledProcessError:
            return self.lang["flameshot error"]

        if not os.path.exists(screenshot_path):
            return self.lang["screenshot not found"]

        time.sleep(0.2)  # make sure file is ready

        # -----------------------------
        # Load images to OpenCV
        # -----------------------------
        screen = cv2.imread(screenshot_path)
        if screen is None:
            clean(screenshot_path)
            return self.lang["screenshot unreadable"]

        template_path = f"./modules/AI_voice_control/images/{place.lower()}.png"
        template = cv2.imread(template_path)
        if template is None:
            clean(screenshot_path)
            return self.lang["patern unreadable"]
        # -----------------------------
        # Multi-scale Template Matching
        # -----------------------------
        threshold = 0.9
        found = None

        for scale in np.linspace(0.01, 1.0):  # tries different sizes (10% to 100%)
            resized = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            h, w = resized.shape[:2]

            if h > screen.shape[0] or w > screen.shape[1]:
                continue  # too big, skip

            result = cv2.matchTemplate(screen, resized, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val > threshold:
                found = (max_val, max_loc, (w, h))
                break  # found with enough confidence, stop

        if found:
            max_val, top_left, (w, h) = found
            center_x = top_left[0] + w // 2
            center_y = top_left[1] + h // 2
            pyautogui.click(center_x, center_y)
            result = f"{place} {self.lang["clicked"]}."
        else:
            result = f"{place} {self.lang["not found"]}."
        clean(screenshot_path)
        return result

    def set_focus(self, title):
        result = os.system(f'wmctrl -a "{title}"')
        if result != 0:
            return f"{self.lang["can't find window"]} '{title}'. {self.lang["install wmctrl"]}."
        else:
            return f"{self.lang["focused"]} {title}"
