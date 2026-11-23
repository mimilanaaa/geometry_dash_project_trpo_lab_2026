import os
import sys
import subprocess
import threading
import arcade
from ui import theme
from ui.menu import draw_title

FORMATS = [".mp3", ".wav", ".ogg", ".flac", ".m4a"]
MIN_SECONDS = 30
MAX_SECONDS = 600

DIALOG_CODE = (
    "import tkinter as tk\n"
    "from tkinter import filedialog\n"
    "root = tk.Tk()\n"
    "root.withdraw()\n"
    "root.attributes('-topmost', True)\n"
    "path = filedialog.askopenfilename(title='Выберите трек', "
    "filetypes=[('Аудио', '*.mp3 *.wav *.ogg *.flac *.m4a'), ('Все файлы', '*.*')])\n"
    "print(path)\n"
)


def check_file(path):
    if not os.path.exists(path):
        return "Файл не найден"
    ext = os.path.splitext(path)[1].lower()
    if ext not in FORMATS:
        return "Формат не поддерживается. Нужен MP3, WAV, OGG, FLAC или M4A"
    return ""


def check_duration(seconds):
    if seconds < MIN_SECONDS:
        return "Трек слишком короткий: нужно не меньше 30 секунд"
    if seconds > MAX_SECONDS:
        return "Трек слишком длинный: нужно не больше 10 минут"
    return ""


def format_time(seconds):
    seconds = int(seconds)
    return str(seconds // 60) + ":" + str(seconds % 60).zfill(2)


class Button:
    def __init__(self, text, x, y, width=260, height=56):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains(self, px, py):
        return (self.x - self.width / 2 <= px <= self.x + self.width / 2
                and self.y - self.height / 2 <= py <= self.y + self.height / 2)

    def draw(self, filled=True):
        t = theme.get_theme()
        left = self.x - self.width / 2
        right = self.x + self.width / 2
        bottom = self.y - self.height / 2
        top = self.y + self.height / 2
        if filled:
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, t["accent"])
            text_color = t["background"]
        else:
            arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, t["line"], 3)
            text_color = t["text"]
        arcade.draw_text(self.text, self.x, self.y, text_color, 16, font_name=theme.FONT,
                         bold=True, anchor_x="center", anchor_y="center")


class TrackLoadView(arcade.View):
    def __init__(self, on_ready, on_back=None, analyze=None):
        super().__init__()
        self.on_ready = on_ready
        self.on_back = on_back
        self.analyze = analyze
        self.state = "empty"
        self.path = ""
        self.error = ""
        self.result = None
        self.thread_result = None
        self.thread_error = ""
        self.picked_path = None
        self.dot_timer = 0
        self.choose_button = Button("ВЫБРАТЬ ФАЙЛ", 0, 0)
        self.play_button = Button("ИГРАТЬ", 0, 0)

    def place_buttons(self):
        w = self.window.width
        self.choose_button.x = w / 2 - 150
        self.choose_button.y = 140
        self.play_button.x = w / 2 + 150
        self.play_button.y = 140

    def on_show_view(self):
        self.place_buttons()

    def on_resize(self, width, height):
        self.place_buttons()

    def open_dialog(self):
        def worker():
            try:
                out = subprocess.run([sys.executable, "-c", DIALOG_CODE],
                                     capture_output=True, text=True)
                self.picked_path = out.stdout.strip()
            except Exception:
                self.picked_path = ""
        self.state = "dialog"
        threading.Thread(target=worker, daemon=True).start()

    def set_file(self, path):
        self.path = path
        self.result = None
        self.error = check_file(path)
        if self.error:
            self.state = "error"
            return
        self.start_analysis()

    def start_analysis(self):
        analyze = self.analyze
        if analyze is None:
            try:
                from music.beat_detect import analyze_track
                analyze = analyze_track
            except Exception:
                self.state = "error"
                self.error = "Модуль анализа не запустился. Установите librosa"
                return

        def worker():
            try:
                self.thread_result = analyze(self.path)
            except Exception as e:
                self.thread_error = "Не удалось разобрать трек: " + str(e)

        self.thread_result = None
        self.thread_error = ""
        self.state = "analyzing"
        threading.Thread(target=worker, daemon=True).start()

    def on_update(self, delta_time):
        self.dot_timer += delta_time
        if self.state == "dialog" and self.picked_path is not None:
            path = self.picked_path
            self.picked_path = None
            if path:
                self.set_file(path)
            else:
                self.state = "error" if self.error else ("done" if self.result else "empty")
        if self.state == "analyzing":
            if self.thread_error:
                self.state = "error"
                self.error = self.thread_error
            elif self.thread_result is not None:
                self.error = check_duration(self.thread_result["duration"])
                if self.error:
                    self.state = "error"
                else:
                    self.result = self.thread_result
                    self.state = "done"

    def draw_info_line(self, label, value, y):
        t = theme.get_theme()
        left = self.window.width / 2 - 260
        arcade.draw_text(label, left, y, t["text_soft"], 14, font_name=theme.FONT, bold=True)
        arcade.draw_text(value, left + 220, y, t["text"], 14, font_name=theme.FONT, bold=True)

    def on_draw(self):
        self.clear(theme.get_theme()["background"])
        t = theme.get_theme()
        w = self.window.width
        h = self.window.height
        draw_title(self, "ЗАГРУЗКА ТРЕКА", "MP3, WAV, OGG, FLAC, M4A — от 30 секунд до 10 минут")

        left = w / 2 - 300
        right = w / 2 + 300
        bottom = 200
        top = h - 230
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, t["panel"])
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, t["line"], 2)

        cy = (top + bottom) / 2
        if self.state == "empty":
            arcade.draw_text("Трек не выбран", w / 2, cy, t["text_soft"], 18,
                             font_name=theme.FONT, bold=True, anchor_x="center")
        elif self.state == "dialog":
            arcade.draw_text("Выберите файл в открывшемся окне", w / 2, cy, t["text_soft"], 16,
                             font_name=theme.FONT, bold=True, anchor_x="center")
        elif self.state == "analyzing":
            dots = "." * (int(self.dot_timer * 3) % 4)
            arcade.draw_text("Анализ трека" + dots, w / 2, cy + 20, t["text"], 20,
                             font_name=theme.FONT, bold=True, anchor_x="center")
            arcade.draw_text(os.path.basename(self.path), w / 2, cy - 20, t["text_soft"], 14,
                             font_name=theme.FONT, anchor_x="center")
            bar_left = w / 2 - 150
            pos = (self.dot_timer * 150) % 300
            arcade.draw_lrbt_rectangle_filled(bar_left, bar_left + 300, cy - 60, cy - 52, t["bar_back"])
            arcade.draw_lrbt_rectangle_filled(bar_left + pos, min(bar_left + pos + 60, bar_left + 300),
                                              cy - 60, cy - 52, t["accent"])
        elif self.state == "done":
            r = self.result
            arcade.draw_text(os.path.basename(self.path), w / 2, top - 50, t["text"], 18,
                             font_name=theme.FONT, bold=True, anchor_x="center")
            self.draw_info_line("ТЕМП", str(round(r["bpm"])) + " BPM", cy + 10)
            self.draw_info_line("ДЛИТЕЛЬНОСТЬ", format_time(r["duration"]), cy - 25)
            self.draw_info_line("БИТОВ НАЙДЕНО", str(len(r["beat_times"])), cy - 60)
        elif self.state == "error":
            arcade.draw_text(self.error, w / 2, cy, t["accent"], 15,
                             font_name=theme.FONT, bold=True, anchor_x="center",
                             width=560, multiline=True, align="center")

        self.choose_button.draw(filled=False)
        if self.state == "done":
            self.play_button.draw(filled=True)
        arcade.draw_text("Esc — назад", 24, 24, t["text_soft"], 12, font_name=theme.FONT, bold=True)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state in ("dialog", "analyzing"):
            return
        if self.choose_button.contains(x, y):
            self.open_dialog()
        elif self.state == "done" and self.play_button.contains(x, y):
            self.on_ready(self.path, self.result)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.T:
            theme.toggle_theme()
        elif key == arcade.key.ESCAPE and self.on_back and self.state != "analyzing":
            self.on_back()
        elif key == arcade.key.ENTER and self.state == "done":
            self.on_ready(self.path, self.result)
