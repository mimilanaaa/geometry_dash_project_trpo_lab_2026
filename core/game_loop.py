"""Игровая логика одного забега по уровню, без отрисовки.

GameSession берёт Level из generator/level_format.py, двигает игрока
в такт времени трека и сообщает, умер он или прошёл уровень.
Отрисовка и ввод — в ui/game_view.py.
"""

import bisect

from core import physics
from core import collision
from core.player import Player


def value_of(item):
    if hasattr(item, "value"):
        return item.value
    return str(item)


def find_speed(level):
    for obj in list(level.obstacles) + list(level.portals):
        if obj.time > 0 and obj.x > 0:
            return obj.x / obj.time
    return physics.DEFAULT_SPEED


def find_floor(level):
    if len(level.obstacles) == 0:
        return physics.DEFAULT_FLOOR
    return min(obs.y for obs in level.obstacles)


class LevelObject:
    __slots__ = ("kind", "x", "y", "time", "target", "used")

    def __init__(self, kind, x, y, time, target=None):
        self.kind = kind
        self.x = x
        self.y = y
        self.time = time
        self.target = target
        self.used = False


class GameSession:
    def __init__(self, level, form="cube"):
        self.level = level
        self.speed = find_speed(level)
        self.floor = find_floor(level)
        self.ceiling = self.floor + physics.SHIP_CEILING
        self.duration = max(float(level.duration), 1.0)
        self.lead = physics.JUMP_LEAD_TIME * self.speed

        objects = []
        for obs in level.obstacles:
            objects.append(LevelObject(value_of(obs.type), obs.x, obs.y, obs.time))
        for portal in level.portals:
            # Портал срабатывает при пересечении по x на любой высоте и рисуется от пола.
            objects.append(LevelObject("portal", portal.x, self.floor, portal.time,
                                       value_of(portal.target_form)))
        objects.sort(key=lambda o: o.x)
        self.objects = objects
        self.xs = [o.x for o in objects]

        self.player = Player(form, self.floor, self.speed)
        self.player.x = -self.lead
        self.time = 0.0
        self.state = "playing"      # playing / dead / complete
        self.holding = False
        self.orb_buffer = 0.0
        self.accum = 0.0
        self.events = []

    def percent(self):
        return max(0.0, min(100.0, self.time / self.duration * 100))

    def press(self):
        """Новое нажатие: нужно для колец-орбов, удержание для них не считается."""
        self.orb_buffer = 0.12

    def update(self, dt, holding):
        if self.state != "playing":
            return
        self.holding = holding
        self.accum += min(max(dt, 0.0), physics.MAX_FRAME)
        while self.accum >= physics.STEP and self.state == "playing":
            self.accum -= physics.STEP
            self.step(physics.STEP)

    def step(self, dt):
        p = self.player
        self.time += dt
        if self.orb_buffer > 0:
            self.orb_buffer -= dt

        p.form.update(p, self.holding, dt)
        p.on_ground = False
        p.y += p.vy * dt
        p.x = self.time * self.speed - self.lead

        if p.y <= self.floor:
            p.y = self.floor
            if p.vy < 0:
                p.vy = 0
            p.on_ground = True
        if p.form.name == "ship" and p.y + p.height >= self.ceiling:
            p.y = self.ceiling - p.height
            if p.vy > 0:
                p.vy = 0

        reach = physics.BLOCK * 1.5
        lo = bisect.bisect_left(self.xs, p.x - reach)
        hi = bisect.bisect_right(self.xs, p.x + reach)
        for obj in self.objects[lo:hi]:
            self.touch(obj)
            if self.state != "playing":
                return

        if self.time >= self.duration:
            self.state = "complete"
            self.events.append(("complete", None))

    def touch(self, obj):
        p = self.player
        kind = obj.kind
        if kind == "spike":
            if collision.overlaps(p.hitbox(), collision.spike_box(obj)):
                self.die()
        elif kind == "block":
            if collision.resolve_block(p, obj) == "dead":
                self.die()
        elif kind == "portal":
            if not obj.used and p.x >= obj.x:
                obj.used = True
                p.change_form(obj.target)
                self.events.append(("portal", obj.target))
        elif kind == "pad":
            if not obj.used and p.form.name == "cube" and collision.overlaps(p.hitbox(), collision.pad_box(obj)):
                obj.used = True
                p.vy = physics.PAD_SPEED
                p.on_ground = False
                self.events.append(("pad", None))
        elif kind == "orb":
            if (not obj.used and self.orb_buffer > 0 and p.form.name == "cube"
                    and collision.touches_orb(p, obj)):
                obj.used = True
                self.orb_buffer = 0
                p.vy = physics.ORB_SPEED
                p.on_ground = False
                self.events.append(("orb", None))

    def die(self):
        self.state = "dead"
        self.player.alive = False
        self.events.append(("death", None))
