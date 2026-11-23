import arcade
from ui import theme
from ui import form_view
from ui.hud import Hud
from ui.menu import FormSelectView
from ui.track_screen import TrackLoadView

WIDTH = 1280
HEIGHT = 720


class PreviewView(arcade.View):
    def __init__(self, form, duration, on_back):
        super().__init__()
        self.form = form
        self.duration = duration
        self.on_back = on_back
        self.time = 0
        self.attempt = 1
        self.angle = 0
        self.hud = Hud(WIDTH, HEIGHT)

    def on_update(self, delta_time):
        self.time += delta_time
        self.angle -= 180 * delta_time
        if self.time >= self.duration:
            self.time = 0
            self.attempt += 1

    def on_draw(self):
        self.clear(theme.get_theme()["background"])
        t = theme.get_theme()
        ground = 180
        arcade.draw_lrbt_rectangle_filled(0, self.window.width, 0, ground, t["panel"])
        arcade.draw_line(0, ground, self.window.width, ground, t["line"], 3)
        angle = self.angle if self.form == "cube" else 0
        form_view.draw_form(self.form, 300, ground + 30, 60, angle)
        percent = self.time / self.duration * 100
        self.hud.draw(percent, self.attempt, self.form)
        arcade.draw_text("Esc — назад, T — тема", 24, 24, t["text_soft"], 12,
                         font_name=theme.FONT, bold=True)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.on_back()
        elif key == arcade.key.T:
            theme.toggle_theme()


class Demo:
    def __init__(self):
        self.window = arcade.Window(WIDTH, HEIGHT, "Musically Geometry — UI")
        self.track = None
        self.form = "cube"

    def show_track(self):
        self.window.show_view(TrackLoadView(self.track_ready))

    def track_ready(self, path, result):
        self.track = result
        self.show_forms()

    def show_forms(self):
        self.window.show_view(FormSelectView(self.form_chosen, self.show_track, self.form))

    def form_chosen(self, form):
        self.form = form
        self.window.show_view(PreviewView(form, self.track["duration"], self.show_forms))

    def run(self):
        self.show_track()
        arcade.run()


if __name__ == "__main__":
    Demo().run()
