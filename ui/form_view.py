import math
import arcade
from ui import theme


def rotate_points(points, cx, cy, angle):
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    result = []
    for px, py in points:
        dx = px - cx
        dy = py - cy
        result.append((cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a))
    return result


def draw_shape(points, color, line_color):
    arcade.draw_polygon_filled(points, color)
    arcade.draw_polygon_outline(points, line_color, 3)


def draw_cube(x, y, size, angle, color):
    h = size / 2
    dark = theme.darker(color)
    outer = [(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h)]
    draw_shape(rotate_points(outer, x, y, angle), color, dark)
    q = size / 5
    inner = [(x - q, y - q), (x + q, y - q), (x + q, y + q), (x - q, y + q)]
    draw_shape(rotate_points(inner, x, y, angle), dark, dark)


def draw_ship(x, y, size, angle, color):
    h = size / 2
    dark = theme.darker(color)
    body = [(x - h, y - h * 0.6), (x + h, y), (x - h, y + h * 0.6), (x - h * 0.6, y)]
    draw_shape(rotate_points(body, x, y, angle), color, dark)
    window = [(x - h * 0.3, y - h * 0.2), (x + h * 0.2, y), (x - h * 0.3, y + h * 0.2)]
    draw_shape(rotate_points(window, x, y, angle), dark, dark)


def draw_ball(x, y, size, angle, color):
    r = size / 2
    dark = theme.darker(color)
    arcade.draw_circle_filled(x, y, r, color)
    arcade.draw_circle_outline(x, y, r, dark, 3)
    line1 = rotate_points([(x - r, y), (x + r, y)], x, y, angle)
    line2 = rotate_points([(x, y - r), (x, y + r)], x, y, angle)
    arcade.draw_line(line1[0][0], line1[0][1], line1[1][0], line1[1][1], dark, 3)
    arcade.draw_line(line2[0][0], line2[0][1], line2[1][0], line2[1][1], dark, 3)
    arcade.draw_circle_filled(x, y, r / 3, dark)


def draw_wave(x, y, size, angle, color):
    h = size / 2
    dark = theme.darker(color)
    arrow = [(x - h, y - h * 0.7), (x + h, y), (x - h, y + h * 0.7)]
    draw_shape(rotate_points(arrow, x, y, angle), color, dark)


def draw_ufo(x, y, size, angle, color):
    h = size / 2
    dark = theme.darker(color)
    arcade.draw_arc_filled(x, y, size * 0.6, size * 0.8, (200, 230, 255), 0, 180)
    arcade.draw_arc_outline(x, y, size * 0.6, size * 0.8, dark, 0, 180, 3)
    arcade.draw_ellipse_filled(x, y - h * 0.15, size, size * 0.4, color)
    arcade.draw_ellipse_outline(x, y - h * 0.15, size, size * 0.4, dark, 3)
    for k in (-1, 0, 1):
        arcade.draw_circle_filled(x + k * h * 0.5, y - h * 0.15, size * 0.06, dark)


def draw_form(form, x, y, size, angle=0, color=None):
    if color is None:
        color = theme.get_form_color(form)
    if form == "cube":
        draw_cube(x, y, size, angle, color)
    elif form == "ship":
        draw_ship(x, y, size, angle, color)
    elif form == "ball":
        draw_ball(x, y, size, angle, color)
    elif form == "wave":
        draw_wave(x, y, size, angle, color)
    elif form == "ufo":
        draw_ufo(x, y, size, angle, color)
    else:
        draw_cube(x, y, size, angle, (128, 128, 128))
