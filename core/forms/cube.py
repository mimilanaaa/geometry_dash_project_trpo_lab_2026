from core import physics
from core.forms.base import Form


class Cube(Form):
    """Куб: прыгает, пока стоит на опоре и кнопка зажата; в воздухе вращается."""

    name = "cube"
    height = physics.BLOCK

    def enter(self, player):
        player.vy = min(player.vy, physics.CUBE_JUMP_SPEED * 0.5)

    def update(self, player, holding, dt):
        if player.on_ground and holding:
            player.vy = physics.CUBE_JUMP_SPEED
            player.on_ground = False
        player.vy = max(player.vy - physics.CUBE_GRAVITY * dt, -physics.CUBE_MAX_FALL)

        if player.on_ground:
            target = round(player.angle / 90) * 90
            step = 900 * dt
            if abs(target - player.angle) <= step:
                player.angle = target
            else:
                player.angle += step if target > player.angle else -step
        else:
            player.angle -= physics.CUBE_SPIN * dt
