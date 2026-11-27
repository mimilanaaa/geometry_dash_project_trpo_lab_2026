from core import physics
from core.forms.cube import Cube
from core.forms.ship import Ship

FORMS = {
    "cube": Cube,
    "ship": Ship,
}


def make_form(name):
    """Форма по имени из формата уровня; ещё не сделанные формы пока играются кубом."""
    return FORMS.get(name, Cube)()


class Player:
    def __init__(self, form="cube", floor=physics.DEFAULT_FLOOR, speed=physics.DEFAULT_SPEED):
        self.x = 0.0
        self.y = floor          # нижняя грань хитбокса
        self.vy = 0.0
        self.speed = speed
        self.angle = 0.0
        self.on_ground = True
        self.alive = True
        self.gravity = 1        # 1 — обычная, -1 — перевёрнутая
        self.form = make_form(form)

    @property
    def form_name(self):
        return self.form.name

    @property
    def height(self):
        return self.form.height

    def hitbox(self):
        half = physics.BLOCK / 2
        return self.x - half, self.x + half, self.y, self.y + self.height

    def center_y(self):
        return self.y + self.height / 2

    def change_form(self, name):
        if name == self.form.name:
            return
        old_center = self.center_y()
        self.form = make_form(name)
        self.y = old_center - self.height / 2
        self.form.enter(self)

    def change_gravity(self, gravity):
        """Гравитационный портал: жёлтый даёт -1 (вверх), синий — 1 (обычная)."""
        if gravity == self.gravity:
            return
        self.gravity = gravity
        self.vy *= physics.GRAVITY_PORTAL_DAMP
        self.on_ground = False
