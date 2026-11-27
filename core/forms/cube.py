from core import physics
from core.forms.base import Form


class Cube(Form):
    """Куб: прыгает, пока стоит на опоре и кнопка зажата; в воздухе вращается.

    Всё считается относительно гравитации: при перевёрнутой (player.gravity = -1)
    опора — потолок, а прыжок идёт вниз.
    """

    name = "cube"
    height = physics.BLOCK

    def enter(self, player):
        g = player.gravity
        player.vy = min(player.vy * g, physics.CUBE_JUMP_SPEED * 0.5) * g

    def update(self, player, holding, dt):
        g = player.gravity
        if player.on_ground and holding:
            player.vy = physics.CUBE_JUMP_SPEED * g
            player.on_ground = False
        up = player.vy * g - physics.CUBE_GRAVITY * dt
        player.vy = max(up, -physics.CUBE_MAX_FALL) * g

        if player.on_ground:
            target = round(player.angle / 90) * 90
            step = 900 * dt
            if abs(target - player.angle) <= step:
                player.angle = target
            else:
                player.angle += step if target > player.angle else -step
        else:
            player.angle -= physics.CUBE_SPIN * dt * g
