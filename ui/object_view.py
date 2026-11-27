import arcade
from ui import theme
from ui import form_view
from ui import shadow

ORB_COLOR = (255, 210, 0)
PAD_COLOR = (255, 90, 200)
GRAVITY_FLIP_COLOR = (255, 190, 0)      # жёлтый портал: гравитация вверх
GRAVITY_NORMAL_COLOR = (0, 190, 255)    # голубой портал: обычная гравитация


def gravity_color(gravity):
    return GRAVITY_FLIP_COLOR if gravity < 0 else GRAVITY_NORMAL_COLOR


def draw_spike(x, y, size, flip=False):
    """Шип в клетке [y, y + size]; перевёрнутый висит основанием на верхней грани клетки."""
    t = theme.get_theme()
    h = size / 2
    if flip:
        top = y + size
        points = [(x - h, top), (x + h, top), (x, y)]
        arcade.draw_polygon_filled([(x - h, top), (x + h, top), (x + h + size * 0.5, top - size * 0.35)],
                                   shadow.color())
    else:
        points = [(x - h, y), (x + h, y), (x, y + size)]
        arcade.draw_polygon_filled([(x - h, y), (x + h, y), (x + h + size * 0.5, y + size * 0.35)],
                                   shadow.color())
    arcade.draw_polygon_filled(points, t["text"])
    arcade.draw_polygon_outline(points, t["accent"], 2)


def draw_block(x, y, size):
    t = theme.get_theme()
    h = size / 2
    arcade.draw_polygon_filled([(x + h, y), (x + h + size * 0.4, y + size * 0.3),
                                (x + h + size * 0.4, y + size * 1.1), (x + h, y + size)], shadow.color())
    arcade.draw_lrbt_rectangle_filled(x - h, x + h, y, y + size, t["panel"])
    arcade.draw_lrbt_rectangle_outline(x - h, x + h, y, y + size, t["line"], 3)
    q = size / 4
    arcade.draw_lrbt_rectangle_outline(x - q, x + q, y + q, y + size - q, t["text_soft"], 2)


def draw_orb(x, y, size):
    r = size / 2.5
    cy = y + size / 2
    shadow.ground(x, y + 2, size * 0.6)
    arcade.draw_circle_outline(x, cy, r, ORB_COLOR, 5)
    arcade.draw_circle_filled(x, cy, r / 2.5, ORB_COLOR)


def draw_pad(x, y, size):
    h = size / 2
    arcade.draw_arc_filled(x, y, size, size * 0.8, PAD_COLOR, 0, 180)
    arcade.draw_lrbt_rectangle_filled(x - h, x + h, y, y + 3, theme.darker(PAD_COLOR))


def draw_arrow(x, y, size, up, color):
    """Стрелка гравитационного портала: наконечник и древко."""
    d = 1 if up else -1
    tip = y + size * 0.5 * d
    base = y
    arcade.draw_polygon_filled([(x, tip), (x - size * 0.45, base), (x + size * 0.45, base)], color)
    tail = y - size * 0.5 * d
    arcade.draw_lrbt_rectangle_filled(x - size * 0.15, x + size * 0.15, min(base, tail), max(base, tail), color)


def draw_portal(x, y, size, target_form="cube", speed=1.0, kind="form"):
    """Портал высотой size * 2.4 от y. kind: form, gravity_flip (жёлтый) или gravity_normal (голубой)."""
    t = theme.get_theme()
    if kind == "gravity_flip":
        color = GRAVITY_FLIP_COLOR
    elif kind == "gravity_normal":
        color = GRAVITY_NORMAL_COLOR
    else:
        color = theme.get_form_color(target_form)
    w = size * 0.8
    h = size * 2.4
    cy = y + h / 2
    if kind != "gravity_normal":
        shadow.ground(x, y + 2, size)     # голубой висит на потолке, тени на полу у него нет
    arcade.draw_ellipse_filled(x, cy, w, h, color + (60,))
    arcade.draw_ellipse_outline(x, cy, w, h, color, 6)
    arcade.draw_ellipse_outline(x, cy, w * 0.6, h * 0.8, theme.darker(color), 2)
    if kind == "form":
        form_view.draw_form(target_form, x, cy, size * 0.45)
    else:
        draw_arrow(x, cy, size * 0.6, kind == "gravity_flip", theme.darker(color))
    if speed != 1.0:
        arcade.draw_text("x" + str(speed), x, y + h + 6, t["text"], 12,
                         font_name=theme.FONT, bold=True, anchor_x="center")


def draw_object(obj_type, x, y, size=50, properties=None):
    if obj_type == "spike":
        draw_spike(x, y, size, bool(properties and properties.get("flip")))
    elif obj_type == "block":
        draw_block(x, y, size)
    elif obj_type == "orb":
        draw_orb(x, y, size)
    elif obj_type == "pad":
        draw_pad(x, y, size)
    elif obj_type == "portal":
        target = "cube"
        if properties:
            target = properties.get("target_form", "cube")
        draw_portal(x, y, size, target)
    else:
        t = theme.get_theme()
        h = size / 2
        arcade.draw_lrbt_rectangle_outline(x - h, x + h, y, y + size, t["accent"], 2)
        arcade.draw_text("?", x, y + h, t["accent"], 16, font_name=theme.FONT,
                         bold=True, anchor_x="center", anchor_y="center")


def draw_ground(width, ground_y):
    t = theme.get_theme()
    arcade.draw_lrbt_rectangle_filled(0, width, 0, ground_y, t["panel"])
    arcade.draw_line(0, ground_y, width, ground_y, t["line"], 3)


def draw_ceiling(left, right, ceiling_y, top):
    """Потолок корабля и перевёрнутой гравитации на участке экрана [left, right]."""
    t = theme.get_theme()
    arcade.draw_lrbt_rectangle_filled(left, right, ceiling_y, top, t["panel"])
    arcade.draw_line(left, ceiling_y, right, ceiling_y, t["line"], 3)
