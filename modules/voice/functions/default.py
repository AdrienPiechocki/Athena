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
import platform
import sys
import __main__

def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(getattr(__main__, '__file__', sys.argv[0])))
    return os.path.join(base_path, relative_path)

config_path = resource_path("settings/config.cfg")
lang_dir = resource_path("lang")
data_dir = resource_path("data")
log_dir = resource_path("logs")
apps_path = resource_path("settings/apps.json")

config = configparser.ConfigParser()
config.read(config_path)
name = config.get('General', 'username', fallback="").capitalize()
system = platform.system()

lang_file = os.path.join(lang_dir, f"{config.get('General', 'lang', fallback='en_US')}.json")
with open(lang_file, 'r', encoding='utf-8') as f:
    lang = json.load(f)

with open(apps_path, 'r', encoding='utf-8') as f:
    ALLOWED_APPS = json.load(f)

def run_application(app_name):
    global ALLOWED_APPS, lang, system
    app_name = app_name.lower()

    if system == "Linux":
        executable = "exec_linux"
    else:
        executable = "exec_windows"

    # Exact or partial search
    cmd = None
    for data in ALLOWED_APPS.values():
        # exact search
        if app_name in data["aliases"]:
            cmd = data[executable]
            break
        # partial search
        for alias in data["aliases"]:
            if app_name in alias or alias in app_name:
                cmd = data[executable]
                break
        if cmd:
            break

    # With no correspondence, fuzzy matching
    if not cmd:
        all_aliases = [alias for data in ALLOWED_APPS.values() for alias in data["aliases"]]
        matches = difflib.get_close_matches(app_name, [a for a in all_aliases], n=1, cutoff=0.7)
        if matches:
            match_alias = matches[0]
            for data in ALLOWED_APPS.values():
                if match_alias in data["aliases"]:
                    cmd = data[executable]
                    break
    
    if cmd:
        try:
            # Base command
            exec_cmd = [cmd]

            # Add args if any
            if data and "args" in data and data["args"].strip():
                exec_cmd.extend(data["args"].split())
            
            # Linux
            if system == "Linux":
                subprocess.Popen(
                    exec_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True
                )
            # Windows
            elif system == "Windows":
                subprocess.Popen(
                    exec_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )

            else:
                return f"{lang['launch error']} {app_name} : OS ERROR."
            return f"{lang['app']} {app_name} {lang['lauched']}."
        except Exception as e:
            return f"{lang['launch error']} {app_name} : {e}."
    else:
        return f"{lang['app']} {app_name} {lang['not authorized']}."

def close_application(app_name):
    global ALLOWED_APPS, lang, system
    app_name = app_name.lower()

    if system == "Linux":
        executable = "exec_linux"
    else:
        executable = "exec_windows"

    # Exact or partial search
    cmd = None
    for data in ALLOWED_APPS.values():
        if app_name in data["aliases"]:
            cmd = data[executable]
            break
        for alias in data["aliases"]:
            if app_name in alias or alias in app_name:
                cmd = data[executable]
                break
        if cmd:
            break

    # Fuzzy matching
    if not cmd:
        all_aliases = [alias for data in ALLOWED_APPS.values() for alias in data["aliases"]]
        matches = difflib.get_close_matches(app_name, [a for a in all_aliases], n=1, cutoff=0.7)
        if matches:
            match_alias = matches[0]
            for data in ALLOWED_APPS.values():
                if match_alias in data["aliases"]:
                    cmd = data[executable]
                    break

    if cmd:
        try:
            # --- Linux ---
            if system == "Linux":
                command = f"pkill -TERM {cmd}"
                executables = ["bin", "deb", "rpm", "etc", "sh", "AppImage"]

                if len(cmd) > 15:
                    command = f"pkill -f {cmd}"
                if len(cmd.split(".")) >= 3:
                    command = f"flatpak kill {cmd}"
                    if cmd.split(".")[-1] in executables:
                        command = f"pkill -TERM {cmd}"
                        if len(cmd) > 15:
                            command = f"pkill -f {cmd}"
                            
            # --- Windows ---
            elif system == "Windows":
                cmd = cmd.split("/")[-1]
                command = f"taskkill /IM {cmd} /F"

            else:
                return f"{lang['close error']} {app_name} : OS ERROR."

            # Exécution
            exec_cmd = command.split(" ")
            try:
                subprocess.run(exec_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, check=True)
                return f"{lang['app']} {app_name} {lang['closed']}."
            except subprocess.CalledProcessError:
                return f"{lang['process']} {app_name} {lang['not found']}."

        except Exception as e:
            return f"{lang['close error']} {app_name} : {e}."
    else:
        return f"{lang['app']} {app_name} {lang['not authorized']}."


def get_time():
    global lang
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    return f"{lang['time']} {current_time}."

def get_day():
    global lang
    now = datetime.today()
    current_time = now.strftime("%A %d %B %Y")
    return f"{lang['day']} {current_time}."

def terminate(cancel_callback):
    global lang, name
    cancel_callback()
    return f"{lang['goodbye']} {name}"

def press(place):
    global lang

    # -----------------------------
    # Screenshot
    # -----------------------------
    screenshot_path = os.path.join(os.getcwd(), "screen.png")
    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)

    system = platform.system()

    try:
        if system == "Linux":
            # Linux -> flameshot
            subprocess.run(["flameshot", "full", "--path", screenshot_path], check=True)
        elif system == "Windows":
            # Windows -> pyautogui
            img = pyautogui.screenshot()
            img.save(screenshot_path)
        else:
            return f"{lang['screenshot not supported']} ({system})"
    except Exception:
        return lang["flameshot error"] if system == "Linux" else lang["screenshot error"]

    if not os.path.exists(screenshot_path):
        return lang["screenshot not found"]

    time.sleep(0.2)

    # -----------------------------
    # Load images with OpenCV
    # -----------------------------
    screen = cv2.imread(screenshot_path)
    if screen is None:
        os.remove(screenshot_path)
        return lang["screenshot unreadable"]

    template_path = f"./modules/voice/images/{place.lower()}.png"
    template = cv2.imread(template_path)
    if template is None:
        os.remove(screenshot_path)
        return lang["patern unreadable"]

    # -----------------------------
    # Multi-scale Template Matching
    # -----------------------------
    threshold = 0.9
    found = None

    for scale in np.linspace(0.01, 1.0):  # 1% à 100%
        resized = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        h, w = resized.shape[:2]

        if h > screen.shape[0] or w > screen.shape[1]:
            continue

        result = cv2.matchTemplate(screen, resized, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val > threshold:
            found = (max_val, max_loc, (w, h))
            break

    if found:
        max_val, top_left, (w, h) = found
        center_x = top_left[0] + w // 2
        center_y = top_left[1] + h // 2
        pyautogui.click(center_x, center_y)
        result = f"{place} {lang['clicked']}."
    else:
        result = f"{place} {lang['not found']}."

    os.remove(screenshot_path)
    return result

def set_focus(title):
    global lang, system

    if system == "Linux":

        result = os.system(f'wmctrl -a "{title}"')
        if result != 0:
            return f"{lang['cant find window']} '{title}'. {lang['no wayland']}."
        else:
            return f"{lang['focused']} {title}"
    

    elif system == "Windows":
        import win32gui
        import win32con
        import win32api

        target_hwnd = None

        def enum_windows_callback(hwnd, _):
            nonlocal target_hwnd
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if title.lower() in window_title.lower():
                    target_hwnd = hwnd

        win32gui.EnumWindows(enum_windows_callback, None)

        if target_hwnd:
            win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)

            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # Alt down
            time.sleep(0.05)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt up

            win32gui.SetForegroundWindow(target_hwnd)
            return f"{lang['focused']} '{win32gui.GetWindowText(target_hwnd)}'"
        else:
            return f"{lang['cant find window']} '{title}'."

    else:
        return "OS ERROR"


def browse(subject):
    global ALLOWED_APPS, lang, system

    cmd = None
    search_url = None
    browser = None
    for data in ALLOWED_APPS.values():
        if "browser" in data.keys():
            search_url = data["browser"]
            if system == "Linux":
                browser = data["exec_linux"]
            else:
                browser = data["exec_windows"]
            break
        
    if search_url and browser:
        research = subject.replace(" ", "+")
        cmd = f"{browser} {search_url}{research}"
    else:
        return lang["no browser defined"]

    try:
        exec_cmd = cmd.split(" ")
        
        # Linux
        if system == "Linux":
            subprocess.Popen(
                exec_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True
            )
        # Windows
        else:
            subprocess.Popen(
                exec_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        return f"{lang['searching for']} {subject}"
    except Exception as e:
        return e
