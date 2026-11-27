import bisect
import math
import random
import arcade

from ui import theme
from ui import settings
from ui import form_view
from ui import object_view
from ui import shadow
from core import physics
from core.game_loop import GameSession
from music.loader import TrackPlayer

PLAYER_SCREEN_X = 320
GROUND_SCREEN_Y = 110
PORTAL_SIZE = 110
JUMP_KEYS = (arcade.key.SPACE, arcade.key.UP, arcade.key.W)
DEATH_DELAY = 0.7


class Piece:
    def __init__(self, x, y, color):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(150, 520)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed + 200
        self.size = random.uniform(6, 14)
        self.color = color

    def update(self, dt):
        self.vy -= 1400 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt


class GameView(arcade.View):
    """Забег по уровню: рисует GameSession, передаёт ей нажатия и ведёт музыку."""

    def __init__(self, level, form, track_path, attempt, hud, on_pause, on_death, on_complete):
        super().__init__()
        self.session = GameSession(level, form)
        self.music = TrackPlayer(track_path, settings.values.get("music_volume", 80) / 100)
        self.attempt = attempt
        self.hud = hud
        self.on_pause = on_pause
        self.on_death = on_death
        self.on_complete = on_complete
        self.keys = set()
        self.mouse = False
        self.started = False
        self.finished = False
        self.death_timer = 0.0
        self.pieces = []
        self.flash = 0.0
        self.flash_color = (255, 255, 255)

    # --- жизненный цикл ---

    def on_show_view(self):
        self.keys.clear()
        self.mouse = False
        if not self.started:
            self.started = True
            self.music.start()
        elif self.session.state == "playing":
            self.music.resume()

    def stop_music(self):
        self.music.stop()

    def pause(self):
        self.music.pause()
        self.on_pause()

    def percent(self):
        return self.session.percent()

    # --- обновление ---

    def holding(self):
        return bool(self.keys) or self.mouse

    def game_step(self, dt):
        """Время игры идёт за музыкой: мелкий разнос подтягиваем плавно, крупный — сразу."""
        step = dt
        pos = self.music.position()
        if pos is not None and pos > 0.05:
            diff = pos - (self.session.time + dt)
            step = dt + (diff if abs(diff) > 0.25 else diff * 0.1)
        return max(0.0, step)

    def on_update(self, delta_time):
        s = self.session
        if s.state == "playing":
            s.update(self.game_step(delta_time), self.holding())
        for kind, value in s.events:
            if kind == "portal":
                self.flash = 0.35
                self.flash_color = theme.get_form_color(value)
            elif kind == "gravity":
                self.flash = 0.35
                self.flash_color = object_view.gravity_color(value)
            elif kind == "death":
                self.music.stop()
                p = s.player
                color = theme.get_form_color(p.form_name)
                sx, sy = self.to_screen(p.x, p.center_y())
                self.pieces = [Piece(sx, sy, color) for _ in range(18)]
        s.events.clear()

        self.flash = max(0.0, self.flash - delta_time)
        for piece in self.pieces:
            piece.update(delta_time)

        if s.state == "dead":
            self.death_timer += delta_time
            if self.death_timer >= DEATH_DELAY and not self.finished:
                self.finished = True
                self.on_death()
        elif s.state == "complete" and not self.finished:
            self.finished = True
            self.music.stop()
            self.on_complete()

    # --- отрисовка ---

    def to_screen(self, x, y):
        s = self.session
        return x - s.player.x + PLAYER_SCREEN_X, y - s.floor + GROUND_SCREEN_Y

    def on_draw(self):
        self.clear(theme.get_theme()["background"])
        t = theme.get_theme()
        s = self.session
        p = s.player
        w = self.window.width
        h = self.window.height

        ceil_y = s.ceiling - s.floor + GROUND_SCREEN_Y
        for start, end in s.ceiling_spans:
            left = max(0, self.to_screen(start, 0)[0])
            right = min(w, self.to_screen(end, 0)[0])
            if left < right:
                object_view.draw_ceiling(left, right, ceil_y, h)
        object_view.draw_ground(w, GROUND_SCREEN_Y)

        if self.flash > 0:
            alpha = int(120 * self.flash / 0.35)
            arcade.draw_lrbt_rectangle_filled(0, w, GROUND_SCREEN_Y, h, self.flash_color + (alpha,))

        left = p.x - PLAYER_SCREEN_X - physics.BLOCK * 3
        right = left + w + physics.BLOCK * 6
        lo = bisect.bisect_left(s.xs, left)
        hi = bisect.bisect_right(s.xs, right)
        for obj in s.objects[lo:hi]:
            sx, sy = self.to_screen(obj.x, obj.y)
            if obj.kind == "portal":
                object_view.draw_portal(sx, GROUND_SCREEN_Y, PORTAL_SIZE, obj.target)
            elif obj.kind == "gravity":
                if obj.target < 0:
                    object_view.draw_portal(sx, GROUND_SCREEN_Y, PORTAL_SIZE, kind="gravity_flip")
                else:
                    # к голубому порталу игрок подходит вверх ногами, поэтому он висит на потолке
                    object_view.draw_portal(sx, ceil_y - PORTAL_SIZE * 2.4, PORTAL_SIZE,
                                            kind="gravity_normal")
            elif not (obj.used and obj.kind == "orb"):
                object_view.draw_object(obj.kind, sx, sy, physics.BLOCK, obj.props)

        if p.alive:
            sx, sy = self.to_screen(p.x, p.center_y())
            if p.gravity > 0:
                height = p.y - s.floor
                if height < 200:
                    shadow.ground(sx, GROUND_SCREEN_Y + 2, 60 * (1 - height / 300))
            else:
                height = s.ceiling - p.y - p.height
                if height < 200:
                    shadow.ground(sx, ceil_y - 2, 60 * (1 - height / 300))
            form_view.draw_form(p.form_name, sx, sy, physics.BLOCK, p.angle)

        for piece in self.pieces:
            half = piece.size / 2
            arcade.draw_lrbt_rectangle_filled(piece.x - half, piece.x + half,
                                              piece.y - half, piece.y + half, piece.color)

        self.hud.draw(s.percent(), self.attempt, p.form_name)
        hint = "Пробел / ↑ / ЛКМ — прыжок, удерживать — лететь   Esc — пауза   T — тема"
        arcade.draw_text(hint, 24, 24, t["text_soft"], 12, font_name=theme.FONT, bold=True)
        if self.music.error:
            arcade.draw_text(self.music.error, w - 24, 24, t["accent"], 12, font_name=theme.FONT,
                             bold=True, anchor_x="right")

    # --- ввод ---

    def on_key_press(self, key, modifiers):
        if key in JUMP_KEYS:
            if key not in self.keys:
                self.keys.add(key)
                self.session.press()
        elif key == arcade.key.ESCAPE and self.session.state == "playing":
            self.pause()
        elif key == arcade.key.T:
            theme.toggle_theme()

    def on_key_release(self, key, modifiers):
        self.keys.discard(key)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.mouse = True
            self.session.press()

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.mouse = False
