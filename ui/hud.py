import arcade
from ui import theme
from ui import form_view


class Hud:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.bar_width = width * 0.5
        self.bar_height = 14
        self.best_percent = 0

    def resize(self, width, height):
        self.width = width
        self.height = height
        self.bar_width = width * 0.5

    def draw(self, percent, attempt=1, form="cube", practice=False):
        t = theme.get_theme()
        percent = max(0, min(100, percent))
        if percent > self.best_percent:
            self.best_percent = percent

        left = (self.width - self.bar_width) / 2
        right = left + self.bar_width
        top = self.height - 24
        bottom = top - self.bar_height

        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, t["bar_back"])
        fill_right = left + self.bar_width * percent / 100
        if fill_right > left:
            arcade.draw_lrbt_rectangle_filled(left, fill_right, bottom, top, t["accent"])
        best_x = left + self.bar_width * self.best_percent / 100
        arcade.draw_line(best_x, bottom - 4, best_x, top + 4, t["text"], 2)
        arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, t["line"], 2)

        arcade.draw_text(str(int(percent)) + "%", right + 16, bottom - 4, t["text"],
                         22, font_name=theme.FONT, bold=True)

        arcade.draw_text("ПОПЫТКА " + str(attempt), 24, self.height - 38, t["text"],
                         14, font_name=theme.FONT, bold=True)

        form_view.draw_form(form, 40, self.height - 70, 24)
        arcade.draw_text(theme.FORM_NAMES.get(form, form).upper(), 62, self.height - 77,
                         t["text_soft"], 12, font_name=theme.FONT, bold=True)

        if practice:
            arcade.draw_text("ПРАКТИКА", self.width - 24, self.height - 70, t["accent"],
                             12, font_name=theme.FONT, bold=True, anchor_x="right")

    def reset(self):
        self.best_percent = 0
