import arcade
from ui import theme
from ui import form_view
from ui import shadow


def draw_title(view, title, subtitle):
    t = theme.get_theme()
    w = view.window.width
    h = view.window.height
    arcade.draw_polygon_filled([(0, h), (220, h), (120, h - 90), (0, h - 90)], t["accent"])
    shadow.text(title, 40, h - 150, 40, 4)
    arcade.draw_text(title, 40, h - 150, t["text"], 40, font_name=theme.FONT, bold=True)
    arcade.draw_text(subtitle, 42, h - 185, t["text_soft"], 14, font_name=theme.FONT, bold=True)
    arcade.draw_text("T — тема", w - 24, h - 40, t["text_soft"], 12,
                     font_name=theme.FONT, bold=True, anchor_x="right")


class FormSelectView(arcade.View):
    def __init__(self, on_choose, on_back=None, selected="cube"):
        super().__init__()
        self.on_choose = on_choose
        self.on_back = on_back
        self.forms = theme.FORM_ORDER
        self.index = self.forms.index(selected) if selected in self.forms else 0
        self.message = ""
        self.angle = 0

    def card_rect(self, i):
        w = self.window.width
        card_w = 150
        gap = 24
        total = len(self.forms) * card_w + (len(self.forms) - 1) * gap
        left = (w - total) / 2 + i * (card_w + gap)
        bottom = self.window.height / 2 - 110
        return left, left + card_w, bottom, bottom + 200

    def is_open(self, form):
        return form in theme.FIRST_VERSION_FORMS

    def on_update(self, delta_time):
        self.angle -= 90 * delta_time

    def on_draw(self):
        self.clear(theme.get_theme()["background"])
        t = theme.get_theme()
        draw_title(self, "ВЫБОР ФОРМЫ", "Стрелки — выбор, Enter — подтвердить, Esc — назад")

        for i, form in enumerate(self.forms):
            left, right, bottom, top = self.card_rect(i)
            opened = self.is_open(form)
            lift = 12 if i == self.index else 6
            shadow.box(left, right, bottom, top, lift)
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, t["panel"])
            if i == self.index:
                arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, t["accent"], 5)
            else:
                arcade.draw_lrbt_rectangle_outline(left, right, bottom, top, t["line"], 2)

            cx = (left + right) / 2
            angle = self.angle if i == self.index and opened else 0
            shadow.ground(cx, bottom + 72, 60)
            if opened:
                form_view.draw_form(form, cx, bottom + 120, 70, angle)
                name_color = t["text"]
            else:
                form_view.draw_form(form, cx, bottom + 120, 70, 0, t["locked"])
                name_color = t["locked"]

            arcade.draw_text(theme.FORM_NAMES[form].upper(), cx, bottom + 40, name_color, 16,
                             font_name=theme.FONT, bold=True, anchor_x="center")
            if not opened:
                arcade.draw_text("СКОРО", cx, bottom + 16, t["text_soft"], 11,
                                 font_name=theme.FONT, bold=True, anchor_x="center")

        if self.message:
            arcade.draw_text(self.message, self.window.width / 2, 80, t["accent"], 14,
                             font_name=theme.FONT, bold=True, anchor_x="center")

    def choose(self):
        form = self.forms[self.index]
        if self.is_open(form):
            self.on_choose(form)
        else:
            self.message = theme.FORM_NAMES[form] + " появится в следующей версии"

    def on_key_press(self, key, modifiers):
        self.message = ""
        if key == arcade.key.LEFT:
            self.index = (self.index - 1) % len(self.forms)
        elif key == arcade.key.RIGHT:
            self.index = (self.index + 1) % len(self.forms)
        elif key == arcade.key.ENTER or key == arcade.key.SPACE:
            self.choose()
        elif key == arcade.key.T:
            theme.toggle_theme()
        elif key == arcade.key.ESCAPE and self.on_back:
            self.on_back()

    def on_mouse_press(self, x, y, button, modifiers):
        for i in range(len(self.forms)):
            left, right, bottom, top = self.card_rect(i)
            if left <= x <= right and bottom <= y <= top:
                self.message = ""
                if self.index == i:
                    self.choose()
                else:
                    self.index = i
