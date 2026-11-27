"""Хитбоксы объектов и проверка столкновений. Прямоугольник — (left, right, bottom, top)."""

from core import physics

HALF = physics.BLOCK / 2


def overlaps(a, b):
    return a[0] < b[1] and a[1] > b[0] and a[2] < b[3] and a[3] > b[2]


def block_box(obj):
    return obj.x - HALF, obj.x + HALF, obj.y, obj.y + physics.BLOCK


def spike_box(obj):
    """Шип стоит основанием на y и смотрит вверх; перевёрнутый (flip) висит на y + BLOCK остриём вниз."""
    w = physics.SPIKE_HALF_WIDTH
    if obj.flip:
        top = obj.y + physics.BLOCK
        return obj.x - w, obj.x + w, top - physics.SPIKE_HEIGHT, top
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


def stand_on_top(player, box):
    player.y = box[3]
    if player.vy <= 0:
        player.vy = 0
        if player.gravity > 0:
            player.on_ground = True


def stand_under(player, box):
    player.y = box[2] - player.height
    if player.vy >= 0:
        player.vy = 0
        if player.gravity < 0:
            player.on_ground = True


def resolve_block(player, obj):
    """Столкновение с блоком: встать на него, удариться другой стороной (корабль) или погибнуть.

    При обычной гравитации опора — верх блока, при перевёрнутой — низ.
    """
    box = block_box(obj)
    hb = player.hitbox()
    if not overlaps(hb, box):
        return None
    on_top = hb[2] >= box[3] - physics.SNAP
    under = hb[3] <= box[2] + physics.SNAP
    if player.gravity > 0:
        if on_top:
            # Верх блока: стоим на нём, а на подъёме прощаем задетый угол.
            stand_on_top(player, box)
            return "land"
        if player.form.can_bonk and player.vy >= 0 and under:
            stand_under(player, box)
            return "bonk"
    else:
        if under:
            stand_under(player, box)
            return "land"
        if player.form.can_bonk and player.vy <= 0 and on_top:
            stand_on_top(player, box)
            return "bonk"
    return "dead"
