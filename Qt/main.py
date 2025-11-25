import sys
import os
import pygame
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


pygame.mixer.init()


#размеры окна
def get_window_size():
    screen = QApplication.primaryScreen().geometry()
    w = int(screen.width() * 0.25)
    h = int(w * (10/8))
    return w, h


class PlayerWindow(QWidget):
    def __init__(self):
        super().__init__()

        w, h = get_window_size()
        self.setFixedSize(w, h)
        self.setWindowTitle("Студенческий плеер")

        self.playlist_window = None
        self.settings_window = None
        self.global_opacity = 1.0
        self.is_paused = False

        # загружаем треки
        self.playlist_files = self.load_song_folder()
        self.current_index = 0 if self.playlist_files else -1

        #ОБЛОЖКА
        self.cover = QLabel()
        self.cover.setFixedSize(200, 200)
        self.cover.setStyleSheet("background:#444; border-radius:10px;")
        self.cover.setAlignment(Qt.AlignCenter)

        #ТЕКСТЫ
        self.artist_label = QLabel("")
        self.artist_label.setAlignment(Qt.AlignCenter)
        self.artist_label.setStyleSheet("font-size:14px; color:#ccc;")

        self.title_label = QLabel("Нет трека")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size:18px;")

        # ПОЛОСА ПРОИГРЫВАНИЯ
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.sliderPressed.connect(self.user_seek)
        self.slider.sliderReleased.connect(self.user_release)
        self.slider_is_moving = False

        #КНОПКИ
        self.btn_open_playlist = self.make_btn("📂")
        self.btn_prev = self.make_btn("⏮")
        self.btn_play = self.make_btn("▶")
        self.btn_play.setFixedSize(70, 70)
        self.btn_next = self.make_btn("⏭")
        self.btn_pin = self.make_btn("📌")

        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(30, 30)

        self.btn_open_playlist.clicked.connect(self.toggle_playlist)
        self.btn_prev.clicked.connect(self.play_prev)
        self.btn_play.clicked.connect(self.play_pause)
        self.btn_next.clicked.connect(self.play_next)
        self.btn_pin.clicked.connect(self.toggle_pin)
        self.btn_settings.clicked.connect(self.open_settings)

        #РАЗМЕТКА
        top = QHBoxLayout()
        top.addWidget(self.btn_settings)
        top.addStretch()

        ctrl = QHBoxLayout()
        ctrl.addStretch()
        for b in [self.btn_open_playlist, self.btn_prev, self.btn_play, self.btn_next, self.btn_pin]:
            ctrl.addWidget(b)
        ctrl.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addStretch()
        layout.addWidget(self.cover, alignment=Qt.AlignCenter)
        layout.addWidget(self.artist_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.slider)
        layout.addStretch()
        layout.addLayout(ctrl)
        self.setLayout(layout)

        # запуск первой песни
        if self.current_index != -1:
            self.load_track(self.playlist_files[self.current_index])

        # таймер для обновления слайдера
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_slider)
        self.timer.start(300)

    #ВСПОМОГАТЕЛЬНЫЕ

    def make_btn(self, text):
        btn = QPushButton(text)
        btn.setFixedSize(50, 50)
        btn.setStyleSheet("""
            QPushButton {
                background:#666;
                border-radius:25px;
                font-size:20px;
            }
            QPushButton:hover { background:#888; }
        """)
        return btn

    def load_song_folder(self):
        songs = []
        folder = "songs"
        if not os.path.exists(folder):
            os.mkdir(folder)
        for f in os.listdir(folder):
            if f.lower().endswith((".mp3", ".wav", ".ogg")):
                songs.append(os.path.join(folder, f))
        return songs

    #ПАРСИНГ НАЗВАНИЙ (Artist - Title.mp3)
    def parse_name(self, filename):
        base = os.path.basename(filename)
        name = os.path.splitext(base)[0]

        if " - " in name:
            artist, title = name.split(" - ", 1)
        else:
            artist = "Неизвестный исполнитель"
            title = name

        return artist, title

    #ПРОИГРЫВАНИЕ

    def load_track(self, path):
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()

        artist, title = self.parse_name(path)

        self.artist_label.setText(artist)
        self.title_label.setText(title)
        self.btn_play.setText("⏸")

        # длительность узнаём через pygame
        try:
            self.sound = pygame.mixer.Sound(path)
            self.duration = self.sound.get_length()
        except:
            self.duration = 1

    def play_pause(self):
        if not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.btn_play.setText("▶")
        else:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.btn_play.setText("⏸")
    
    def play_prev(self):
        if not self.playlist_files:
            return
        self.current_index = (self.current_index - 1) % len(self.playlist_files)
        self.load_track(self.playlist_files[self.current_index])

    def play_next(self):
        if not self.playlist_files:
            return
        self.current_index = (self.current_index + 1) % len(self.playlist_files)
        self.load_track(self.playlist_files[self.current_index])

    #ОБНОВЛЕНИЕ ПОЛОСКИ ВРЕМЕНИ
    def update_slider(self):
        if not pygame.mixer.music.get_busy() and not self.is_paused:
            self.play_next()
            return

        if self.slider_is_moving:
            return

        pos = pygame.mixer.music.get_pos() / 1000  # миллисекунды → секунды
        if pos < 0:
            pos = 0

        if self.duration > 0:
            val = int((pos / self.duration) * 1000)
            self.slider.setValue(val)

    # пользователь начал двигать
    def user_seek(self):
        self.slider_is_moving = True

    # пользователь отпустил
    def user_release(self):
        value = self.slider.value()
        if self.duration > 0:
            new_time = (value / 1000) * self.duration
            pygame.mixer.music.play(start=new_time)
        self.slider_is_moving = False

    #ОКНА 

    def toggle_pin(self):
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(Qt.Window)
        else:
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.show()

    def toggle_playlist(self):
        if self.playlist_window and self.playlist_window.isVisible():
            self.playlist_window.close()
            return

        self.playlist_window = PlaylistWindow(self)
        self.playlist_window.setWindowOpacity(self.global_opacity)
        self.playlist_window.show()

    def open_settings(self):
        if self.settings_window and self.settings_window.isVisible():
            self.settings_window.close()
            return
        self.settings_window = SettingsWindow(self)
        self.settings_window.setWindowOpacity(self.global_opacity)
        self.settings_window.show()

    def update_opacity(self, val):
        self.global_opacity = val
        self.setWindowOpacity(val)
        if self.playlist_window:
            self.playlist_window.setWindowOpacity(val)
        if self.settings_window:
            self.settings_window.setWindowOpacity(val)


#ПЛЕЙЛИСТ

class PlaylistWindow(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        w, h = get_window_size()
        self.setFixedSize(int(w * 0.9), h)

        self.move(main.x() - self.width(), main.y())
        self.setWindowTitle("Плейлист")

        self.list = QListWidget()
        for f in self.main.playlist_files:
            self.list.addItem(f)

        self.list.itemDoubleClicked.connect(self.play_file)

        layout = QVBoxLayout()
        layout.addWidget(self.list)
        self.setLayout(layout)

    def play_file(self, item):
        path = item.text()
        self.main.current_index = self.main.playlist_files.index(path)
        self.main.load_track(path)


#ОКНО НАСТРОЕК

class SettingsWindow(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        w, h = get_window_size()
        self.setFixedSize(w, 120)
        self.move(main.x(), main.y() - 130)
        self.setWindowTitle("Настройки")

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(30)
        slider.setMaximum(100)
        slider.setValue(int(main.global_opacity * 100))
        slider.valueChanged.connect(self.change_opacity)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Прозрачность всех окон"))
        layout.addWidget(slider)
        self.setLayout(layout)

    def change_opacity(self, val):
        self.main.update_opacity(val / 100)


#ЗАПУСК

app = QApplication(sys.argv)
win = PlayerWindow()
win.show()
sys.exit(app.exec_())
