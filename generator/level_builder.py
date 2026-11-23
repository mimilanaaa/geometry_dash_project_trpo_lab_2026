import random
import sys
from pathlib import Path

from generator.level_format import Level, Obstacle, Portal, ObjectType, FormType
from music.beat_detect import analyze_track

SCROLL_SPEED = 500.0
FLOOR_Y = 100.0
MIN_SAFE_GAP = 0.45
PORTAL_HEIGHT = 300.0

def generate_level(audio_path: str, seed: int = 42, difficulty: str = "normal") -> Level:
    random.seed(seed)
    
    print(f"[*] Запуск анализа аудиофайла: {audio_path}")
    try:
        audio_data = analyze_track(audio_path)
    except Exception as e:
        print(f"[!] Ошибка при чтении файла: {e}")
        sys.exit(1)

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

    level_name = f"Auto_{Path(audio_path).stem}_{difficulty}"
    level = Level(
        name=level_name,
        bpm=bpm,
        duration=duration,
        author="Automatic Generator",
        track_name=audio_data["file_name"],
        track_hash="hash_" + str(abs(hash(audio_data["file_name"]))),
        obstacles=obstacles,
        portals=portals
    )
    
    return level

