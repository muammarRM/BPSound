# 🎵 BPSound - Automated Hourly Audio Player

![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)
![GUI Framework](https://img.shields.io/badge/GUI-Tkinter-orange.svg)
![Audio Engine](https://img.shields.io/badge/Audio-Pygame-green.svg)
![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)

**BPSound** is a feature-rich desktop application designed to play audio and extracted video soundtracks automatically based on hourly and day-specific schedules. Built with a modern dark interface, it streamlines automated public announcements, background music, or hourly audio reminders.

---

## ✨ Key Features

* 📅 **Day-Based & Hourly Scheduling:** Assign audio files to specific days of the week (Monday–Sunday) or set them to play every day.
* 🎬 **Automatic Video-to-Audio Conversion:** Select video files (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.flv`) and BPSound will automatically extract and cache the audio as `.mp3` using `moviepy`.
* 🔊 **Master Volume Control:** Interactive real-time volume slider (0% to 100%) integrated with the Pygame audio engine.
* ▶️ **Audio Testing & Quick Preview:**
  * Click **▶ Tes Audio** to preview selected tracks before saving.
  * **Double-click** any schedule in the list to trigger immediate playback testing.
* ⏰ **Real-Time Digital Clock & Status Monitor:** Header clock with live seconds display and dynamic playback status indicators.
* 🛠️ **Full Schedule Management (CRUD):**
  * ➕ **Add New:** Create new time, day, and track schedules.
  * ✏️ **Update:** Modify existing schedules or switch assigned media.
  * 🗑️ **Delete:** Remove schedules from the active list.
  * 🔄 **Reset Form:** Clear current form selection to create a new entry quickly.
  * ⏹️ **Stop:** Halt currently playing audio immediately.
* 💾 **Auto-Save & Backward Compatibility:** Configuration automatically syncs to `config_bpsound.json`.
* ⚡ **Multi-Threaded Engine:** Non-blocking background thread continuously monitors clock schedules without freezing the UI.
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
py -m pip install pygame moviepy
```

### 2. Running the Application
Execute the following command in your PowerShell or Terminal:

```bash
py bpsound.py
```

### 3. Usage Guide
1. **Set Time:** Choose the **Hour** and **Minute** from the dropdown menus.
2. **Select Days:** Check the specific days of the week or check **Setiap Hari** (Everyday).
3. **Choose File:** Click **🎵 Pilih File** to choose an audio (`.mp3`, `.wav`, `.ogg`) or video file (`.mp4`, `.avi`, etc.).
4. **Test Track (Optional):** Click **▶ Tes Audio** to verify the sound level.
5. **Add/Update Schedule:** Click **➕ Tambah Baru** to save the schedule, or **✏️ Update Jadwal** to edit an existing entry.
6. **Quick Test:** Double-click any item in the schedule list to test playback immediately.
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
# Python cache
__pycache__/
*.pyc

# Build outputs
build/
dist/
*.spec

# Local user configurations & cached conversions
config_bpsound.json
converted_audio_cache/
```
---