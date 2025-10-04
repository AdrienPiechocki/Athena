import os
import platform
import subprocess
import sys
import shutil
import time
from tqdm import tqdm
import configparser
import json

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
config_path = os.path.join(BASE_DIR, "settings", "config.cfg")
config = configparser.ConfigParser()
config.read(config_path)
lang_dir = os.path.join(BASE_DIR, "lang")
lang_file = os.path.join(lang_dir, f"{config.get('General', 'lang', fallback='en_US')}.json")
with open(lang_file, 'r', encoding='utf-8') as f:
    lang = json.load(f)

# --- Couleurs console ---
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

# --- Fonctions utilitaires ---
def print_banner():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"""{Colors.OKCYAN}
    ===============================================
              {lang['auto-install title']}
    ===============================================
    """)

def run_command(cmd, shell=False, silent=False):
    cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
    if not silent:
        print(f"{Colors.OKBLUE}➡️  {lang['executing']} : {cmd_str}{Colors.RESET}")
    try:
        if silent:
            subprocess.check_call(cmd, shell=shell, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.check_call(cmd, shell=shell)
    except subprocess.CalledProcessError:
        print(f"{Colors.FAIL}❌ {lang['exec error']} : {cmd_str}{Colors.RESET}")

def progress_step(description, duration=2):
    for _ in tqdm(range(duration * 20), desc=description, ncols=80, colour="cyan"):
        time.sleep(0.05)

# --- Python virtualenv ---
def install_requirements_venv(silent=False):
    venv_dir = os.path.join(BASE_DIR, ".venv")
    venv_python = os.path.join(venv_dir, "bin", "python") if os.name != "nt" else os.path.join(venv_dir, "Scripts", "python.exe")
    venv_pip = [venv_python, "-m", "pip"]

    if not os.path.exists(venv_dir):
        print(f"{Colors.OKCYAN}🧩 {lang['venv creation']}{Colors.RESET}")
        run_command([sys.executable, "-m", "venv", venv_dir], silent=silent)
    else:
        print(f"{Colors.OKCYAN}🔄 {lang['venv update']}{Colors.RESET}")

    # Mettre à jour pip
    run_command(venv_pip + ["install", "--upgrade", "pip"], silent=silent)

    # Installer / mettre à jour les dépendances
    requirements = os.path.join(BASE_DIR, "requirements.txt")
    if os.path.exists(requirements):
        progress_step(lang["python install"], 2)
        run_command(venv_pip + ["install", "--upgrade", "-r", requirements], silent=silent)
    else:
        print(f"{Colors.WARNING}⚠️  {lang['no requirements found']}{Colors.RESET}")

# --- Ollama ---
def install_ollama_model(silent=False):
    if shutil.which("ollama"):
        progress_step(lang["qwen3 install"], 3)
        run_command(["ollama", "pull", "qwen3"], silent=silent)
    else:
        print(f"{Colors.WARNING}⚠️  {lang['ollama not found']}{Colors.RESET}")

# --- Dépendances système ---
def install_linux(silent=False):
    print(f"{Colors.HEADER}🐧 {lang['linux install']}{Colors.RESET}")
    if shutil.which("apt"):
        pkg_manager = "apt"
    elif shutil.which("pacman"):
        pkg_manager = "pacman"
    elif shutil.which("dnf"):
        pkg_manager = "dnf"
    else:
        print(f"{Colors.FAIL}❌ {lang['no package manager']}{Colors.RESET}")
        return

    progress_step(lang["package update"], 2)
    if pkg_manager == "apt":
        run_command(["sudo", "apt", "update"], silent=silent)
    elif pkg_manager == "pacman":
        run_command(["sudo", "pacman", "-Sy"], silent=silent)
    elif pkg_manager == "dnf":
        run_command(["sudo", "dnf", "makecache"], silent=silent)

    progress_step(lang["packages installation"], 3)
    packages = ["flameshot", "wmctrl", "espeak-ng", "curl"]
    if pkg_manager == "apt":
        run_command(["sudo", "apt", "install", "-y"] + packages, silent=silent)
    elif pkg_manager == "pacman":
        run_command(["sudo", "pacman", "-S", "--noconfirm"] + packages, silent=silent)
    elif pkg_manager == "dnf":
        run_command(["sudo", "dnf", "install", "-y"] + packages, silent=silent)

    if not shutil.which("ollama"):
        print(f"{Colors.OKCYAN}🧩 {lang['ollama install']}{Colors.RESET}")
        run_command("curl -fsSL https://ollama.com/install.sh | sh", shell=True, silent=silent)

    install_ollama_model(silent=silent)

def install_windows(silent=False):
    print(f"{Colors.HEADER}🪟 {lang['windows install']}{Colors.RESET}")
    if not shutil.which("espeak-ng"):
        progress_step(lang["espeak install"], 2)
        run_command(["winget", "install", "-e", "--id", "espeak-ng.espeak-ng"], silent=silent)

    if not shutil.which("ollama"):
        progress_step(lang["ollama install"], 2)
        run_command(["winget", "install", "-e", "--id", "Ollama.Ollama"], silent=silent)

    install_ollama_model(silent=silent)

# --- Main ---
def main():
    silent = "--silent" in sys.argv
    print_banner()
    system = platform.system().lower()
    print(f"{Colors.OKBLUE}🖥️  {lang['system detected']} : {system.capitalize()}{Colors.RESET}\n")

    try:
        if "linux" in system:
            install_linux(silent=silent)
        elif "windows" in system:
            install_windows(silent=silent)
        else:
            print(f"{Colors.FAIL}❌ {lang['wrong system']} : {system}{Colors.RESET}")
            sys.exit(1)

        install_requirements_venv(silent=silent)
        progress_step(lang["finish install"], 2)

        print(f"\n{Colors.OKGREEN}✅ {lang['install success']}{Colors.RESET}")

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}{lang['install interupted']}{Colors.RESET}")

if __name__ == "__main__":
    main()
