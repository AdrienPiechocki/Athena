# Athena
This app is a **WIP** accessible computer assistant written in Python. It works with a **local** version of Qwen3, thanks to Ollama.
For now, you can use your voice to command the AI and ask questions.

**For now, it only speaks and understands French or English**

## Installation 

### Linux
(tested on Arch with GNOME 49 and on Linux Mint 22 with Cinnamon)
- ``pip install -r requrements.txt``
- install flameshot (to take screenshot for image recognition)
- install Ollama and pull Qwen3
- install a Vosk model (for speech recognition) and put it in this folder
- in config.cfg, chose the language you want to use based on what's in the lang folder and input the path to your vosk model

### Windows
for now only on Linux

## Usage
``python main.py`` to run the app
### Voiced commands
- You can ask Athena to open or close apps among those in `settings/apps.json`
- You can ask Athena what time or what day it is.
- You can ask Athena to press something on your screen (for now, it's just able to see 'play' buttons)
- You can ask Athena to shut down itself.
- You can ask Athena anything you would ask an AI (It can't generate images tough)

## What it aims to be
Athena aims to be an open source alternative to expensive assertive apps like Grid 3 (for Windows / Ipad). 
It aims to bring computer control for disabled people whatever is their disability.
In the end, Athena will be accessible by all means (even with a single button). 
This means you will be able to access your whole computer via Athena (mouse, keyboard, apps, etc.)