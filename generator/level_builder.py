"""Генератор уровня по битам трека.

Уровень собирается из секций, которые сменяют друг друга по кругу:
    куб → корабль → куб → перевёрнутая гравитация → куб → ...
В секции куба на биты ставятся одиночные, двойные и тройные шипы и блоки,
в секции корабля — ворота из блоков с проходом, который гуляет вверх-вниз,
в перевёрнутой секции куб бежит по потолку, а шипы висят остриём вниз.
Что именно и как часто — задаёт профиль сложности в DIFFICULTIES.

Все паттерны рассчитаны на прыжок ровно в бит: игрок доходит до центра
паттерна через physics.JUMP_LEAD_TIME после бита, на вершине прыжка.
Проверить, что уровень проходим: python -m generator.bot_check <уровень.json>
"""

import random
import sys
import hashlib
from pathlib import Path

from core import physics
from generator.level_format import Level, Obstacle, Portal, ObjectType, FormType, PortalType
from music.beat_detect import analyze_track

SCROLL_SPEED = 500.0          # базовая скорость; у каждой сложности своя, см. DIFFICULTIES
FLOOR_Y = 100.0
BLOCK = physics.BLOCK
CEILING_Y = FLOOR_Y + physics.SHIP_CEILING     # потолок корабля и перевёрнутой гравитации
CELLS = int(physics.SHIP_CEILING // BLOCK)     # клеток между полом и потолком (11)
MIN_SAFE_GAP = 0.45
PORTAL_HEIGHT = 300.0

INTRO = 2.0                   # первые секунды без препятствий
OUTRO = 1.0                   # последние секунды без препятствий
CLEAR_BEFORE_PORTAL = 0.6     # от последнего препятствия до портала
SETTLE_AFTER_PORTAL = 1.0     # от портала до первого препятствия: долететь до пола или потолка
MIN_SPECIAL_BEATS = 8         # короче этого секция корабля или гравитации не ставится

# Вершина прыжка наступает чуть позже, чем игрок доходит до объекта бита (JUMP_LEAD_TIME).
# Паттерны куба сдвигаются на эту разницу, чтобы прыжок ровно в бит был в середине окна.
APEX_SHIFT = physics.CUBE_JUMP_SPEED / physics.CUBE_GRAVITY - physics.JUMP_LEAD_TIME

# Паттерны куба: (сдвиг по x в клетках от бита, тип, высота в клетках над опорой).
# Блок не начинается раньше чем за полклетки до бита — иначе прыжок в бит врезается в его бок.
PATTERNS = {
    "spike":          [(0, "spike", 0)],
    "spike2":         [(-0.5, "spike", 0), (0.5, "spike", 0)],
    "spike3":         [(-1, "spike", 0), (0, "spike", 0), (1, "spike", 0)],
    "block":          [(0, "block", 0)],
    "block2":         [(0, "block", 0), (1, "block", 0)],
    "block_spike":    [(0, "block", 0), (1, "spike", 0)],
    "spike_block":    [(-0.5, "spike", 0), (0.5, "block", 0)],
    "spike_on_block": [(0, "block", 0), (0, "spike", 1)],
}

# После паттернов с блоками игрок может приземлиться на блок и сойти с него позже,
# поэтому следующий паттерн ставится не раньше чем через столько секунд.
RECOVERY = {
    "block": 0.6,
    "block2": 0.7,
    "block_spike": 0.65,
    "spike_block": 0.65,
    "spike_on_block": 0.6,
}

# Профили сложности.
#   speed     — скорость прокрутки, px/с. Чем быстрее, тем шире окно у тройного шипа:
#               при 500 — около 20 мс (почти нереально), при 550 — около 45, при 600 — около 80
#   step      — препятствие ставится на каждый step-й бит
#   min_gap   — но не чаще, чем раз в столько секунд
#   cube      — веса паттернов в обычной секции куба
#   upside    — веса паттернов в перевёрнутой секции (шипы на потолке)
#   ship      — ворота корабля: высота прохода в клетках, на сколько клеток проход
#               может сместиться между воротами, шаг по битам и доля ворот с шипами
#   lengths   — длина секций в битах
DIFFICULTIES = {
    "easy": {
        "speed": 500.0,
        "step": 2,
        "min_gap": 0.6,
        "cube": {"spike": 40, "spike2": 30, "block": 15, "block2": 15},
        "upside": {"spike": 60, "spike2": 25, "block": 15},
        "ship": {"gap": 6, "shift": 1, "step": 2, "min_gap": 0.6, "spikes": 0.0},
        "lengths": {"cube": 24, "ship": 12, "upside": 12},
    },
    "normal": {
        "speed": 550.0,
        "step": 1,
        "min_gap": 0.5,
        "cube": {"spike": 20, "spike2": 35, "spike3": 6, "block": 9, "block2": 10,
                 "block_spike": 10, "spike_block": 10},
        "upside": {"spike": 30, "spike2": 40, "spike3": 5, "block": 10, "block_spike": 15},
        "ship": {"gap": 4, "shift": 2, "step": 1, "min_gap": 0.45, "spikes": 0.0},
        "lengths": {"cube": 16, "ship": 16, "upside": 12},
    },
    "hard": {
        "speed": 600.0,
        "step": 1,
        "min_gap": MIN_SAFE_GAP,
        "cube": {"spike": 5, "spike2": 25, "spike3": 30, "block2": 10,
                 "block_spike": 10, "spike_block": 10, "spike_on_block": 10},
        "upside": {"spike2": 35, "spike3": 35, "block_spike": 15, "spike_on_block": 15},
        "ship": {"gap": 3, "shift": 2, "step": 1, "min_gap": 0.4, "spikes": 0.5},
        "lengths": {"cube": 12, "ship": 16, "upside": 16},
    },
}

SECTION_ORDER = ["cube", "ship", "cube", "upside"]
SECTION_NAMES = {"cube": "куб", "ship": "корабль", "upside": "перевёрнутая гравитация"}


def get_file_hash(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def plan_sections(beats, cfg):
    """Делит биты на секции по SECTION_ORDER; хвост, где секция не помещается, отдаётся кубу."""
    sections = []
    i = 0
    k = 0
    while i < len(beats):
        kind = SECTION_ORDER[k % len(SECTION_ORDER)]
        n = cfg["lengths"][kind]
        chunk = beats[i:i + n]
        if kind != "cube" and len(chunk) < MIN_SPECIAL_BEATS:
            kind = "cube"
        if sections and sections[-1][0] == kind:
            sections[-1][1].extend(chunk)
        else:
            sections.append((kind, list(chunk)))
        i += n
        k += 1
    return sections


class LevelPlan:
    """Расставляет объекты секция за секцией и помнит, где игрок и что было последним."""

    def __init__(self, cfg, rng):
        self.cfg = cfg
        self.rng = rng
        self.speed = cfg["speed"]
        self.obstacles = []
        self.portals = []
        self.mode = "cube"          # cube / ship / upside
        self.last = -10.0           # бит последнего препятствия
        self.free_from = INTRO      # раньше этого времени препятствия не ставим
        self.gate_lo = 1            # нижняя клетка прохода у прошлых ворот корабля

    # --- объекты ---

    def add(self, kind, x, y, flip=False):
        props = {"flip": True} if flip else {}
        self.obstacles.append(Obstacle(x=x, y=y, time=x / self.speed,
                                       type=ObjectType(kind), properties=props))

    def add_portal(self, time, portal_type, form=FormType.CUBE):
        if portal_type == PortalType.GRAVITY_NORMAL:
            y = CEILING_Y - BLOCK * 2.4      # игрок подходит к нему по потолку
        elif portal_type == PortalType.GRAVITY_FLIP:
            y = FLOOR_Y
        else:
            y = PORTAL_HEIGHT
        self.portals.append(Portal(x=time * self.speed, y=y, time=time,
                                   target_form=form, type=portal_type))

    def pick(self, weights):
        names = list(weights)
        return self.rng.choices(names, weights=[weights[n] for n in names])[0]

    # --- переходы ---

    def switch_to(self, kind, beats):
        """Ставит портал на первый бит, до которого успели закончиться препятствия.

        Возвращает биты секции после портала.
        """
        for i, beat in enumerate(beats):
            if beat - self.last < CLEAR_BEFORE_PORTAL or beat < self.free_from:
                continue
            if self.mode == "ship":
                self.add_portal(beat, PortalType.FORM, FormType.CUBE)
            elif self.mode == "upside":
                self.add_portal(beat, PortalType.GRAVITY_NORMAL)
            if kind == "ship":
                self.add_portal(beat, PortalType.FORM, FormType.SHIP)
                self.gate_lo = 1
            elif kind == "upside":
                self.add_portal(beat, PortalType.GRAVITY_FLIP)
            self.mode = kind
            self.free_from = beat + SETTLE_AFTER_PORTAL
            print(f"  [+] Портал: {SECTION_NAMES[kind]} на {beat:.2f} сек.")
            return beats[i + 1:]
        return []

    # --- секции ---

    def section(self, kind, beats):
        if kind != self.mode:
            if self.mode != "cube" and kind != "cube":
                beats = self.switch_to("cube", beats)
            beats = self.switch_to(kind, beats)
        if kind == "ship":
            self.ship_section(beats)
        else:
            self.cube_section(beats, upside=(kind == "upside"))

    def cube_section(self, beats, upside):
        cfg = self.cfg
        weights = cfg["upside"] if upside else cfg["cube"]
        gap = cfg["min_gap"]
        for i, beat in enumerate(beats):
            if i % cfg["step"] != 0 or beat < self.free_from or beat - self.last < gap:
                continue
            name = self.pick(weights)
            x0 = (beat + APEX_SHIFT) * self.speed
            for dx, kind, dy in PATTERNS[name]:
                if upside:
                    self.add(kind, x0 + dx * BLOCK, CEILING_Y - BLOCK * (dy + 1), flip=(kind == "spike"))
                else:
                    self.add(kind, x0 + dx * BLOCK, FLOOR_Y + BLOCK * dy)
            self.last = beat
            gap = max(cfg["min_gap"], RECOVERY.get(name, 0.0))

    def ship_section(self, beats):
        """Ворота: колонна блоков от пола и от потолка, между ними проход высотой gap клеток."""
        ship = self.cfg["ship"]
        size = ship["gap"]
        top_lo = CELLS - size - 1          # хотя бы по блоку сверху и снизу
        gate = 0
        for i, beat in enumerate(beats):
            if i % ship["step"] != 0 or beat < self.free_from or beat - self.last < ship["min_gap"]:
                continue
            if gate == 0:
                lo = 1                     # корабль влетает с пола
            else:
                lo = self.gate_lo + self.rng.randint(-ship["shift"], ship["shift"])
            lo = max(1, min(top_lo, lo))
            x = beat * self.speed
            for cell in range(lo):
                self.add("block", x, FLOOR_Y + cell * BLOCK)
            for cell in range(lo + size, CELLS):
                self.add("block", x, FLOOR_Y + cell * BLOCK)
            if gate > 0 and self.rng.random() < ship["spikes"]:
                if self.rng.random() < 0.5:
                    self.add("spike", x, FLOOR_Y + lo * BLOCK)                          # торчит из нижней колонны
                else:
                    self.add("spike", x, FLOOR_Y + (lo + size - 1) * BLOCK, flip=True)  # висит на верхней
            self.gate_lo = lo
            self.last = beat
            gate += 1


def build_level(beats, bpm, duration, seed=42, difficulty="normal", name="Level",
                track_name="", track_hash=""):
    """Строит уровень по готовым битам. Без анализа аудио — удобно для проверок."""
    cfg = DIFFICULTIES.get(difficulty, DIFFICULTIES["normal"])
    plan = LevelPlan(cfg, random.Random(seed))
    usable = [b for b in beats if INTRO <= b <= duration - OUTRO]
    for kind, section_beats in plan_sections(usable, cfg):
        plan.section(kind, section_beats)
    plan.obstacles.sort(key=lambda o: o.x)
    plan.portals.sort(key=lambda p: p.x)
    return Level(
        name=name,
        bpm=bpm,
        duration=duration,
        author="Automatic Generator",
        track_name=track_name,
        track_hash=track_hash,
        obstacles=plan.obstacles,
        portals=plan.portals,
    )


def generate_level(audio_path: str, seed: int = 42, difficulty: str = "normal") -> Level:
    print(f"[*] Запуск анализа аудиофайла: {audio_path}")
    try:
        audio_data = analyze_track(audio_path)
    except Exception as e:
        raise RuntimeError(f"Не удалось обработать аудиофайл {audio_path}: {e}") from e

    beats = audio_data["beat_times"]
    bpm = audio_data["bpm"]
    duration = audio_data["duration"]

    print(f"[*] Анализ завершен. BPM: {bpm:.2f}, Всего битов: {len(beats)}")

    return build_level(
        beats, bpm, duration, seed=seed, difficulty=difficulty,
        name=f"Auto_{Path(audio_path).stem}_{difficulty}",
        track_name=audio_data["file_name"],
        track_hash=get_file_hash(audio_path),
    )


def save_level_to_file(level: Level, output_dir: str = "levels"):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    safe_name = "".join([c for c in level.name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    filename = out_path / f"{safe_name}.json"

    level.to_json(str(filename))
    print(f"\n[+] Уровень успешно сохранен: {filename}")
    print(f"    Всего препятствий: {len(level.obstacles)}")
    print(f"    Всего порталов: {len(level.portals)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Ошибка: Не указан путь к аудиофайлу.")
        print("Использование: python -m generator.level_builder <путь_к_музыке.mp3> [сложность]")
        sys.exit(1)

    audio_path = sys.argv[1]
    diff = sys.argv[2] if len(sys.argv) > 2 else "normal"

    try:
        generated_level = generate_level(audio_path, seed=42, difficulty=diff)
        save_level_to_file(generated_level)
    except RuntimeError as e:
        print(f"[!] Ошибка: {e}")
        sys.exit(1)
