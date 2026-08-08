# 🎵 BPSound - Automated Hourly Audio Player

![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)
![GUI Framework](https://img.shields.io/badge/GUI-Tkinter-orange.svg)
![Audio Engine](https://img.shields.io/badge/Audio-Pygame-green.svg)
![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)

**BPSound** is a lightweight desktop application designed to play `.mp3` audio files automatically based on set hourly schedules. Built with a user-friendly dark interface, it simplifies audio management for routine scheduling tasks.

---

## ✨ Key Features

* **Flexible Audio Scheduling:** Assign specific MP3 files to any hour and minute.
* **Interactive Time Picker:** Dual dropdown menus (hours & minutes) for quick and seamless time selection.
* **Full Control Management (CRUD):**
  * ➕ **Add New:** Create new time-to-audio schedules.
  * ✏️ **Update:** Change audio tracks or times for existing schedules.
  * 🗑️ **Delete:** Remove selected schedules from the list.
  * ⏹️ **Stop:** Immediately stop the currently playing audio.
* **Auto-Save Configuration:** Schedules are saved automatically to `config_bpsound.json`.
* **Multi-Threading Engine:** Background playback monitoring keeps the interface responsive without freezing.

---

## 🛠️ Built With

* **Language:** Python 3.12 / 3.13
* **GUI Framework:** `tkinter` & `tkinter.ttk`
* **Audio Engine:** `pygame.mixer`
* **Storage:** JSON (`config_bpsound.json`)

---

## 📁 Project Structure

```text
BPSound/
├── bpsound.py            # Main application source code
├── config_bpsound.json   # Auto-generated configuration file
├── .gitignore            # Git ignore rules
└── README.md             # Project documentation
```
## 🚀 Getting Started

### 1. Prerequisites
Ensure Python is installed on your system. Install the required dependency via terminal:

```bash
py -m pip install pygame
```

### 2. Running the Application
Execute the following command in your PowerShell or Terminal:

```bash
py bpsound.py
```

### 3. Usage Guide
1. Select the **Hour** and **Minute** from the dropdown menus.
2. Click **🎵 Choose MP3** to select an audio file from your local directory.
3. Click **➕ Add New** to add it to the schedule list.
4. Click any item on the list to edit or update its song using **✏️ Update / Change Track**.
5. Use **🗑️ Delete** to remove a schedule or **⏹️ Stop** to halt audio playback immediately.'''
---

## 📦 Build Standalone Executable (.exe)

To run the application on other systems without installing Python:

1. Instal PyInstaller:
   ```bash
   py -m pip install pyinstaller
   ```
2. Build the .exe file:
   ```bash
   pyinstaller --noconsole --onefile bpsound.py
   ```
3. Find your executable inside the dist/ directory.

---

## 📄 Recommended `.gitignore`

```plaintext
__pycache__/
*.pyc
build/
dist/
*.spec
config_bpsound.json
```
---