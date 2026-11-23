import arcade
from ui import theme
from ui import settings
from ui import form_view
from ui import shadow
from ui.menu import draw_title
from ui.track_screen import Button


class ButtonMenu:
    def __init__(self, items, x, top, width=320, height=56, gap=16):
        self.items = items
        self.index = 0
        self.buttons = []
        for i, item in enumerate(items):
            y = top - i * (height + gap)
            self.buttons.append(Button(item[0], x, y, width, height))

    def move(self, x, top, gap=16):
        for i, b in enumerate(self.buttons):
            b.x = x
            b.y = top - i * (b.height + gap)

    def draw(self):
        for i, b in enumerate(self.buttons):
            b.draw(filled=(i == self.index))

    def press(self):
        self.items[self.index][1]()

    def on_key_press(self, key):
        if key == arcade.key.UP:
            self.index = (self.index - 1) % len(self.items)
        elif key == arcade.key.DOWN:
            self.index = (self.index + 1) % len(self.items)
        elif key == arcade.key.ENTER or key == arcade.key.SPACE:
            self.press()

    def on_mouse_motion(self, x, y):
        for i, b in enumerate(self.buttons):
            if b.contains(x, y):
                self.index = i

    def on_mouse_press(self, x, y):
        for i, b in enumerate(self.buttons):
            if b.contains(x, y):
                self.index = i
                self.press()
                return


def draw_overlay(window):
    t = theme.get_theme()
    arcade.draw_lrbt_rectangle_filled(0, window.width, 0, window.height, t["background"] + (215,))


class MainMenuView(arcade.View):
    def __init__(self, on_play, on_forms, on_settings, on_exit):
        super().__init__()
        self.menu = ButtonMenu([
            ("ИГРАТЬ", on_play),
            ("ФОРМЫ", on_forms),
            ("НАСТРОЙКИ", on_settings),
            ("ВЫХОД", on_exit),
        ], 200, 380)
        self.angle = 0

    def on_show_view(self):
        self.menu.move(200, self.window.height / 2 + 20)

    def on_update(self, delta_time):
        self.angle -= 60 * delta_time

    def on_draw(self):
        self.clear(theme.get_theme()["background"])
        t = theme.get_theme()
        w = self.window.width
        h = self.window.height
        arcade.draw_polygon_filled([(w * 0.55, 0), (w, 0), (w, h), (w * 0.75, h)], t["accent"])
        shadow.text("MUSICALLY", 40, h - 110, 54, 5)
        shadow.text("GEOMETRY", 40, h - 175, 54, 5)
        arcade.draw_text("MUSICALLY", 40, h - 110, t["text"], 54, font_name=theme.FONT, bold=True)
        arcade.draw_text("GEOMETRY", 40, h - 175, t["accent"], 54, font_name=theme.FONT, bold=True)
        arcade.draw_text("Уровни из твоей музыки", 44, h - 210, t["text_soft"], 16,
                         font_name=theme.FONT, bold=True)
        self.menu.draw()
        cx = w * 0.8
        cy = h / 2
        cube = [(cx - 145, cy + 35), (cx - 35, cy + 35), (cx - 35, cy + 145), (cx - 145, cy + 145)]
        shadow.polygon(form_view.rotate_points(cube, cx - 90, cy + 90, self.angle), 14)
        shadow.polygon([(cx + 25, cy - 53), (cx + 135, cy - 20), (cx + 25, cy + 13)], 14)
        shadow.circle(cx - 60, cy - 150, 45, 14)
        form_view.draw_form("cube", cx - 90, cy + 90, 110, self.angle)
        form_view.draw_form("ship", cx + 80, cy - 20, 110)
        form_view.draw_form("ball", cx - 60, cy - 150, 90, -self.angle)
        arcade.draw_text("T — тема", w - 24, 24, t["background"], 12, font_name=theme.FONT,
                         bold=True, anchor_x="right")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.T:
            theme.toggle_theme()
            settings.save()
        else:
            self.menu.on_key_press(key)

    def on_mouse_motion(self, x, y, dx, dy):
        self.menu.on_mouse_motion(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        self.menu.on_mouse_press(x, y)


class PauseView(arcade.View):
    def __init__(self, game_view, on_resume, on_restart, on_menu):
        super().__init__()
        self.game_view = game_view
        self.on_resume = on_resume
        self.menu = ButtonMenu([
            ("ПРОДОЛЖИТЬ", on_resume),
            ("ЗАНОВО", on_restart),
            ("В МЕНЮ", on_menu),
        ], 0, 0)

    def on_show_view(self):
        self.menu.move(self.window.width / 2, self.window.height / 2 + 30)

    def on_draw(self):
        self.clear(theme.get_theme()["background"])
        if self.game_view:
            self.game_view.on_draw()
        draw_overlay(self.window)
        t = theme.get_theme()
        arcade.draw_text("ПАУЗА", self.window.width / 2, self.window.height / 2 + 110, t["text"], 44,
                         font_name=theme.FONT, bold=True, anchor_x="center")
        self.menu.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.on_resume()
        else:
            self.menu.on_key_press(key)

    def on_mouse_motion(self, x, y, dx, dy):
        self.menu.on_mouse_motion(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        self.menu.on_mouse_press(x, y)


class DeathView(arcade.View):
    def __init__(self, attempt, percent, best, on_retry, on_menu, game_view=None):
        super().__init__()
        self.attempt = attempt
        self.percent = int(percent)
        self.best = int(best)
        self.game_view = game_view
        self.menu = ButtonMenu([
            ("ЕЩЁ РАЗ", on_retry),
            ("В МЕНЮ", on_menu),
        ], 0, 0)

    def on_show_view(self):
        self.menu.move(self.window.width / 2, self.window.height / 2 - 60)

    def on_draw(self):
        self.clear(theme.get_theme()["background"])
        if self.game_view:
            self.game_view.on_draw()
        draw_overlay(self.window)
        t = theme.get_theme()
        cx = self.window.width / 2
        cy = self.window.height / 2
        shadow.text(str(self.percent) + "%", cx, cy + 110, 72, 5, anchor_x="center")
        arcade.draw_text(str(self.percent) + "%", cx, cy + 110, t["accent"], 72,
                         font_name=theme.FONT, bold=True, anchor_x="center")
        arcade.draw_text("ПОПЫТКА " + str(self.attempt), cx, cy + 60, t["text"], 20,
                         font_name=theme.FONT, bold=True, anchor_x="center")
        arcade.draw_text("ЛУЧШИЙ РЕЗУЛЬТАТ " + str(self.best) + "%", cx, cy + 25, t["text_soft"], 14,
                         font_name=theme.FONT, bold=True, anchor_x="center")
        self.menu.draw()

    def on_key_press(self, key, modifiers):
        self.menu.on_key_press(key)

    def on_mouse_motion(self, x, y, dx, dy):
        self.menu.on_mouse_motion(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        self.menu.on_mouse_press(x, y)


class CompleteView(arcade.View):
    def __init__(self, level_name, attempts, on_retry, on_menu):
        super().__init__()
        self.level_name = level_name
        self.attempts = attempts
        self.angle = 0
        self.menu = ButtonMenu([
            ("СЫГРАТЬ ЕЩЁ", on_retry),
            ("В МЕНЮ", on_menu),
        ], 0, 0)

    def on_show_view(self):
        self.menu.move(self.window.width / 2, self.window.height / 2 - 90)

    def on_update(self, delta_time):
        self.angle -= 120 * delta_time

    def on_draw(self):
        self.clear(theme.get_theme()["background"])
        t = theme.get_theme()
        w = self.window.width
        h = self.window.height
        cx = w / 2
        cy = h / 2
        arcade.draw_polygon_filled([(0, 0), (w * 0.25, 0), (0, h * 0.45)], t["accent"])
        arcade.draw_polygon_filled([(w, h), (w * 0.75, h), (w, h * 0.55)], t["accent"])
        shadow.ground(cx, cy + 122, 70)
        form_view.draw_form("cube", cx, cy + 170, 70, self.angle)
        shadow.text("УРОВЕНЬ ПРОЙДЕН", cx, cy + 70, 44, 4, anchor_x="center")
        arcade.draw_text("УРОВЕНЬ ПРОЙДЕН", cx, cy + 70, t["text"], 44,
                         font_name=theme.FONT, bold=True, anchor_x="center")
        arcade.draw_text(self.level_name, cx, cy + 30, t["text_soft"], 18,
                         font_name=theme.FONT, bold=True, anchor_x="center")
        arcade.draw_text("ПОПЫТОК: " + str(self.attempts), cx, cy - 5, t["accent"], 18,
                         font_name=theme.FONT, bold=True, anchor_x="center")
        self.menu.draw()

    def on_key_press(self, key, modifiers):
        self.menu.on_key_press(key)

    def on_mouse_motion(self, x, y, dx, dy):
        self.menu.on_mouse_motion(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        self.menu.on_mouse_press(x, y)


class SettingsView(arcade.View):
    def __init__(self, on_back):
        super().__init__()
        self.on_back = on_back
        self.rows = ["theme", "music_volume", "sfx_volume"]
        self.names = {"theme": "ТЕМА", "music_volume": "МУЗЫКА", "sfx_volume": "ЭФФЕКТЫ"}
        self.index = 0

    def row_y(self, i):
        return self.window.height / 2 + 60 - i * 80

    def draw_volume(self, value, x, y):
        t = theme.get_theme()
        shadow.box(x, x + 300, y - 6, y + 6, 3)
        arcade.draw_lrbt_rectangle_filled(x, x + 300, y - 6, y + 6, t["bar_back"])
        arcade.draw_lrbt_rectangle_filled(x, x + 3 * value, y - 6, y + 6, t["accent"])
        arcade.draw_text(str(value) + "%", x + 320, y - 9, t["text"], 16,
                         font_name=theme.FONT, bold=True)

    def on_draw(self):
        self.clear(theme.get_theme()["background"])
        t = theme.get_theme()
        draw_title(self, "НАСТРОЙКИ", "Вверх/вниз — пункт, влево/вправо — изменить, Esc — сохранить и выйти")
        left = self.window.width / 2 - 320
        for i, row in enumerate(self.rows):
            y = self.row_y(i)
            color = t["accent"] if i == self.index else t["text"]
            if i == self.index:
                arcade.draw_lrbt_rectangle_filled(left - 20, left - 12, y - 14, y + 14, t["accent"])
            arcade.draw_text(self.names[row], left, y - 10, color, 20, font_name=theme.FONT, bold=True)
            if row == "theme":
                label = "SWISS (СВЕТЛАЯ)" if t["name"] == "swiss" else "NOIR (ТЁМНАЯ)"
                arcade.draw_text("‹  " + label + "  ›", left + 220, y - 10, t["text"], 18,
                                 font_name=theme.FONT, bold=True)
            else:
                self.draw_volume(settings.values[row], left + 220, y)

    def change(self, step):
        row = self.rows[self.index]
        if row == "theme":
            theme.toggle_theme()
        else:
            settings.change_volume(row, step * 10)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.index = (self.index - 1) % len(self.rows)
        elif key == arcade.key.DOWN:
            self.index = (self.index + 1) % len(self.rows)
        elif key == arcade.key.LEFT:
            self.change(-1)
        elif key == arcade.key.RIGHT:
            self.change(1)
        elif key == arcade.key.ESCAPE:
            settings.save()
            self.on_back()

    def on_mouse_press(self, x, y, button, modifiers):
        for i in range(len(self.rows)):
            if abs(y - self.row_y(i)) < 30:
                self.index = i
                if x > self.window.width / 2:
                    self.change(1)
                else:
                    self.change(-1)
