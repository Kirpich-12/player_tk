import tkinter as tk
from tkinter import filedialog
import os
import pygame

# инициализация pygame для музыки
pygame.mixer.init()

# главное окно
root = tk.Tk()
root.title("плеер")

# размеры окна
screen_w = root.winfo_screenwidth()
win_w = int(screen_w * 0.25)
win_h = int(win_w * (10/8))
root.geometry(f"{win_w}x{win_h}")
root.resizable(False, False)

# центрирование элементов
main_frame = tk.Frame(root)
main_frame.pack(expand=True)

# список треков
playlist = []

# текущий трек
current_index = -1

# плейлист окно
playlist_win = None

# окно настроек
settings_win = None

# функция открыть/закрыть плейлист
def toggle_playlist():
    global playlist_win
    if playlist_win and tk.Toplevel.winfo_exists(playlist_win):
        playlist_win.destroy()
        playlist_win = None
    else:
        playlist_win = tk.Toplevel(root)
        playlist_win.title("Плейлист")
        playlist_win.geometry(f"{150}x{win_h}+{root.winfo_x()-150}+{root.winfo_y()}")
        playlist_box = tk.Listbox(playlist_win)
        playlist_box.pack(fill="both", expand=True)
        for track in playlist:
            playlist_box.insert("end", os.path.basename(track))
        def on_select(evt):
            global current_index
            w = evt.widget
            idx = w.curselection()[0]
            current_index = idx
            play_track()
        playlist_box.bind("<<ListboxSelect>>", on_select)

# функция выбрать файлы вручную
def add_files():
    files = filedialog.askopenfilenames(filetypes=[("MP3 files","*.mp3")])
    for f in files:
        playlist.append(f)
    toggle_playlist()

# переменные для имени исполнителя и названия
artist_name = tk.StringVar()
song_title = tk.StringVar()

# функция играть трек
track_length = 0
def play_track():
    global current_index, track_length
    if current_index < 0 or current_index >= len(playlist):
        return
    track = playlist[current_index]
    pygame.mixer.music.load(track)
    pygame.mixer.music.play()
    # получить длину трека
    track_length = pygame.mixer.Sound(track).get_length()
    time_slider.config(to=track_length)
    time_slider.set(0)
    # имя файла
    fname = os.path.basename(track)
    if "-" in fname:
        parts = fname.rsplit("-", 1)
        artist_name.set(parts[0].strip())
        song_title.set(parts[1].replace(".mp3","").strip())
    else:
        artist_name.set("")
        song_title.set(fname.replace(".mp3",""))

# назад
def prev_track():
    global current_index
    if current_index > 0:
        current_index -= 1
        play_track()

# вперед
def next_track():
    global current_index
    if current_index < len(playlist)-1:
        current_index += 1
        play_track()

# пауза/старт
paused = False
def toggle_play():
    global paused
    if pygame.mixer.music.get_busy():
        if paused:
            pygame.mixer.music.unpause()
            paused = False
        else:
            pygame.mixer.music.pause()
            paused = True
    else:
        play_track()

# закрепить окно
def toggle_topmost():
    root.attributes("-topmost", not root.attributes("-topmost"))

# настройки открыть/закрыть
def toggle_settings():
    global settings_win
    if settings_win and tk.Toplevel.winfo_exists(settings_win):
        settings_win.destroy()
        settings_win = None
    else:
        settings_win = tk.Toplevel(root)
        settings_win.title("Настройки")
        settings_win.geometry(f"{win_w}x150+{root.winfo_x()}+{root.winfo_y()-200}")
        tk.Label(settings_win, text="Прозрачность").pack()
        slider = tk.Scale(settings_win, from_=50, to=100, orient="horizontal")
        slider.set(100)
        slider.pack(fill="x")
        def update_alpha(val):
            alpha = int(val)/100
            root.attributes("-alpha", alpha)
            if playlist_win and tk.Toplevel.winfo_exists(playlist_win):
                playlist_win.attributes("-alpha", alpha)
            settings_win.attributes("-alpha", alpha)
        slider.config(command=update_alpha)

# квадрат обложки
cover = tk.Canvas(main_frame, width=150, height=150, bg="gray")
cover.pack(pady=10)

# имя исполнителя и название трека
tk.Label(main_frame, textvariable=artist_name, font=("Arial", 12, "bold")).pack(pady=2)
tk.Label(main_frame, textvariable=song_title, font=("Arial", 11)).pack(pady=2)

# кнопки
btn_frame = tk.Frame(main_frame)
btn_frame.pack(pady=10)

def make_round_button(parent, text, cmd, size=50):
    c = tk.Canvas(parent, width=size, height=size, highlightthickness=0)
    c.create_oval(2,2,size-2,size-2, fill="lightblue")
    c.create_text(size//2, size//2, text=text)
    c.bind("<Button-1>", lambda e: cmd())
    c.pack(side="left", padx=10)
    return c

# кнопка плейлист
make_round_button(btn_frame, "PL", toggle_playlist)

# назад
make_round_button(btn_frame, "<<", prev_track)

# пауза/старт (большая)
make_round_button(btn_frame, "▶/⏸", toggle_play, size=70)

# вперед
make_round_button(btn_frame, ">>", next_track)

# закрепить
make_round_button(btn_frame, "TOP", toggle_topmost)

# кнопка настроек (шестерёнка)
gear_btn = tk.Button(root, text="⚙", command=toggle_settings)
gear_btn.place(x=443, y=10)

# === Полоса времени ===
time_frame = tk.Frame(main_frame)
time_frame.pack(fill="x", padx=20, pady=10)

time_slider = tk.Scale(time_frame, from_=0, to=100, orient="horizontal", resolution=0.01, showvalue=0)
time_slider.pack(fill="x")

def update_time_slider():
    if pygame.mixer.music.get_busy() and not paused:
        pos_ms = pygame.mixer.music.get_pos()
        if pos_ms >= 0:
            pos_sec = pos_ms / 1000.0
            time_slider.set(pos_sec)
    root.after(10, update_time_slider)

def seek_track(val):
    try:
        pos = float(val)
        pygame.mixer.music.play(start=pos)
    except Exception as e:
        print("Seek error:", e)

time_slider.config(command=seek_track)
update_time_slider()

# === Автозагрузка музыки из папки songs ===
songs_dir = os.path.join(os.getcwd(), "songs")
if os.path.exists(songs_dir):
    for f in os.listdir(songs_dir):
        if f.lower().endswith(".mp3"):
            playlist.append(os.path.join(songs_dir, f))
if playlist:
    current_index = 0
    play_track()

root.mainloop()
