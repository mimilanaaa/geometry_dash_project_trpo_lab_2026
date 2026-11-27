import math

from core import physics
from core.forms.base import Form


class Ship(Form):
    """Корабль: зажатая кнопка тянет вверх, отпущенная — вниз. Пол и потолок не убивают.

    При перевёрнутой гравитации всё наоборот: зажатая кнопка тянет вниз.
    """

    name = "ship"
    height = physics.SHIP_HEIGHT
    can_bonk = True

    def enter(self, player):
        player.vy *= 0.4
        player.angle = 0

    def update(self, player, holding, dt):
        accel = physics.SHIP_LIFT if holding else -physics.SHIP_GRAVITY
        player.vy += accel * player.gravity * dt
        player.vy = max(-physics.SHIP_MAX_SPEED, min(physics.SHIP_MAX_SPEED, player.vy))
        player.angle = math.degrees(math.atan2(player.vy, player.speed)) * 0.8
