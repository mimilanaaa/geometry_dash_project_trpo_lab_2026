SWISS = {
    "name": "swiss",
    "background": (245, 243, 238),
    "panel": (255, 255, 255),
    "text": (17, 17, 17),
    "text_soft": (110, 110, 110),
    "accent": (225, 29, 42),
    "line": (17, 17, 17),
    "bar_back": (220, 218, 212),
    "locked": (190, 190, 190),
}

NOIR = {
    "name": "noir",
    "background": (14, 14, 16),
    "panel": (28, 28, 32),
    "text": (240, 236, 226),
    "text_soft": (150, 146, 138),
    "accent": (212, 175, 55),
    "line": (240, 236, 226),
    "bar_back": (50, 50, 56),
    "locked": (80, 80, 86),
}

FORM_COLORS = {
    "cube": (255, 140, 0),
    "ship": (40, 110, 255),
    "ball": (230, 40, 40),
    "wave": (0, 200, 160),
    "ufo": (160, 80, 230),
}

FORM_NAMES = {
    "cube": "Куб",
    "ship": "Корабль",
    "ball": "Шар",
    "wave": "Волна",
    "ufo": "НЛО",
}

FORM_ORDER = ["cube", "ship", "ball", "wave", "ufo"]

FIRST_VERSION_FORMS = ["cube", "ship"]

FONT = "Arial"

current = SWISS


def get_theme():
    return current


def set_theme(name):
    global current
    if name == "noir":
        current = NOIR
    else:
        current = SWISS


def toggle_theme():
    if current["name"] == "swiss":
        set_theme("noir")
    else:
        set_theme("swiss")


def get_form_color(form):
    return FORM_COLORS.get(form, (128, 128, 128))


def darker(color, k=0.6):
    return (int(color[0] * k), int(color[1] * k), int(color[2] * k))
