import sys
import arcade
from ui import theme
from ui import object_view
from generator.level_format import Level, Obstacle, Portal, ObjectType, FormType

WIDTH = 1280
HEIGHT = 720
GROUND = 160
SIZE = 50
LEFT_PAD = 80


def make_demo_level():
    level = Level(name="Демо-уровень", bpm=120.0, duration=20.0, track_name="Без трека")
    beat = 60 / level.bpm
    speed = 300
    kinds = [ObjectType.SPIKE, ObjectType.BLOCK, ObjectType.SPIKE, ObjectType.PAD,
             ObjectType.SPIKE, ObjectType.ORB, ObjectType.BLOCK, ObjectType.SPIKE]
    for i in range(1, 17):
        time = i * 2 * beat
        kind = kinds[i % len(kinds)]
        y = 120 if kind == ObjectType.ORB else 0
        level.obstacles.append(Obstacle(x=time * speed, y=y, time=time, type=kind))
    level.portals.append(Portal(x=8.5 * speed, y=0, time=8.5, target_form=FormType.SHIP))
    level.portals.append(Portal(x=12.5 * speed, y=0, time=12.5, target_form=FormType.CUBE,
                                speed_multiplier=1.5))
    return level


def value_of(item):
    if hasattr(item, "value"):
        return item.value
    return str(item)


class LevelViewerView(arcade.View):
    def __init__(self, level, on_back=None):
        super().__init__()
        self.level = level
        self.on_back = on_back
        self.scroll = 0
        self.floor = self.find_floor()
        self.zoom = self.find_zoom()
        self.speed = self.find_speed()
        self.length = self.find_length()

    def find_floor(self):
        if len(self.level.obstacles) == 0:
            return 0
        return min(obs.y for obs in self.level.obstacles)

    def find_zoom(self):
        top = SIZE
        for obj in self.level.obstacles:
            top = max(top, obj.y - self.floor + SIZE)
        for obj in self.level.portals:
            top = max(top, obj.y - self.floor + SIZE * 2.4)
        space = HEIGHT - 130 - GROUND - 20
        zoom = 1.0
        while top * zoom > space and zoom > 0.25:
            zoom -= 0.25
        return zoom

    def to_screen_y(self, y):
        return GROUND + (y - self.floor) * self.zoom

    def find_speed(self):
        for obj in self.level.obstacles + self.level.portals:
            if obj.time > 0 and obj.x > 0:
                return obj.x / obj.time
        return 300

    def find_length(self):
        last = self.level.duration * self.speed
        for obj in self.level.obstacles + self.level.portals:
            last = max(last, obj.x)
        return last

    def to_screen(self, x):
        return LEFT_PAD + (x - self.scroll) * self.zoom

    def draw_beats(self):
        t = theme.get_theme()
        if self.level.bpm <= 0:
            return
        beat = 60 / self.level.bpm
        number = 0
        time = 0
        while time <= self.level.duration:
            sx = self.to_screen(time * self.speed)
            if 0 <= sx <= self.window.width:
                strong = number % 4 == 0
                color = t["text_soft"] if strong else t["bar_back"]
                arcade.draw_line(sx, GROUND, sx, self.window.height - 130, color, 2 if strong else 1)
                if strong:
                    arcade.draw_text(str(round(time, 1)) + " с", sx + 4, GROUND - 24, t["text_soft"], 11,
                                     font_name=theme.FONT, bold=True)
            number += 1
            time = number * beat

    def draw_objects(self):
        size = SIZE * self.zoom
        for obs in self.level.obstacles:
            sx = self.to_screen(obs.x)
            if -size <= sx <= self.window.width + size:
                object_view.draw_object(value_of(obs.type), sx, self.to_screen_y(obs.y), size,
                                        obs.properties)
        for portal in self.level.portals:
            sx = self.to_screen(portal.x)
            if -size <= sx <= self.window.width + size:
                object_view.draw_portal(sx, self.to_screen_y(portal.y), size,
                                        value_of(portal.target_form), portal.speed_multiplier)

    def draw_info(self):
        t = theme.get_theme()
        h = self.window.height
        arcade.draw_lrbt_rectangle_filled(0, self.window.width, h - 110, h, t["background"])
        arcade.draw_polygon_filled([(0, h), (160, h), (90, h - 70), (0, h - 70)], t["accent"])
        arcade.draw_text(self.level.name.upper(), 190, h - 50, t["text"], 26, font_name=theme.FONT, bold=True)
        info = ("BPM " + str(round(self.level.bpm)) + "   ·   " + str(round(self.level.duration)) + " с"
                + "   ·   препятствий: " + str(len(self.level.obstacles))
                + "   ·   порталов: " + str(len(self.level.portals))
                + "   ·   трек: " + (self.level.track_name or "—"))
        arcade.draw_text(info, 192, h - 82, t["text_soft"], 13, font_name=theme.FONT, bold=True)

        left = 190
        right = self.window.width - 40
        y = h - 100
        arcade.draw_line(left, y, right, y, t["bar_back"], 4)
        if self.length > 0:
            view_width = self.window.width / self.zoom
            a = left + (right - left) * self.scroll / self.length
            b = left + (right - left) * min(1, (self.scroll + view_width) / self.length)
            arcade.draw_line(a, y, b, y, t["accent"], 4)

        arcade.draw_text("← → прокрутка (Shift — быстрее)   + − масштаб   Home — в начало   T — тема   Esc — выход",
                         24, 20, t["text_soft"], 12, font_name=theme.FONT, bold=True)

    def on_draw(self):
        self.clear(theme.get_theme()["background"])
        object_view.draw_ground(self.window.width, GROUND)
        self.draw_beats()
        self.draw_objects()
        self.draw_info()

    def scroll_by(self, dx):
        self.scroll = max(0, min(self.length, self.scroll + dx))

    def on_key_press(self, key, modifiers):
        step = 400 if modifiers & arcade.key.MOD_SHIFT else 100
        if key == arcade.key.RIGHT:
            self.scroll_by(step / self.zoom)
        elif key == arcade.key.LEFT:
            self.scroll_by(-step / self.zoom)
        elif key == arcade.key.HOME:
            self.scroll = 0
        elif key in (arcade.key.PLUS, arcade.key.EQUAL, arcade.key.NUM_ADD):
            self.zoom = min(2.0, self.zoom + 0.25)
        elif key in (arcade.key.MINUS, arcade.key.NUM_SUBTRACT):
            self.zoom = max(0.25, self.zoom - 0.25)
        elif key == arcade.key.T:
            theme.toggle_theme()
        elif key == arcade.key.ESCAPE:
            if self.on_back:
                self.on_back()
            else:
                arcade.exit()

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.scroll_by(-(scroll_y + scroll_x) * 60 / self.zoom)


def main():
    if len(sys.argv) > 1:
        level = Level.from_json(sys.argv[1])
    else:
        level = make_demo_level()
    window = arcade.Window(WIDTH, HEIGHT, "Musically Geometry — просмотр уровня")
    window.show_view(LevelViewerView(level))
    arcade.run()


if __name__ == "__main__":
    main()
