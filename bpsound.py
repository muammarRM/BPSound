import json
import os
import threading
import time
from datetime import datetime
from tkinter import (
    Button,
    Frame,
    Label,
    Listbox,
    Scrollbar,
    Tk,
    filedialog,
    messagebox,
    ttk,
)
import pygame

# Inisialisasi Audio Engine
pygame.mixer.init()

CONFIG_FILE = "config_bpsound.json"

# === PALET WARNA BPS SOUND (DARK THEME) ===
COLOR_BG = "#181818"
COLOR_CARD = "#242424"
COLOR_PRIMARY = "#005BB5"
COLOR_TEXT = "#FFFFFF"
COLOR_MUTED = "#9E9E9E"

COLOR_ADD = "#007ACC"
COLOR_UPDATE = "#D97706"
COLOR_DELETE = "#B91C1C"
COLOR_STOP = "#4B5563"


class BPSoundApp:

    def __init__(self, root):
        self.root = root
        self.root.title("BPSound - BPS Automated Hourly Audio Player")
        self.root.geometry("540x650")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        self.schedule_data = {}
        self.temp_file_path = ""
        self.last_played_hour = None
        self.is_running = True

        self.load_config()
        self.setup_ui()

        # Thread Background untuk Cek Jam
        self.checker_thread = threading.Thread(
            target=self.check_schedule_loop, daemon=True
        )
        self.checker_thread.start()

    def setup_ui(self):
        # Styling TTK Combobox untuk Dark Mode
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "TCombobox",
            fieldbackground="#333333",
            background="#444444",
            foreground="white",
            bordercolor=COLOR_CARD,
        )

        # === HEADER SECTION ===
        frame_header = Frame(self.root, bg=COLOR_BG)
        frame_header.pack(fill="x", padx=20, pady=(15, 5))

        Label(
            frame_header,
            text="BPSound Player",
            font=("Segoe UI", 18, "bold"),
            fg=COLOR_PRIMARY,
            bg=COLOR_BG,
        ).pack(anchor="w")

        self.lbl_status = Label(
            frame_header,
            text="● Memantau jadwal pemutaran...",
            fg="#10B981",
            bg=COLOR_BG,
            font=("Segoe UI", 10, "bold"),
        )
        self.lbl_status.pack(anchor="w", pady=(2, 0))

        # === CARD FORM INPUT ===
        card_input = Frame(self.root, bg=COLOR_CARD, padx=15, pady=15)
        card_input.pack(fill="x", padx=20, pady=10)

        Label(
            card_input,
            text="Kelola Jadwal & Lagu",
            font=("Segoe UI", 11, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD,
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

        # Label Jam & Menit
        Label(
            card_input,
            text="Pilih Jam:",
            font=("Segoe UI", 10),
            fg=COLOR_TEXT,
            bg=COLOR_CARD,
        ).grid(row=1, column=0, sticky="w")

        # Container khusus Pemilih Waktu (Jam : Menit)
        time_frame = Frame(card_input, bg=COLOR_CARD)
        time_frame.grid(row=1, column=1, sticky="w", padx=5)

        # Dropdown Jam (00 - 23)
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

        # Dropdown Menit (00 - 59)
        minutes_list = [f"{i:02d}" for i in range(60)]
        self.combo_minute = ttk.Combobox(
            time_frame, values=minutes_list, width=3, state="normal"
        )
        self.combo_minute.set("00")
        self.combo_minute.pack(side="left")

        # File Chooser Button
        self.btn_select_file = Button(
            card_input,
            text="🎵 Pilih MP3",
            command=self.browse_mp3,
            bg="#374151",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=10,
        )
        self.btn_select_file.grid(row=1, column=2, sticky="e", padx=5)

        self.lbl_selected_file = Label(
            card_input,
            text="Belum ada lagu dipilih",
            fg=COLOR_MUTED,
            bg=COLOR_CARD,
            font=("Segoe UI", 9, "italic"),
            anchor="w",
        )
        self.lbl_selected_file.grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(8, 10)
        )

        # Tombol Aksi Form (Tambah & Update)
        frame_form_btns = Frame(card_input, bg=COLOR_CARD)
        frame_form_btns.grid(row=3, column=0, columnspan=3, sticky="we")

        self.btn_add = Button(
            frame_form_btns,
            text="➕ Tambah Baru",
            command=self.add_schedule,
            bg=COLOR_ADD,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            pady=5,
        )
        self.btn_add.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_update = Button(
            frame_form_btns,
            text="✏️ Update / Ganti Lagu",
            command=self.update_schedule,
            bg=COLOR_UPDATE,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            pady=5,
        )
        self.btn_update.pack(side="right", expand=True, fill="x", padx=(5, 0))

        # === LIST DAFTAR JADWAL ===
        Label(
            self.root,
            text="Daftar Jam Terpasang:",
            font=("Segoe UI", 11, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_BG,
        ).pack(anchor="w", padx=20, pady=(10, 5))

        frame_list = Frame(self.root, bg=COLOR_BG)
        frame_list.pack(fill="both", expand=True, padx=20)

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

        # Event ketika item listbox diklik (auto fill form)
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)

        # === BOTTOM BUTTONS (DELETE & STOP) ===
        frame_bottom = Frame(self.root, bg=COLOR_BG)
        frame_bottom.pack(fill="x", padx=20, pady=15)

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

        self.btn_stop = Button(
            frame_bottom,
            text="⏹️ Stop Audio Saat Ini",
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

        self.refresh_listbox()

    # === LOGIKA & FUNGSI ===
    def get_formatted_time(self):
        h = self.combo_hour.get().strip().zfill(2)
        m = self.combo_minute.get().strip().zfill(2)

        # Validasi batas angka
        if not (h.isdigit() and m.isdigit()):
            return None
        if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            return None

        return f"{h}:{m}"

    def browse_mp3(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3")]
        )
        if file_path:
            self.temp_file_path = file_path
            self.lbl_selected_file.config(
                text=os.path.basename(file_path), fg="#60A5FA"
            )

    def add_schedule(self):
        time_str = self.get_formatted_time()

        if not time_str:
            messagebox.showerror(
                "Jam Tidak Valid",
                "Pilih/ketik jam (00-23) dan menit (00-59) dengan benar!",
            )
            return

        if not self.temp_file_path:
            messagebox.showwarning(
                "Lagu Kosong", "Pilih file MP3 terlebih dahulu!"
            )
            return

        if time_str in self.schedule_data:
            messagebox.showwarning(
                "Jam Sudah Ada",
                f"Jam {time_str} sudah ada! Gunakan 'Update / Ganti Lagu' untuk mengubahnya.",
            )
            return

        self.schedule_data[time_str] = self.temp_file_path
        self.save_config()
        self.refresh_listbox()
        self.clear_form()
        messagebox.showinfo("Berhasil", f"Jadwal jam {time_str} ditambahkan.")

    def update_schedule(self):
        time_str = self.get_formatted_time()

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

        if self.temp_file_path:
            self.schedule_data[time_str] = self.temp_file_path

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
                self.temp_file_path = self.schedule_data[time_key]
                self.lbl_selected_file.config(
                    text=os.path.basename(self.temp_file_path), fg="#60A5FA"
                )
        except IndexError:
            pass

    def clear_form(self):
        self.combo_hour.set("08")
        self.combo_minute.set("00")
        self.temp_file_path = ""
        self.lbl_selected_file.config(
            text="Belum ada lagu dipilih", fg=COLOR_MUTED
        )

    def refresh_listbox(self):
        self.listbox.delete(0, "end")
        sorted_keys = sorted(self.schedule_data.keys())
        for k in sorted_keys:
            song_name = os.path.basename(self.schedule_data[k])
            self.listbox.insert("end", f" {k}  |  {song_name}")

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
                    self.schedule_data = json.load(f)
            except Exception:
                self.schedule_data = {}
        else:
            self.schedule_data = {}

    def play_audio(self, time_key, file_path):
        if not os.path.exists(file_path):
            self.lbl_status.config(
                text=f"❌ File lagu jam {time_key} hilang!", fg="#EF4444"
            )
            return

        song_name = os.path.basename(file_path)
        self.lbl_status.config(
            text=f"▶ Memutar [{time_key}]: {song_name}", fg="#3B82F6"
        )

        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error play audio: {e}")

    def stop_audio(self):
        pygame.mixer.music.stop()
        self.lbl_status.config(
            text="● Memantau jadwal pemutaran...", fg="#10B981"
        )

    def check_schedule_loop(self):
        while self.is_running:
            now = datetime.now()
            current_hm = now.strftime("%H:%M")

            if current_hm in self.schedule_data:
                if self.last_played_hour != current_hm:
                    mp3_file = self.schedule_data[current_hm]
                    if mp3_file:
                        self.play_audio(current_hm, mp3_file)
                        self.last_played_hour = current_hm

            if current_hm not in self.schedule_data:
                self.last_played_hour = None

            time.sleep(5)


if __name__ == "__main__":
    root = Tk()
    app = BPSoundApp(root)
    root.mainloop()