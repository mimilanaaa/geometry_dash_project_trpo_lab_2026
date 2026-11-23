import arcade
from ui import theme
from ui import form_view

ORB_COLOR = (255, 210, 0)
PAD_COLOR = (255, 90, 200)


def draw_spike(x, y, size):
    t = theme.get_theme()
    h = size / 2
    points = [(x - h, y), (x + h, y), (x, y + size)]
    arcade.draw_polygon_filled(points, t["text"])
    arcade.draw_polygon_outline(points, t["accent"], 2)


def draw_block(x, y, size):
    t = theme.get_theme()
    h = size / 2
    arcade.draw_lrbt_rectangle_filled(x - h, x + h, y, y + size, t["panel"])
    arcade.draw_lrbt_rectangle_outline(x - h, x + h, y, y + size, t["line"], 3)
    q = size / 4
    arcade.draw_lrbt_rectangle_outline(x - q, x + q, y + q, y + size - q, t["text_soft"], 2)


def draw_orb(x, y, size):
    r = size / 2.5
    cy = y + size / 2
    arcade.draw_circle_outline(x, cy, r, ORB_COLOR, 5)
    arcade.draw_circle_filled(x, cy, r / 2.5, ORB_COLOR)


def draw_pad(x, y, size):
    h = size / 2
    arcade.draw_arc_filled(x, y, size, size * 0.8, PAD_COLOR, 0, 180)
    arcade.draw_lrbt_rectangle_filled(x - h, x + h, y, y + 3, theme.darker(PAD_COLOR))


def draw_portal(x, y, size, target_form="cube", speed=1.0):
    t = theme.get_theme()
    color = theme.get_form_color(target_form)
    w = size * 0.8
    h = size * 2.4
    cy = y + h / 2
    arcade.draw_ellipse_filled(x, cy, w, h, color + (60,))
    arcade.draw_ellipse_outline(x, cy, w, h, color, 6)
    arcade.draw_ellipse_outline(x, cy, w * 0.6, h * 0.8, theme.darker(color), 2)
    form_view.draw_form(target_form, x, cy, size * 0.45)
    if speed != 1.0:
        arcade.draw_text("x" + str(speed), x, y + h + 6, t["text"], 12,
                         font_name=theme.FONT, bold=True, anchor_x="center")


def draw_object(obj_type, x, y, size=50, properties=None):
    if obj_type == "spike":
        draw_spike(x, y, size)
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
