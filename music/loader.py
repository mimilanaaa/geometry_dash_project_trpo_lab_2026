"""Проигрывание трека во время забега.

Звук открывается потоково: файл не декодируется целиком, а потоковый звук
в arcade играет только один раз, поэтому на каждую попытку он открывается заново.
"""

import arcade


class TrackPlayer:
    def __init__(self, path, volume=0.8):
        self.path = path
        self.volume = max(0.0, min(1.0, volume))
        self.sound = None
        self.player = None
        self.error = ""

    def start(self):
        self.stop()
        if not self.path:
            return
        try:
            self.sound = arcade.load_sound(self.path, streaming=True)
            self.player = self.sound.play(volume=self.volume)
        except Exception as e:
            self.sound = None
            self.player = None
            self.error = "Музыка не играет: " + str(e)

    def pause(self):
        if self.player is not None:
            self.player.pause()

    def resume(self):
        if self.player is not None:
            self.player.play()

    def stop(self):
        if self.player is not None:
            try:
                arcade.stop_sound(self.player)
            except Exception:
                pass
        self.player = None
        self.sound = None

    def position(self):
        """Сколько секунд трека уже прозвучало, или None, если музыки нет."""
        if self.player is None:
            return None
        try:
            return float(self.player.time)
        except Exception:
            return None
