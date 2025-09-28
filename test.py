import subprocess
import cv2
import numpy as np
import pyautogui
import time
import os

# -----------------------------
# 1️⃣ Capturer l'écran avec Flameshot
# -----------------------------
screenshot_path = "/tmp/screen.png"
try:
    subprocess.run(["flameshot", "full", "--path", screenshot_path], check=True)
except subprocess.CalledProcessError:
    print("Erreur : impossible de capturer l'écran avec Flameshot.")
    exit(1)

if not os.path.exists(screenshot_path):
    print("Erreur : fichier de capture introuvable.")
    exit(1)

time.sleep(0.2)  # s'assurer que le fichier est prêt

# -----------------------------
# 2️⃣ Charger les images avec OpenCV
# -----------------------------
# Capture d'écran
screen = cv2.imread(screenshot_path)
if screen is None:
    print("Erreur : impossible de lire la capture d'écran")
    exit(1)

# Modèle du bouton pause (ex: pause.png)
image = "/home/adrien/Images/pause.png"  # à créer ou récupérer
img = cv2.imread(image)
img_8 = cv2.resize(img, (8, 8), interpolation=cv2.INTER_AREA)
img_16 = cv2.resize(img, (16, 16), interpolation=cv2.INTER_AREA)
img_32 = cv2.resize(img, (32, 32), interpolation=cv2.INTER_AREA)
img_64 = cv2.resize(img, (64, 64), interpolation=cv2.INTER_AREA)
img_128 = cv2.resize(img, (128, 128), interpolation=cv2.INTER_AREA)
images = [img_128, img_64, img_32, img_16, img_8]
for img in images:
    # -----------------------------
    # 3️⃣ Template Matching pour trouver le bouton
    # -----------------------------
    result = cv2.matchTemplate(screen, img, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Seuil de confiance pour considérer une détection valide
    threshold = 0.75
    if max_val < threshold:
        print("Bouton pause non trouvé (max_val =", max_val, ")")
        continue

    # Coordonnées du bouton
    top_left = max_loc
    h, w = img.shape[:2]
    center_x = top_left[0] + w // 2
    center_y = top_left[1] + h // 2

    # -----------------------------
    # 4️⃣ Cliquer sur le bouton
    # -----------------------------
    pyautogui.click(center_x, center_y)
    print(f"Bouton pause cliqué en ({center_x}, {center_y}) (max_val =", max_val, ")")
    break

try:
    subprocess.run(["rm", screenshot_path], check=True)
except subprocess.CalledProcessError:
    print("Erreur : impossible de supprimer l'image.")
    exit(1)
