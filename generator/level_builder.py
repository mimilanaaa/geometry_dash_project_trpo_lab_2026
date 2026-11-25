import random
import sys
import hashlib
from pathlib import Path

from generator.level_format import Level, Obstacle, Portal, ObjectType, FormType
from music.beat_detect import analyze_track

SCROLL_SPEED = 500.0
FLOOR_Y = 100.0
MIN_SAFE_GAP = 0.45
PORTAL_HEIGHT = 300.0

def get_file_hash(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_level(audio_path: str, seed: int = 42, difficulty: str = "normal") -> Level:
    random.seed(seed)
    
    print(f"[*] Запуск анализа аудиофайла: {audio_path}")
    try:
        audio_data = analyze_track(audio_path)
    except Exception as e:
        raise RuntimeError(f"Не удалось обработать аудиофайл {audio_path}: {e}") from e

    beats = audio_data["beat_times"]
    bpm = audio_data["bpm"]
    duration = audio_data["duration"]
    
    print(f"[*] Анализ завершен. BPM: {bpm:.2f}, Всего битов: {len(beats)}")

    obstacles = []
    portals = []
    
    if difficulty == "easy":
        step = 4
    elif difficulty == "hard":
        step = 1
    else:
        step = 2

    last_obstacle_time = -10.0
    last_form = FormType.CUBE
    portal_cooldown = 0.0

    for i, beat_time in enumerate(beats):
        if beat_time < 2.0:
            continue

        if i % step != 0:
            continue

        if (beat_time - last_obstacle_time) < MIN_SAFE_GAP:
            continue

        x_pos = beat_time * SCROLL_SPEED

        if last_form == FormType.CUBE:
            obs_type = ObjectType.SPIKE if random.random() < 0.8 else ObjectType.BLOCK
            obstacles.append(
                Obstacle(x=x_pos, y=FLOOR_Y, time=beat_time, type=obs_type)
            )
        elif last_form == FormType.SHIP:
            obstacles.append(
                Obstacle(x=x_pos, y=FLOOR_Y, time=beat_time, type=ObjectType.SPIKE)
            )
            obstacles.append(
                Obstacle(x=x_pos, y=600.0, time=beat_time, type=ObjectType.BLOCK)
            )

        last_obstacle_time = beat_time

        if beat_time > portal_cooldown:
            if len(obstacles) > 0 and len(obstacles) % 40 == 0:
                new_form = FormType.SHIP if last_form == FormType.CUBE else FormType.CUBE
                portal_time = beat_time + 0.5
                
                portals.append(
                    Portal(
                        x=portal_time * SCROLL_SPEED,
                        y=PORTAL_HEIGHT,
                        time=portal_time,
                        target_form=new_form
                    )
                )
                last_form = new_form
                portal_cooldown = portal_time + 10.0 
                print(f"  [+] Добавлен портал в {new_form.value} на {portal_time:.2f} сек.")

    track_hash = get_file_hash(audio_path)

    level_name = f"Auto_{Path(audio_path).stem}_{difficulty}"
    level = Level(
        name=level_name,
        bpm=bpm,
        duration=duration,
        author="Automatic Generator",
        track_name=audio_data["file_name"],
        track_hash=track_hash,
        obstacles=obstacles,
        portals=portals
    )
    
    return level

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