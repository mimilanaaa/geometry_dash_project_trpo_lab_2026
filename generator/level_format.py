import json
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import List, Dict, Any

class FormType(str, Enum):
    CUBE = "cube"
    SHIP = "ship"
    BALL = "ball"
    WAVE = "wave"
    UFO = "ufo"
    ROBOT = "robot"
    SPIDER = "spider"

class PortalType(str, Enum):
    FORM = "form"                       # меняет форму на target_form
    GRAVITY_FLIP = "gravity_flip"       # жёлтый: гравитация вверх, куб бежит по потолку
    GRAVITY_NORMAL = "gravity_normal"   # синий: обычная гравитация

class ObjectType(str, Enum):
    SPIKE = "spike"
    BLOCK = "block"
    ORB = "orb"
    PAD = "pad"
    PORTAL = "portal"

@dataclass
class GameObject:

    x: float
    y: float
    time: float

@dataclass
class Obstacle(GameObject):
    type: ObjectType = ObjectType.SPIKE
    # {"flip": True} — шип висит на потолке остриём вниз (для перевёрнутой гравитации)
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Portal(GameObject):
    target_form: FormType = FormType.CUBE
    speed_multiplier: float = 1.0 
    type: PortalType = PortalType.FORM   # у гравитационных порталов target_form не используется

@dataclass
class Level:
    name: str
    bpm: float
    duration: float
    author: str = "Musically Geometry Generator"
    
    track_name: str = ""
    track_hash: str = ""
    
    obstacles: List[Obstacle] = field(default_factory=list)
    portals: List[Portal] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "bpm": self.bpm,
            "duration": self.duration,
            "author": self.author,
            "track_name": self.track_name,
            "track_hash": self.track_hash,
            "obstacles": [
                {
                    **asdict(obs),
                    "type": obs.type.value
                } for obs in self.obstacles
            ],
            "portals": [
                {
                    **asdict(portal),
                    "target_form": portal.target_form.value,
                    "type": portal.type.value
                } for portal in self.portals
            ]
        }

    def to_json(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict) -> 'Level':
        obstacles = []
        for obs_data in data.get("obstacles", []):
            obs_data_copy = obs_data.copy()
            obs_data_copy["type"] = ObjectType(obs_data_copy["type"])
            obstacles.append(Obstacle(**obs_data_copy))

        portals = []
        for port_data in data.get("portals", []):
            port_data_copy = port_data.copy()
            port_data_copy["target_form"] = FormType(port_data_copy["target_form"])
            port_data_copy["type"] = PortalType(port_data_copy.get("type", "form"))
            portals.append(Portal(**port_data_copy))

        return cls(
            name=data["name"],
            bpm=data["bpm"],
            duration=data["duration"],
            author=data.get("author", "Unknown"),
            track_name=data.get("track_name", ""),
            track_hash=data.get("track_hash", ""),
            obstacles=obstacles,
            portals=portals
        )

    @classmethod
    def from_json(cls, filepath: str) -> 'Level':
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return cls.from_dict(data)


if __name__ == "__main__":
    test_level = Level(
        name="Test Level 1",
        bpm=128.0,
        duration=60.0,
        track_name="Test Track",
        track_hash="abc123hash"
    )
    
    test_level.obstacles.append(
        Obstacle(x=500.0, y=0.0, time=1.0, type=ObjectType.SPIKE)
    )
    
    test_level.portals.append(
        Portal(x=5000.0, y=300.0, time=10.0, target_form=FormType.SHIP)
    )

    test_level.to_json("test_level.json")
    print("Тестовый уровень сохранен в test_level.json")

    loaded_level = Level.from_json("test_level.json")
    print(f"Загружен уровень: {loaded_level.name}, BPM: {loaded_level.bpm}")
    print(f"Шипов: {len(loaded_level.obstacles)}, Порталов: {len(loaded_level.portals)}")