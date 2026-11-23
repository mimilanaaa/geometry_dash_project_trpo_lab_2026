import arcade
from ui import theme
from ui import settings
from ui import form_view
from ui import object_view
from ui import shadow
from ui.hud import Hud
from ui.menu import FormSelectView
from ui.track_screen import TrackLoadView
from ui.screens import MainMenuView, PauseView, DeathView, CompleteView, SettingsView
from ui.level_viewer import LevelViewerView, make_demo_level

WIDTH = 1280
HEIGHT = 720


class PreviewView(arcade.View):
    def __init__(self, demo, form, duration):
        super().__init__()
        self.demo = demo
        self.form = form
        self.duration = duration
        self.time = 0
        self.angle = 0
        self.hud = Hud(WIDTH, HEIGHT)

    def percent(self):
        return self.time / self.duration * 100

    def on_update(self, delta_time):
        self.time += delta_time
        self.angle -= 180 * delta_time
        if self.time >= self.duration:
            self.demo.show_complete()

    def on_draw(self):
        self.clear(theme.get_theme()["background"])
        t = theme.get_theme()
        ground = 180
        object_view.draw_ground(self.window.width, ground)
        shift = (self.time * 300) % 400
        for i in range(5):
            x = 700 + i * 400 - shift
            object_view.draw_object("spike" if i % 2 == 0 else "block", x, ground, 50)
        angle = self.angle if self.form == "cube" else 0
        shadow.ground(300, ground + 2, 60)
        form_view.draw_form(self.form, 300, ground + 30, 60, angle)
        self.hud.draw(self.percent(), self.demo.attempt, self.form)
        arcade.draw_text("Esc — пауза, D — смерть, T — тема", 24, 24, t["text_soft"], 12,
                         font_name=theme.FONT, bold=True)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.demo.show_pause()
        elif key == arcade.key.D:
            self.demo.show_death()
        elif key == arcade.key.T:
            theme.toggle_theme()


class Demo:
    def __init__(self):
        settings.load()
        self.window = arcade.Window(WIDTH, HEIGHT, "Musically Geometry — UI")
        self.track = None
        self.form = "cube"
        self.attempt = 1
        self.best = 0
        self.game = None

    def show_menu(self):
        self.window.show_view(MainMenuView(self.show_track, self.show_forms_only,
                                           self.show_settings, arcade.exit))

    def show_settings(self):
        self.window.show_view(SettingsView(self.show_menu))

    def show_forms_only(self):
        def chosen(form):
            self.form = form
            self.show_menu()
        self.window.show_view(FormSelectView(chosen, self.show_menu, self.form))

    def show_track(self):
        self.window.show_view(TrackLoadView(self.track_ready, self.show_menu))

    def track_ready(self, path, result):
        self.track = result
        self.window.show_view(FormSelectView(self.form_chosen, self.show_track, self.form))

    def form_chosen(self, form):
        self.form = form
        self.attempt = 1
        self.start_game()

    def start_game(self):
        self.game = PreviewView(self, self.form, self.track["duration"])
        self.window.show_view(self.game)

    def resume(self):
        self.window.show_view(self.game)

    def restart(self):
        self.attempt += 1
        self.start_game()

    def show_pause(self):
        self.window.show_view(PauseView(self.game, self.resume, self.restart, self.show_menu))

    def show_death(self):
        percent = self.game.percent()
        self.best = max(self.best, percent)
        self.window.show_view(DeathView(self.attempt, percent, self.best, self.restart,
                                        self.show_menu, self.game))

    def show_complete(self):
        self.window.show_view(CompleteView(self.track.get("file_name", "Трек"), self.attempt,
                                           self.restart, self.show_menu))

    def show_level_viewer(self):
        self.window.show_view(LevelViewerView(make_demo_level(), self.show_menu))

    def run(self):
        self.show_menu()
        arcade.run()


if __name__ == "__main__":
    Demo().run()
