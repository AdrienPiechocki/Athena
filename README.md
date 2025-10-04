# Athena
This app is a **WIP** accessible computer assistant written in Python. It works with a **local** version of Qwen3, thanks to Ollama.
For now, you can use your voice to command the AI and ask questions.

**For now, it only speaks and understands French or English**

## Warning
Some older laptops may not be able to launch the AI model due to RAM requirements...

## Installation 
```
git clone https://github.com/AdrienPiechocki/Athena.git``
cd Athena/
```
## Usage

Launch with :
```
python main.py
```
When launching for the first time, you will be prompted by the installation wizard. Follow it's steps to complete the installation.

if you need to restart the installation process, set `wizard = false` in `settings/config.cfg` or simply run 
```
python wizard.py
```
Then, restart the app.

### Voiced commands
- You can ask Athena to open, close or restart apps among those in `settings/apps.json` (customizable)
- You can ask Athena to focus existing windows (does not work very well)
- You can ask Athena what time or what day it is.
- You can ask Athena to press something on your screen (for now, it's just able to see 'play' buttons and it isn't perfect)
- You can ask Athena to shut down itself.
- You can ask Athena anything you would ask an AI (It can't generate images tough)

## What it aims to be
Athena aims to be an open source alternative to expensive assertive apps like Grid 3 (for Windows / Ipad). 
It aims to bring computer control for disabled people whatever is their disability.
In the end, Athena will be accessible by all means (even with a single button). 
This means you will be able to access your whole computer via Athena (mouse, keyboard, apps, etc.)