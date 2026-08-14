import json
import os
import sys
import threading
import time
from datetime import datetime
from tkinter import (
    Button,
    Checkbutton,
    Frame,
    BooleanVar,
    Label,
    Listbox,
    Scrollbar,
    Scale,
    HORIZONTAL,
    Tk,
    filedialog,
    messagebox,
    ttk,
)

import ctypes

# Virtual Key Code untuk Media Play/Pause di Windows
VK_MEDIA_PLAY_PAUSE = 0xAF
KEYEVENTF_KEYUP = 0x0002

from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

def set_other_apps_mute(mute=True):
    """Membungkam (mute) atau mengembalikan suara (unmute) aplikasi lain selain BPSound."""
    try:
        # Inisialisasi COM untuk thread yang sedang berjalan
        ctypes.windll.ole32.CoInitialize(None)

        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            volume = session._ctl.QueryInterface(ISimpleAudioVolume)
            if session.Process and session.Process.name():
                proc_name = session.Process.name().lower()
                # Jangan mute Python / BPSound itu sendiri!
                if "python" not in proc_name and "bpsound" not in proc_name:
                    volume.SetMute(mute, None)
    except Exception as e:
        print(f"Gagal mengatur mute aplikasi lain: {e}")
    finally:
        # Uninitialize COM setelah selesai
        ctypes.windll.ole32.CoUninitialize()

import pygame
# ============================================================
# MOVIEPY + FFMPEG
# ============================================================

# Jika dijalankan sebagai EXE PyInstaller
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------
# Cari FFmpeg dari imageio-ffmpeg
# ------------------------------------------------------------
FFMPEG_EXE = None
FFMPEG_AVAILABLE = False

try:
    import imageio_ffmpeg

    # Cara normal
    try:
        FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        FFMPEG_EXE = None

    # Kalau PyInstaller gagal menemukan executable,
    # cari langsung di folder bundle.
    if not FFMPEG_EXE or not os.path.exists(FFMPEG_EXE):

        possible_ffmpeg_paths = [
            os.path.join(
                BASE_DIR,
                "imageio_ffmpeg",
                "binaries",
                "ffmpeg-win-x86_64.exe"
            ),

            os.path.join(
                BASE_DIR,
                "imageio_ffmpeg",
                "binaries",
                "ffmpeg-win32.exe"
            ),

            os.path.join(
                BASE_DIR,
                "ffmpeg.exe"
            ),
        ]

        for path in possible_ffmpeg_paths:
            if os.path.exists(path):
                FFMPEG_EXE = path
                break

    if FFMPEG_EXE and os.path.exists(FFMPEG_EXE):
        FFMPEG_AVAILABLE = True

        # Sangat penting untuk MoviePy / imageio
        os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_EXE

        print(f"FFmpeg ditemukan: {FFMPEG_EXE}")
    else:
        print("FFmpeg tidak ditemukan di bundle.")

except Exception as e:
    print(f"FFmpeg tidak tersedia: {e}")


# ------------------------------------------------------------
# MoviePy
# ------------------------------------------------------------
try:
    try:
        from moviepy.editor import VideoFileClip
    except ImportError:
        from moviepy import VideoFileClip

    MOVIEPY_AVAILABLE = True
    print("MoviePy berhasil dimuat.")

except Exception as e:
    print(f"MoviePy tidak tersedia: {e}")
    MOVIEPY_AVAILABLE = False

# Inisialisasi Audio Engine
pygame.mixer.init()

CONFIG_FILE = "config_bpsound.json"
CACHE_DIR = "converted_audio_cache"

# List Hari
DAYS_LIST = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

# === PALET WARNA BPS SOUND (DARK THEME) ===
COLOR_BG = "#121212"
COLOR_CARD = "#1E1E1E"
COLOR_PRIMARY = "#0066CC"
COLOR_TEXT = "#FFFFFF"
COLOR_MUTED = "#A0A0A0"

COLOR_ADD = "#0284C7"
COLOR_UPDATE = "#D97706"
COLOR_DELETE = "#DC2626"
COLOR_STOP = "#4B5563"
COLOR_RESET = "#475569"
COLOR_PREVIEW = "#059669"


def make_hoverable(button, bg_normal, bg_hover):
    """Menambahkan efek hover pada tombol Tkinter."""
    button.bind("<Enter>", lambda e: button.config(bg=bg_hover))
    button.bind("<Leave>", lambda e: button.config(bg=bg_normal))


class BPSoundApp:

    def __init__(self, root):
        self.root = root
        self.root.title("BPSound - BPS Automated Hourly Audio Player")
        self.root.geometry("580x810")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(True, True)

        self.schedule_data = {}
        self.temp_file_path = ""
        self.last_played_hour = None
        self.is_running = True

        # Buat folder cache konversi jika belum ada
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        # Variabel Checkbox Hari
        self.day_vars = {day: BooleanVar(value=True) for day in DAYS_LIST}
        self.var_everyday = BooleanVar(value=True)

        # Variabel pelacak mode layout saat ini
        self.current_layout = None  # 'vertical' atau 'horizontal'

        self.load_config()
        self.setup_ui()

        self.root.bind("<Configure>", self.on_window_resize)

        # Jalankan Update Jam Real-Time UI
        self.update_realtime_clock()

        # Loop Pengecekan Playback Otomatis
        self.check_playback_status()

        # Thread Background untuk Cek Jam & Hari Jadwal
        self.checker_thread = threading.Thread(
            target=self.check_schedule_loop, daemon=True
        )
        self.checker_thread.start()
        self.last_played_hour = None
        self.is_running = True
        self.external_media_paused = False  # Status media eksternal

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "TCombobox",
            fieldbackground="#2A2A2A",
            background="#3A3A3A",
            foreground="white",
            bordercolor=COLOR_CARD,
        )

        # === HEADER SECTION (DENGAN JAM REALTIME) ===
        frame_header = Frame(self.root, bg=COLOR_BG)
        frame_header.pack(fill="x", padx=20, pady=(15, 5))

        header_top = Frame(frame_header, bg=COLOR_BG)
        header_top.pack(fill="x")

        Label(
            header_top,
            text="BPSound Player",
            font=("Segoe UI", 18, "bold"),
            fg=COLOR_PRIMARY,
            bg=COLOR_BG,
        ).pack(side="left")

        self.lbl_clock = Label(
            header_top,
            text="00:00:00",
            font=("Consolas", 16, "bold"),
            fg="#60A5FA",
            bg=COLOR_BG,
        )
        self.lbl_clock.pack(side="right")

        self.lbl_status = Label(
            frame_header,
            text="● Memantau jadwal pemutaran...",
            fg="#10B981",
            bg=COLOR_BG,
            font=("Segoe UI", 10, "bold"),
        )
        self.lbl_status.pack(anchor="w", pady=(4, 0))

        # === KONTAINER UTAMA BERSAMA ===
        self.main_container = Frame(self.root, bg=COLOR_BG)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # === CARD FORM INPUT (SISI KIRI / ATAS) ===
        self.card_input = Frame(self.main_container, bg=COLOR_CARD, padx=15, pady=15)

        Label(
            self.card_input,
            text="Kelola Jadwal & Lagu/Video",
            font=("Segoe UI", 11, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD,
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 2))

        Label(
            self.card_input,
            text="💡 Format: Audio (MP3, WAV, OGG) • Video (MP4, MOV, AVI, MKV, WEBM, FLV)",
            font=("Segoe UI", 8, "italic"),
            fg="#38BDF8",
            bg=COLOR_CARD,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

        Label(
            self.card_input,
            text="Pilih Jam:",
            font=("Segoe UI", 10),
            fg=COLOR_TEXT,
            bg=COLOR_CARD,
        ).grid(row=2, column=0, sticky="w")

        time_frame = Frame(self.card_input, bg=COLOR_CARD)
        time_frame.grid(row=2, column=1, sticky="w", padx=5)

        hours_list = [f"{i:02d}" for i in range(24)]
        self.combo_hour = ttk.Combobox(
            time_frame, values=hours_list, width=3, state="normal"
        )
        self.combo_hour.set("08")
        self.combo_hour.pack(side="left")

        Label(
            time_frame,
            text=" : ",
            font=("Segoe UI", 11, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD,
        ).pack(side="left")

        minutes_list = [f"{i:02d}" for i in range(60)]
        self.combo_minute = ttk.Combobox(
            time_frame, values=minutes_list, width=3, state="normal"
        )
        self.combo_minute.set("00")
        self.combo_minute.pack(side="left")

        media_btn_frame = Frame(self.card_input, bg=COLOR_CARD)
        media_btn_frame.grid(row=2, column=2, sticky="e")

        self.btn_select_file = Button(
            media_btn_frame,
            text="🎵 Pilih File",
            command=self.browse_media,
            bg="#374151",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2,
            font=("Segoe UI", 9),
        )
        self.btn_select_file.pack(side="left", padx=(0, 4))
        make_hoverable(self.btn_select_file, "#374151", "#4B5563")

        self.btn_preview = Button(
            media_btn_frame,
            text="▶ Tes Audio",
            command=self.preview_media,
            bg=COLOR_PREVIEW,
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2,
            font=("Segoe UI", 9, "bold"),
        )
        self.btn_preview.pack(side="left")
        make_hoverable(self.btn_preview, COLOR_PREVIEW, "#047857")

        self.lbl_selected_file = Label(
            self.card_input,
            text="Belum ada file dipilih",
            fg=COLOR_MUTED,
            bg=COLOR_CARD,
            font=("Segoe UI", 9, "italic"),
            anchor="w",
        )
        self.lbl_selected_file.grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(6, 8)
        )

        vol_frame = Frame(self.card_input, bg=COLOR_CARD)
        vol_frame.grid(row=4, column=0, columnspan=3, sticky="we", pady=(0, 10))

        Label(
            vol_frame,
            text="Volume Master:",
            font=("Segoe UI", 9, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD,
        ).pack(side="left")

        self.slider_volume = Scale(
            vol_frame,
            from_=0,
            to=100,
            orient=HORIZONTAL,
            showvalue=True,
            bg=COLOR_CARD,
            fg=COLOR_TEXT,
            highlightthickness=0,
            troughcolor="#333333",
            activebackground=COLOR_PRIMARY,
            length=250,
            command=self.change_volume,
        )
        self.slider_volume.set(80)
        pygame.mixer.music.set_volume(0.8)
        self.slider_volume.pack(side="right")

        Label(
            self.card_input,
            text="Pilih Hari Pemutaran:",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD,
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(5, 5))

        days_frame = Frame(self.card_input, bg=COLOR_CARD)
        days_frame.grid(row=6, column=0, columnspan=3, sticky="w", pady=(0, 10))

        cb_everyday = Checkbutton(
            days_frame,
            text="Setiap Hari",
            variable=self.var_everyday,
            command=self.toggle_everyday,
            bg=COLOR_CARD,
            fg="#60A5FA",
            selectcolor="#333333",
            activebackground=COLOR_CARD,
            activeforeground="#60A5FA",
            font=("Segoe UI", 9, "bold"),
        )
        cb_everyday.pack(anchor="w", pady=(0, 5))

        days_grid_frame = Frame(days_frame, bg=COLOR_CARD)
        days_grid_frame.pack(anchor="w")

        for idx, day in enumerate(DAYS_LIST):
            cb = Checkbutton(
                days_grid_frame,
                text=day[:3],
                variable=self.day_vars[day],
                command=self.on_day_toggle,
                bg=COLOR_CARD,
                fg=COLOR_TEXT,
                selectcolor="#333333",
                activebackground=COLOR_CARD,
                activeforeground=COLOR_TEXT,
                font=("Segoe UI", 9),
            )
            col = idx % 4
            row = idx // 4
            cb.grid(row=row, column=col, sticky="w", padx=(0, 10), pady=2)

        frame_form_btns = Frame(self.card_input, bg=COLOR_CARD)
        frame_form_btns.grid(row=7, column=0, columnspan=3, sticky="we", pady=(10, 0))

        self.btn_add = Button(
            frame_form_btns,
            text="➕ Tambah Baru",
            command=self.add_schedule,
            bg=COLOR_ADD,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            pady=6,
        )
        self.btn_add.pack(side="left", expand=True, fill="x", padx=(0, 3))
        make_hoverable(self.btn_add, COLOR_ADD, "#0369A1")

        self.btn_update = Button(
            frame_form_btns,
            text="✏️ Update Jadwal",
            command=self.update_schedule,
            bg=COLOR_UPDATE,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            pady=6,
        )
        self.btn_update.pack(side="left", expand=True, fill="x", padx=3)
        make_hoverable(self.btn_update, COLOR_UPDATE, "#B45309")

        self.btn_reset = Button(
            frame_form_btns,
            text="Jadwal Baru",
            command=self.clear_form,
            bg=COLOR_RESET,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            pady=6,
        )
        self.btn_reset.pack(side="left", expand=True, fill="x", padx=(3, 0))
        make_hoverable(self.btn_reset, COLOR_RESET, "#334155")

        # === KONTAINER DAFTAR JADWAL (SISI KANAN / BAWAH) ===
        self.list_container = Frame(self.main_container, bg=COLOR_BG)

        Label(
            self.list_container,
            text="Daftar Jam Terpasang (Klik 2x untuk Tes Audio):",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_BG,
        ).pack(anchor="w", pady=(0, 5))

        frame_list = Frame(self.list_container, bg=COLOR_BG)
        frame_list.pack(fill="both", expand=True)

        self.scrollbar = Scrollbar(frame_list)
        self.scrollbar.pack(side="right", fill="y")

        self.listbox = Listbox(
            frame_list,
            bg=COLOR_CARD,
            fg=COLOR_TEXT,
            selectbackground=COLOR_PRIMARY,
            selectforeground="white",
            font=("Consolas", 10),
            relief="flat",
            highlightthickness=0,
            yscrollcommand=self.scrollbar.set,
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.listbox.yview)

        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.listbox.bind("<Double-Button-1>", self.on_listbox_double_click)

        frame_bottom = Frame(self.list_container, bg=COLOR_BG)
        frame_bottom.pack(fill="x", pady=(10, 0))

        self.btn_delete = Button(
            frame_bottom,
            text="🗑️ Hapus Jadwal",
            command=self.delete_schedule,
            bg=COLOR_DELETE,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=6,
        )
        self.btn_delete.pack(side="left")
        make_hoverable(self.btn_delete, COLOR_DELETE, "#991B1B")

        self.btn_stop = Button(
            frame_bottom,
            text="⏹️ Stop Audio",
            command=self.stop_audio,
            bg=COLOR_STOP,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=6,
        )
        self.btn_stop.pack(side="right")
        make_hoverable(self.btn_stop, COLOR_STOP, "#374151")

        self.refresh_listbox()
    def on_window_resize(self, event):
        """Mendeteksi perubahan ukuran jendela & mengubah layout secara dinamis."""
        # Pastikan event resize berasal dari window utama, bukan widget anak
        if event.widget != self.root:
            return

        width = event.width

        # Jika lebar window >= 880px -> Mode Horizontal (Samping-sampingan)
        if width >= 880 and self.current_layout != "horizontal":
            self.current_layout = "horizontal"
            
            # Lepas susunan lama
            self.card_input.pack_forget()
            self.list_container.pack_forget()

            # Pasang susunan baru: Form di Kiri, List di Kanan
            self.card_input.pack(side="left", fill="y", anchor="n", padx=(0, 10))
            self.list_container.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Jika lebar window < 880px -> Mode Vertical (Menumpuk ke Bawah)
        elif width < 880 and self.current_layout != "vertical":
            self.current_layout = "vertical"

            # Lepas susunan lama
            self.card_input.pack_forget()
            self.list_container.pack_forget()

            # Pasang susunan baru: Form di Atas, List di Bawah
            self.card_input.pack(side="top", fill="x", pady=(0, 10))
            self.list_container.pack(side="top", fill="both", expand=True)

    # === UPDATE REALTIME CLOCK & PLAYBACK DETECTOR ===
    def update_realtime_clock(self):
        now_str = datetime.now().strftime("%H:%M:%S")
        self.lbl_clock.config(text=now_str)
        self.root.after(1000, self.update_realtime_clock)

    def check_playback_status(self):
        """Memeriksa apakah audio sedang berputar untuk memperbarui label status secara dinamis."""
        if not pygame.mixer.music.get_busy() and "Memutar" in self.lbl_status.cget("text"):
            self.lbl_status.config(
                text="● Memantau jadwal pemutaran...", fg="#10B981"
            )
        self.root.after(1000, self.check_playback_status)

    def change_volume(self, val):
        volume_level = float(val) / 100.0
        pygame.mixer.music.set_volume(volume_level)

    # === LOGIKA HARI ===
    def toggle_everyday(self):
        is_everyday = self.var_everyday.get()
        for day in DAYS_LIST:
            self.day_vars[day].set(is_everyday)

    def on_day_toggle(self):
        all_checked = all(self.day_vars[day].get() for day in DAYS_LIST)
        self.var_everyday.set(all_checked)

    def get_selected_days(self):
        return [day for day in DAYS_LIST if self.day_vars[day].get()]

    def set_selected_days(self, days_list):
        for day in DAYS_LIST:
            self.day_vars[day].set(day in days_list)
        self.on_day_toggle()

    def get_formatted_time(self):
        h_str = self.combo_hour.get().strip()
        m_str = self.combo_minute.get().strip()

        if not (h_str.isdigit() and m_str.isdigit()):
            return None

        # Deklarasi variabel h_int dan m_int
        h_int = int(h_str)
        m_int = int(m_str)

        if not (0 <= h_int <= 23 and 0 <= m_int <= 59):
            return None

        return f"{h_int:02d}:{m_int:02d}"

    def browse_media(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("All Supported Media", "*.mp3;*.wav;*.ogg;*.mp4;*.mov;*.avi;*.mkv;*.webm;*.flv"),
                ("Audio Files (*.mp3, *.wav, *.ogg)", "*.mp3;*.wav;*.ogg"),
                ("Video Files (*.mp4, *.mov, *.avi, *.mkv)", "*.mp4;*.mov;*.avi;*.mkv;*.webm;*.flv"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.temp_file_path = file_path
            self.lbl_selected_file.config(
                text=os.path.basename(file_path), fg="#60A5FA"
            )

    def preview_media(self):
        """Memutar audio yang sedang dipilih di form sebagai tes/preview."""
        if not self.temp_file_path:
            messagebox.showwarning(
                "File Kosong", "Pilih file Audio atau Video terlebih dahulu untuk dites!"
            )
            return

        processed_file = self.ensure_mp3_format(self.temp_file_path)
        if processed_file:
            self.play_audio("TES PREVIEW", processed_file)

    def ensure_mp3_format(self, original_path):
        ext = os.path.splitext(original_path)[1].lower()

        # Format audio yang langsung bisa dimainkan pygame
        if ext in [".mp3", ".wav", ".ogg"]:
            return original_path

        base_name = os.path.splitext(
            os.path.basename(original_path)
        )[0]

        converted_mp3_path = os.path.join(
            CACHE_DIR,
            f"{base_name}.mp3"
        )

        # Kalau sudah pernah dikonversi
        if (
            os.path.exists(converted_mp3_path)
            and os.path.getsize(converted_mp3_path) > 0
        ):
            return converted_mp3_path

        # Pastikan FFmpeg tersedia
        if not FFMPEG_AVAILABLE or not FFMPEG_EXE:
            messagebox.showerror(
                "FFmpeg Tidak Ditemukan",
                "FFmpeg tidak ditemukan di dalam aplikasi.\n\n"
                "Pastikan aplikasi dibuild menggunakan file .spec "
                "yang benar."
            )
            return None

        try:
            self.lbl_status.config(
                text=f"⚙️ Mengonversi audio dari "
                    f"{os.path.basename(original_path)}...",
                fg="#F59E0B"
            )

            self.root.update_idletasks()

            import subprocess

            command = [
                FFMPEG_EXE,
                "-y",
                "-i",
                original_path,
                "-vn",
                "-acodec",
                "libmp3lame",
                "-q:a",
                "2",
                converted_mp3_path
            ]

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
                if sys.platform == "win32"
                else 0
            )

            if result.returncode != 0:
                raise RuntimeError(
                    result.stderr[-3000:]
                )

            if (
                os.path.exists(converted_mp3_path)
                and os.path.getsize(converted_mp3_path) > 0
            ):
                return converted_mp3_path

            raise RuntimeError(
                "File MP3 hasil konversi tidak terbentuk."
            )

        except Exception as e:
            messagebox.showerror(
                "Detail Error Konversi",
                f"Gagal mengonversi "
                f"'{os.path.basename(original_path)}'.\n\n"
                f"Detail Error:\n{e}"
            )

            return None

    def add_schedule(self):
        time_str = self.get_formatted_time()
        selected_days = self.get_selected_days()

        if not time_str:
            messagebox.showerror(
                "Jam Tidak Valid",
                "Pilih/ketik jam (00-23) dan menit (00-59) dengan benar!",
            )
            return

        if not selected_days:
            messagebox.showwarning(
                "Hari Kosong", "Pilih minimal satu hari pemutaran!"
            )
            return

        if not self.temp_file_path:
            messagebox.showwarning(
                "File Kosong", "Pilih file Audio atau Video terlebih dahulu!"
            )
            return

        if time_str in self.schedule_data:
            messagebox.showwarning(
                "Jam Sudah Ada",
                f"Jam {time_str} sudah ada! Gunakan 'Update Jadwal' untuk mengubahnya.",
            )
            return

        processed_file = self.ensure_mp3_format(self.temp_file_path)

        if not processed_file:
            return

        self.schedule_data[time_str] = {
            "file": processed_file,
            "original_file": self.temp_file_path,
            "days": selected_days,
        }
        self.save_config()
        self.refresh_listbox()
        self.clear_form()
        messagebox.showinfo("Berhasil", f"Jadwal jam {time_str} ditambahkan.")

    def update_schedule(self):
        time_str = self.get_formatted_time()
        selected_days = self.get_selected_days()

        if not time_str:
            messagebox.showerror(
                "Jam Tidak Valid",
                "Pilih/ketik jam (00-23) dan menit (00-59) dengan benar!",
            )
            return

        if time_str not in self.schedule_data:
            messagebox.showwarning(
                "Tidak Ditemukan",
                f"Jam {time_str} belum ada di daftar. Gunakan 'Tambah Baru'.",
            )
            return

        if not selected_days:
            messagebox.showwarning(
                "Hari Kosong", "Pilih minimal satu hari pemutaran!"
            )
            return

        current_file = self.schedule_data[time_str].get("file", "")
        if self.temp_file_path:
            processed_file = self.ensure_mp3_format(
                self.temp_file_path
            )

            if not processed_file:
                return

            orig_file = self.temp_file_path

        else:
            processed_file = current_file
            orig_file = self.schedule_data[time_str].get(
                "original_file",
                current_file
            )

        self.schedule_data[time_str] = {
            "file": processed_file,
            "original_file": orig_file,
            "days": selected_days,
        }

        self.save_config()
        self.refresh_listbox()
        self.clear_form()
        messagebox.showinfo(
            "Berhasil", f"Jadwal jam {time_str} berhasil diperbarui!"
        )

    def delete_schedule(self):
        try:
            selected_index = self.listbox.curselection()[0]
            selected_text = self.listbox.get(selected_index)
            time_key = selected_text.split(" | ")[0].strip()

            if time_key in self.schedule_data:
                del self.schedule_data[time_key]
                self.save_config()
                self.refresh_listbox()
                self.clear_form()
        except IndexError:
            messagebox.showwarning(
                "Peringatan", "Pilih jadwal yang ingin dihapus dari daftar!"
            )

    def on_listbox_select(self, event):
        try:
            selected_index = self.listbox.curselection()[0]
            selected_text = self.listbox.get(selected_index)
            time_key = selected_text.split(" | ")[0].strip()

            if time_key in self.schedule_data:
                h, m = time_key.split(":")
                self.combo_hour.set(h)
                self.combo_minute.set(m)

                item = self.schedule_data[time_key]
                self.temp_file_path = item.get("original_file", item.get("file", ""))
                self.lbl_selected_file.config(
                    text=os.path.basename(self.temp_file_path), fg="#60A5FA"
                )

                days = item.get("days", DAYS_LIST)
                self.set_selected_days(days)
        except IndexError:
            pass

    def on_listbox_double_click(self, event):
        """Putar audio saat item di listbox diklik 2 kali."""
        try:
            selected_index = self.listbox.curselection()[0]
            selected_text = self.listbox.get(selected_index)
            time_key = selected_text.split(" | ")[0].strip()

            if time_key in self.schedule_data:
                audio_file = self.schedule_data[time_key].get("file", "")
                if audio_file:
                    self.play_audio(time_key, audio_file)
        except IndexError:
            pass

    def clear_form(self):
        self.combo_hour.set("08")
        self.combo_minute.set("00")
        self.temp_file_path = ""
        self.lbl_selected_file.config(
            text="Belum ada file dipilih", fg=COLOR_MUTED
        )
        self.set_selected_days(DAYS_LIST)
        self.listbox.selection_clear(0, "end")

    def refresh_listbox(self):
        self.listbox.delete(0, "end")
        sorted_keys = sorted(self.schedule_data.keys())
        for k in sorted_keys:
            item = self.schedule_data[k]
            file_path = item.get("original_file", item.get("file", ""))
            song_name = os.path.basename(file_path)
            days = item.get("days", [])

            if len(days) == 7:
                days_str = "Setiap Hari"
            elif len(days) > 0:
                days_str = ", ".join([d[:3] for d in days])
            else:
                days_str = "Tidak Ada Hari"

            self.listbox.insert("end", f" {k}  |  [{days_str}]  |  {song_name}")

    def save_config(self): 
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.schedule_data, f, indent=4)
        except Exception as e:
            print(f"Gagal menyimpan config: {e}")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    converted_data = {}
                    for time_key, val in data.items():
                        if isinstance(val, str):
                            converted_data[time_key] = {
                                "file": val,
                                "original_file": val,
                                "days": DAYS_LIST.copy(),
                            }
                        else:
                            converted_data[time_key] = val
                    self.schedule_data = converted_data
            except Exception:
                self.schedule_data = {}
        else:
            self.schedule_data = {}

    def play_audio(self, time_key, file_path):
        if not file_path or not os.path.exists(file_path):
            self.lbl_status.config(
                text=f"❌ File audio jam {time_key} tidak ditemukan!", fg="#EF4444"
            )
            return

        if os.path.getsize(file_path) == 0:
            self.lbl_status.config(
                text=f"❌ File audio jam {time_key} kosong / korup!", fg="#EF4444"
            )
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".mp3", ".wav", ".ogg"]:
            self.lbl_status.config(
                text=f"❌ Format {ext} tidak didukung langsung oleh pemutar audio!", fg="#EF4444"
            )
            return

        song_name = os.path.basename(file_path)
        self.lbl_status.config(
            text=f"▶ Memutar [{time_key}]: {song_name}", fg="#3B82F6"
        )

        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()

            # MUTE semua aplikasi lain (Spotify, Browser, Player lokal)
            if not self.external_media_paused:
                set_other_apps_mute(True)
                self.external_media_paused = True

            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            # Thread pantau sampai selesai
            threading.Thread(target=self._wait_and_resume_external_media, daemon=True).start()

        except Exception as e:
            print(f"Error play audio: {e}")
            self.lbl_status.config(
                text=f"❌ Gagal memutar audio: {e}", fg="#EF4444"
            )
            # Jika error, kembalikan suara aplikasi lain
            if self.external_media_paused:
                set_other_apps_mute(False)
                self.external_media_paused = False

    def _wait_and_resume_external_media(self):
        """Menunggu hingga audio BPSound selesai, lalu unmute aplikasi lain."""
        time.sleep(0.5)

        while pygame.mixer.music.get_busy() and self.is_running:
            time.sleep(0.5)

        # UNMUTE semua aplikasi lain setelah alarm BPSound selesai
        if self.external_media_paused:
            set_other_apps_mute(False)
            self.external_media_paused = False

    def stop_audio(self):
        pygame.mixer.music.stop()
        self.lbl_status.config(
            text="● Memantau jadwal pemutaran...", fg="#10B981"
        )

        # Jika di-stop manual, UNMUTE aplikasi lain
        if self.external_media_paused:
            set_other_apps_mute(False)
            self.external_media_paused = False

    def check_schedule_loop(self):
        while self.is_running:
            now = datetime.now()
            current_hm = now.strftime("%H:%M")
            current_day_name = DAYS_LIST[now.weekday()]

            if current_hm in self.schedule_data:
                item = self.schedule_data[current_hm]
                allowed_days = item.get("days", [])
                audio_file = item.get("file", "")

                if current_day_name in allowed_days:
                    trigger_key = f"{current_hm}_{now.strftime('%Y-%m-%d')}"
                    if self.last_played_hour != trigger_key:
                        if audio_file:
                            self.root.after(0, self.play_audio, current_hm, audio_file)
                            self.last_played_hour = trigger_key

            time.sleep(5)


if __name__ == "__main__":
    root = Tk()
    app = BPSoundApp(root)
    root.mainloop()