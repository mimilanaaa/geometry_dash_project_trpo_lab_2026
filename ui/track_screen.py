import os
import sys
import subprocess
import threading
import arcade
from ui import theme
from ui import shadow
from ui.menu import draw_title

FORMATS = [".mp3", ".wav", ".ogg", ".flac", ".m4a"]
MIN_SECONDS = 30
MAX_SECONDS = 600

DIFFICULTIES = ["easy", "normal", "hard"]
DIFFICULTY_NAMES = {"easy": "ЛЁГКИЙ", "normal": "ОБЫЧНЫЙ", "hard": "СЛОЖНЫЙ"}

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

    def draw(self, filled=True, size=16):
        t = theme.get_theme()
        left = self.x - self.width / 2
        right = self.x + self.width / 2
        bottom = self.y - self.height / 2
        top = self.y + self.height / 2
        shadow.box(left, right, bottom, top, 5)
        if filled:
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, t["accent"])
            text_color = t["background"]
        else:
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, t["panel"])
            arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, t["line"], 3)
            text_color = t["text"]
        arcade.draw_text(self.text, self.x, self.y, text_color, size, font_name=theme.FONT,
                         bold=True, anchor_x="center", anchor_y="center")


class TrackLoadView(arcade.View):
    def __init__(self, on_ready, on_back=None, generate=None, on_map=None):
        super().__init__()
        self.on_ready = on_ready
        self.on_back = on_back
        self.on_map = on_map
        self.generate = generate
        self.state = "empty"
        self.path = ""
        self.error = ""
        self.result = None
        self.thread_result = None
        self.thread_error = ""
        self.picked_path = None
        self.dot_timer = 0
        self.difficulty = "normal"
        self.seed = 1
        self.choose_button = Button("ВЫБРАТЬ ФАЙЛ", 0, 0, 230)
        self.variant_button = Button("ЕЩЁ ВАРИАНТ", 0, 0, 230)
        self.map_button = Button("КАРТА", 0, 0, 230)
        self.play_button = Button("ИГРАТЬ", 0, 0, 230)
        self.difficulty_buttons = {}
        for d in DIFFICULTIES:
            self.difficulty_buttons[d] = Button(DIFFICULTY_NAMES[d], 0, 0, 150, 40)

    def place_buttons(self):
        w = self.window.width
        h = self.window.height
        row = [self.choose_button, self.variant_button, self.map_button, self.play_button]
        for i, b in enumerate(row):
            b.x = w / 2 + (i - 1.5) * 250
            b.y = 140
        for i, d in enumerate(DIFFICULTIES):
            b = self.difficulty_buttons[d]
            b.x = w / 2 + (i - 1) * 170
            b.y = h - 270

    def on_show_view(self):
        self.place_buttons()

    def on_resize(self, width, height):
        self.place_buttons()

    def busy(self):
        return self.state in ("dialog", "working")

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
        self.seed = 1
        self.error = check_file(path)
        if self.error:
            self.state = "error"
            return
        self.start_generation()

    def start_generation(self):
        generate = self.generate
        if generate is None:
            try:
                from generator.level_builder import generate_level
                generate = generate_level
            except Exception:
                self.state = "error"
                self.error = "Генератор не запустился. Установите библиотеки: pip install -r requirements.txt"
                return

        path = self.path
        seed = self.seed
        difficulty = self.difficulty

        def worker():
            try:
                level = generate(path, seed=seed, difficulty=difficulty)
                self.thread_result = {
                    "bpm": level.bpm,
                    "duration": level.duration,
                    "file_name": os.path.basename(path),
                    "level": level,
                }
            except Exception as e:
                self.thread_error = "Не удалось построить уровень: " + str(e)

        self.thread_result = None
        self.thread_error = ""
        self.state = "working"
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
        if self.state == "working":
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

    def set_difficulty(self, difficulty):
        if difficulty == self.difficulty or self.busy():
            return
        self.difficulty = difficulty
        if self.result is not None:
            self.start_generation()

    def next_variant(self):
        self.seed += 1
        self.start_generation()

    def draw_info_line(self, label, value, y):
        t = theme.get_theme()
        left = self.window.width / 2 - 220
        arcade.draw_text(label, left, y, t["text_soft"], 14, font_name=theme.FONT, bold=True)
        arcade.draw_text(value, left + 240, y, t["text"], 14, font_name=theme.FONT, bold=True)

    def on_draw(self):
        self.clear(theme.get_theme()["background"])
        t = theme.get_theme()
        w = self.window.width
        h = self.window.height
        draw_title(self, "ЗАГРУЗКА ТРЕКА", "MP3, WAV, OGG, FLAC, M4A — от 30 секунд до 10 минут")

        left = w / 2 - 330
        right = w / 2 + 330
        bottom = 200
        top = h - 230
        shadow.box(left, right, bottom, top, 10)
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, t["panel"])
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, t["line"], 2)

        for d in DIFFICULTIES:
            self.difficulty_buttons[d].draw(filled=(d == self.difficulty), size=13)

        cy = (top - 70 + bottom) / 2
        if self.state == "empty":
            arcade.draw_text("Трек не выбран", w / 2, cy, t["text_soft"], 18,
                             font_name=theme.FONT, bold=True, anchor_x="center")
        elif self.state == "dialog":
            arcade.draw_text("Выберите файл в открывшемся окне", w / 2, cy, t["text_soft"], 16,
                             font_name=theme.FONT, bold=True, anchor_x="center")
        elif self.state == "working":
            dots = "." * (int(self.dot_timer * 3) % 4)
            arcade.draw_text("Анализ трека и генерация уровня" + dots, w / 2, cy + 20, t["text"], 18,
                             font_name=theme.FONT, bold=True, anchor_x="center")
            arcade.draw_text(os.path.basename(self.path) + " · вариант " + str(self.seed), w / 2, cy - 15,
                             t["text_soft"], 14, font_name=theme.FONT, anchor_x="center")
            bar_left = w / 2 - 150
            pos = (self.dot_timer * 150) % 300
            arcade.draw_lrbt_rectangle_filled(bar_left, bar_left + 300, cy - 50, cy - 42, t["bar_back"])
            arcade.draw_lrbt_rectangle_filled(bar_left + pos, min(bar_left + pos + 60, bar_left + 300),
                                              cy - 50, cy - 42, t["accent"])
        elif self.state == "done":
            r = self.result
            level = r["level"]
            arcade.draw_text(r["file_name"], w / 2, cy + 70, t["text"], 18,
                             font_name=theme.FONT, bold=True, anchor_x="center")
            self.draw_info_line("ТЕМП", str(round(r["bpm"])) + " BPM", cy + 25)
            self.draw_info_line("ДЛИТЕЛЬНОСТЬ", format_time(r["duration"]), cy - 5)
            self.draw_info_line("ПРЕПЯТСТВИЙ", str(len(level.obstacles)), cy - 35)
            self.draw_info_line("ПОРТАЛОВ", str(len(level.portals)), cy - 65)
            self.draw_info_line("ВАРИАНТ", "№ " + str(self.seed), cy - 95)
        elif self.state == "error":
            arcade.draw_text(self.error, w / 2, cy, t["accent"], 15,
                             font_name=theme.FONT, bold=True, anchor_x="center",
                             width=600, multiline=True, align="center")

        self.choose_button.draw(filled=False)
        if self.state == "done":
            self.variant_button.draw(filled=False)
            if self.on_map:
                self.map_button.draw(filled=False)
            self.play_button.draw(filled=True)
        arcade.draw_text("1 2 3 — сложность   Esc — назад", 24, 24, t["text_soft"], 12,
                         font_name=theme.FONT, bold=True)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.busy():
            return
        for d in DIFFICULTIES:
            if self.difficulty_buttons[d].contains(x, y):
                self.set_difficulty(d)
                return
        if self.choose_button.contains(x, y):
            self.open_dialog()
        elif self.state == "done":
            if self.variant_button.contains(x, y):
                self.next_variant()
            elif self.on_map and self.map_button.contains(x, y):
                self.on_map(self.result["level"])
            elif self.play_button.contains(x, y):
                self.on_ready(self.path, self.result)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.T:
            theme.toggle_theme()
        elif key == arcade.key.KEY_1:
            self.set_difficulty("easy")
        elif key == arcade.key.KEY_2:
            self.set_difficulty("normal")
        elif key == arcade.key.KEY_3:
            self.set_difficulty("hard")
        elif key == arcade.key.ESCAPE and self.on_back and not self.busy():
            self.on_back()
        elif key == arcade.key.ENTER and self.state == "done":
            self.on_ready(self.path, self.result)
