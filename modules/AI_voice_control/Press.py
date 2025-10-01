import subprocess
import cv2
import numpy as np
import pyautogui
import time
import os

def clean(path):
    try:
        os.remove(path)
    except:
        pass

def Press(endroit):
    # -----------------------------
    # 1️⃣ Capturer l'écran avec Flameshot
    # -----------------------------
    screenshot_path = "/tmp/screen.png"
    clean(screenshot_path)
    try:
        subprocess.run(["flameshot", "full", "--path", screenshot_path], check=True)
    except subprocess.CalledProcessError:
        return "Erreur : impossible de capturer l'écran avec Flameshot."

    if not os.path.exists(screenshot_path):
        return "Erreur : fichier de capture introuvable."

    time.sleep(0.2)  # s'assurer que le fichier est prêt

    # -----------------------------
    # 2️⃣ Charger les images avec OpenCV
    # -----------------------------
    screen = cv2.imread(screenshot_path)
    if screen is None:
        clean(screenshot_path)
        return "Erreur : impossible de lire la capture d'écran"

    template_path = f"./images/{endroit.lower()}.png"
    template = cv2.imread(template_path)
    if template is None:
        clean(screenshot_path)
        return "Erreur : impossible de lire l'image"

    # -----------------------------
    # 3️⃣ Multi-scale Template Matching
    # -----------------------------
    threshold = 0.8
    found = None

    for scale in np.linspace(0.01, 1.0):  # essaie différentes tailles (10% à 100%)
        resized = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        h, w = resized.shape[:2]

        if h > screen.shape[0] or w > screen.shape[1]:
            continue  # trop grand, skip

        result = cv2.matchTemplate(screen, resized, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val > threshold:
            found = (max_val, max_loc, (w, h))
            break  # si trouvé avec assez de confiance, stop

    if found:
        max_val, top_left, (w, h) = found
        center_x = top_left[0] + w // 2
        center_y = top_left[1] + h // 2
        pyautogui.click(center_x, center_y)
        result = f"Bouton {endroit} cliqué"
    else:
        result = f"Bouton {endroit} non trouvé"
    clean(screenshot_path)
    return result
