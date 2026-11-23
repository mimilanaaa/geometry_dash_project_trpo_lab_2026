import json
import os
from ui import theme

FOLDER = os.path.join(os.path.expanduser("~"), ".musically_geometry")
FILE = os.path.join(FOLDER, "settings.json")

values = {
    "theme": "swiss",
    "music_volume": 80,
    "sfx_volume": 80,
}


def load():
    if os.path.exists(FILE):
        try:
            with open(FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key in values:
                if key in data:
                    values[key] = data[key]
        except Exception:
            pass
    theme.set_theme(values["theme"])


def save():
    values["theme"] = theme.get_theme()["name"]
    try:
        os.makedirs(FOLDER, exist_ok=True)
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(values, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


def change_volume(key, step):
    values[key] = max(0, min(100, values[key] + step))
