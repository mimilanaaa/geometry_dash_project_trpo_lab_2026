"""Musically Geometry — запуск игры.

    python main.py          главное меню → трек → генерация уровня → выбор формы → игра
    python main.py --demo   то же, но со встроенным демо-уровнем без музыки
"""

import os
import sys
import arcade

from ui import settings
from ui.hud import Hud
from ui.menu import FormSelectView
from ui.track_screen import TrackLoadView
from ui.screens import MainMenuView, PauseView, DeathView, CompleteView, SettingsView
from ui.level_viewer import LevelViewerView, make_demo_level
from ui.game_view import GameView

WIDTH = 1280
HEIGHT = 720
TITLE = "Musically Geometry"


class App:
    def __init__(self, demo=False):
        settings.load()
        self.window = arcade.Window(WIDTH, HEIGHT, TITLE)
        self.demo = demo
        self.track_view = None
        self.track_path = None
        self.level = None
        self.form = "cube"
        self.attempt = 1
        self.hud = Hud(WIDTH, HEIGHT)
        self.game = None

    # --- меню ---

    def show_menu(self):
        self.stop_game()
        self.window.show_view(MainMenuView(self.play, self.show_forms_only,
                                           self.show_settings, arcade.exit))

    def show_settings(self):
        self.window.show_view(SettingsView(self.show_menu))

    def show_forms_only(self):
        def chosen(form):
            self.form = form
            self.show_menu()
        self.window.show_view(FormSelectView(chosen, self.show_menu, self.form))

    # --- трек и уровень ---

    def play(self):
        if self.demo:
            self.level_ready(make_demo_level(), None)
        else:
            self.show_track()

    def show_track(self):
        if self.track_view is None:
            self.track_view = TrackLoadView(self.track_ready, self.show_menu, on_map=self.show_map)
        self.window.show_view(self.track_view)

    def show_map(self, level):
        self.window.show_view(LevelViewerView(level, self.show_track))

    def track_ready(self, path, result):
        self.level_ready(result["level"], path)

    def level_ready(self, level, track_path):
        self.level = level
        self.track_path = track_path
        self.hud.reset()
        back = self.show_menu if self.demo else self.show_track
        self.window.show_view(FormSelectView(self.form_chosen, back, self.form))

    def form_chosen(self, form):
        self.form = form
        self.attempt = 1
        self.start_game()

    # --- забег ---

    def start_game(self):
        self.stop_game()
        self.game = GameView(self.level, self.form, self.track_path, self.attempt, self.hud,
                             on_pause=self.show_pause, on_death=self.show_death,
                             on_complete=self.show_complete)
        self.window.show_view(self.game)

    def stop_game(self):
        if self.game is not None:
            self.game.stop_music()

    def resume(self):
        self.window.show_view(self.game)

    def restart(self):
        self.attempt += 1
        self.start_game()

    def show_pause(self):
        self.window.show_view(PauseView(self.game, self.resume, self.restart, self.show_menu))

    def show_death(self):
        self.window.show_view(DeathView(self.attempt, self.game.percent(), self.hud.best_percent,
                                        self.restart, self.show_menu, self.game))

    def show_complete(self):
        name = os.path.basename(self.track_path) if self.track_path else self.level.name
        self.window.show_view(CompleteView(name, self.attempt,
                                           lambda: self.form_chosen(self.form), self.show_menu))

    def run(self):
        self.show_menu()
        arcade.run()


if __name__ == "__main__":
    App(demo="--demo" in sys.argv[1:]).run()
