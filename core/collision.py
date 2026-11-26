"""Хитбоксы объектов и проверка столкновений. Прямоугольник — (left, right, bottom, top)."""

from core import physics

HALF = physics.BLOCK / 2


def overlaps(a, b):
    return a[0] < b[1] and a[1] > b[0] and a[2] < b[3] and a[3] > b[2]


def block_box(obj):
    return obj.x - HALF, obj.x + HALF, obj.y, obj.y + physics.BLOCK


def spike_box(obj):
    w = physics.SPIKE_HALF_WIDTH
    return obj.x - w, obj.x + w, obj.y, obj.y + physics.SPIKE_HEIGHT


def pad_box(obj):
    return obj.x - HALF, obj.x + HALF, obj.y, obj.y + physics.BLOCK * 0.3


def touches_orb(player, obj):
    left, right, bottom, top = player.hitbox()
    cx = obj.x
    cy = obj.y + physics.BLOCK / 2
    nearest_x = max(left, min(cx, right))
    nearest_y = max(bottom, min(cy, top))
    return (nearest_x - cx) ** 2 + (nearest_y - cy) ** 2 <= physics.ORB_RADIUS ** 2


def resolve_block(player, obj):
    """Столкновение с блоком: встать сверху, удариться снизу (корабль) или погибнуть."""
    box = block_box(obj)
    hb = player.hitbox()
    if not overlaps(hb, box):
        return None
    if hb[2] >= box[3] - physics.SNAP:
        # Верх блока: стоим на нём, а на подъёме прощаем задетый угол.
        player.y = box[3]
        if player.vy <= 0:
            player.vy = 0
            player.on_ground = True
        return "land"
    if player.form.can_bonk and player.vy >= 0 and hb[3] <= box[2] + physics.SNAP:
        player.y = box[2] - player.height
        player.vy = 0
        return "bonk"
    return "dead"
