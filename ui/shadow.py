import arcade
from ui import theme

OFFSET = 6

SHADOWS = {
    "swiss": (60, 40, 30, 70),
    "noir": (0, 0, 0, 190),
}


def color():
    return SHADOWS.get(theme.get_theme()["name"], (0, 0, 0, 100))


def box(left, right, bottom, top, offset=OFFSET):
    arcade.draw_lrbt_rectangle_filled(left + offset, right + offset, bottom - offset, top - offset, color())


def polygon(points, offset=OFFSET):
    moved = [(x + offset, y - offset) for x, y in points]
    arcade.draw_polygon_filled(moved, color())


def circle(x, y, r, offset=OFFSET):
    arcade.draw_circle_filled(x + offset, y - offset, r, color())


def ellipse(x, y, w, h, offset=OFFSET):
    arcade.draw_ellipse_filled(x + offset, y - offset, w, h, color())


def text(value, x, y, size, offset=3, **kwargs):
    arcade.draw_text(value, x + offset, y - offset, color(), size, font_name=theme.FONT, bold=True, **kwargs)


def ground(x, y, width):
    c = color()
    soft = (c[0], c[1], c[2], c[3] // 2)
    arcade.draw_ellipse_filled(x, y, width * 1.3, width * 0.28, soft)
    arcade.draw_ellipse_filled(x, y, width * 0.9, width * 0.18, c)
