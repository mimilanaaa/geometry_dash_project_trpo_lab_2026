"""Бот проверяет, что уровень можно пройти.

Бот играет по тем же правилам, что и игра (core/game_loop.py): раз в кадр (60 FPS)
решает — держать кнопку или отпустить — и перебирает оба варианта сразу для всех
состояний, которые ещё живы. Похожие состояния склеиваются, а если их слишком много,
остаётся равномерная выборка по высоте. Если хоть одно состояние дошло до конца —
уровень проходим.

    python -m generator.bot_check levels/my_level.json [форма]
"""

import bisect
import sys

from core import physics
from core.game_loop import GameSession
from core.player import make_form

STEPS_PER_DECISION = 4      # 240 шагов физики в секунду / 60 решений в секунду
MAX_STATES = 160
BAND = 5                    # px: полоса высоты, в которой хватает двух состояний
WINDOW = physics.BLOCK * 2  # объекты, у которых может поменяться used за одно решение


class BotResult:
    def __init__(self, passed, time, percent, reason=""):
        self.passed = passed
        self.time = time
        self.percent = percent
        self.reason = reason

    def __repr__(self):
        if self.passed:
            return "BotResult(пройден)"
        return f"BotResult(не пройден на {self.time:.2f} с, {self.percent:.0f}%: {self.reason})"


class Bot:
    def __init__(self, level, form="cube", max_states=MAX_STATES):
        self.session = GameSession(level, form)
        self.max_states = max_states
        self.forms = {}

    def form(self, name):
        if name not in self.forms:
            self.forms[name] = make_form(name)
        return self.forms[name]

    def window(self):
        s = self.session
        x = s.player.x
        lo = bisect.bisect_left(s.xs, x - WINDOW)
        hi = bisect.bisect_right(s.xs, x + WINDOW)
        return lo, hi

    def snapshot(self, held):
        s = self.session
        p = s.player
        lo, hi = self.window()
        used = tuple(o.used for o in s.objects[lo:hi])
        return (s.time, p.x, p.y, p.vy, p.angle, p.on_ground, p.form.name, p.gravity,
                s.orb_buffer, held, lo, used)

    def restore(self, snap):
        s = self.session
        p = s.player
        (s.time, p.x, p.y, p.vy, p.angle, p.on_ground, form, p.gravity,
         s.orb_buffer, held, lo, used) = snap
        p.form = self.form(form)
        p.alive = True
        s.state = "playing"
        s.events.clear()
        for obj, flag in zip(s.objects[lo:lo + len(used)], used):
            obj.used = flag
        return held

    def advance(self, snap, hold):
        """Один кадр из состояния snap с кнопкой hold. Возвращает новое состояние или None."""
        s = self.session
        held = self.restore(snap)
        if hold and not held:
            s.press()
        s.holding = hold
        for _ in range(STEPS_PER_DECISION):
            s.step(physics.STEP)
            if s.state != "playing":
                break
        if s.state == "dead":
            return None
        return self.snapshot(hold)

    @staticmethod
    def key(snap):
        _, _, y, vy, _, on_ground, form, gravity, _, held, _, used = snap
        return (round(y), round(vy / 10), on_ground, form, gravity, used)

    def thin(self, states):
        """Оставляет в каждой полосе высоты самое быстрое вверх и самое быстрое вниз состояние.

        Так сохраняется граница всего, что бот может достичь, а середина выбрасывается.
        """
        if len(states) <= self.max_states:
            return states
        bands = {}
        for st in states:
            band = (st[6], st[7], st[5], int(st[2] // BAND))
            low, high = bands.get(band, (st, st))
            if st[3] < low[3]:
                low = st
            if st[3] > high[3]:
                high = st
            bands[band] = (low, high)
        kept = []
        for low, high in bands.values():
            kept.append(low)
            if high is not low:
                kept.append(high)
        if len(kept) > self.max_states:
            kept.sort(key=lambda st: (st[2], st[3]))
            step = len(kept) / self.max_states
            kept = [kept[int(i * step)] for i in range(self.max_states)]
        return kept

    def run(self):
        s = self.session
        frontier = [self.snapshot(False)]
        while True:
            found = {}
            for snap in frontier:
                for hold in (False, True):
                    new = self.advance(snap, hold)
                    if new is None:
                        continue
                    if s.state == "complete":
                        return BotResult(True, s.time, 100.0)
                    k = self.key(new)
                    old = found.get(k)
                    # Отпущенная кнопка не хуже зажатой: в следующем кадре можно и нажать.
                    if old is None or (old[9] and not new[9]):
                        found[k] = new
            if not found:
                t = frontier[0][0]
                return BotResult(False, t, t / s.duration * 100, self.describe(frontier[0]))
            frontier = self.thin(list(found.values()))

    def describe(self, snap):
        """Что рядом с игроком в момент, когда все варианты погибли."""
        self.restore(snap)
        s = self.session
        p = s.player
        lo, hi = self.window()
        kinds = {}
        for obj in s.objects[lo:hi]:
            kinds[obj.kind] = kinds.get(obj.kind, 0) + 1
        near = ", ".join(f"{k}×{n}" for k, n in sorted(kinds.items())) or "пусто"
        grav = "перевёрнутая" if p.gravity < 0 else "обычная"
        return f"форма {p.form.name}, гравитация {grav}, рядом: {near}"


def check_level(level, form="cube", max_states=MAX_STATES):
    return Bot(level, form, max_states).run()


def main():
    from generator.level_format import Level

    if len(sys.argv) < 2:
        print("Использование: python -m generator.bot_check <уровень.json> [форма]")
        sys.exit(1)
    level = Level.from_json(sys.argv[1])
    form = sys.argv[2] if len(sys.argv) > 2 else "cube"
    result = check_level(level, form)
    if result.passed:
        print(f"[+] {level.name}: бот прошёл уровень")
    else:
        print(f"[!] {level.name}: бот не прошёл — {result.time:.2f} с ({result.percent:.0f}%), {result.reason}")
        sys.exit(2)


if __name__ == "__main__":
    main()
