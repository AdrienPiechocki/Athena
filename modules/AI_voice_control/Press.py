import subprocess
import cv2
import numpy as np
import pyautogui
import time
import os
import json
import configparser

config = configparser.ConfigParser()
config.read("settings/config.cfg")
with open(f"./lang/{config.get("General", "lang", fallback=False)}.json", 'r', encoding='utf-8') as f:
    lang = json.load(f)

def clean(path):
    try:
        os.remove(path)
    except:
        pass

def Press(endroit):
    # -----------------------------
    # Take screenshot with flameshot
    # -----------------------------
    screenshot_path = "/tmp/screen.png"
    clean(screenshot_path)
    try:
        subprocess.run(["flameshot", "full", "--path", screenshot_path], check=True)
    except subprocess.CalledProcessError:
        return lang["flameshot error"]

    if not os.path.exists(screenshot_path):
        return lang["screenshot not found"]

    time.sleep(0.2)  # make sure file is ready

    # -----------------------------
    # Load images to OpenCV
    # -----------------------------
    screen = cv2.imread(screenshot_path)
    if screen is None:
        clean(screenshot_path)
        return lang["screenshot unreadable"]

    template_path = f"./modules/AI_voice_control/images/{endroit.lower()}.png"
    template = cv2.imread(template_path)
    if template is None:
        clean(screenshot_path)
        return lang["patern unreadable"]
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
        result = f"{endroit} {lang["clicked"]}."
    else:
        result = f"{endroit} {lang["not found"]}."
    clean(screenshot_path)
    return result
