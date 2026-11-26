import librosa
import numpy as np
from pathlib import Path

def analyze_track(file_path: str) -> dict:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    
    y, sr = librosa.load(str(path), sr=None)
    
    duration = librosa.get_duration(y=y, sr=sr)
    
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    return {
        "bpm": float(np.atleast_1d(tempo)[0]),
        "beat_times": beat_times.tolist() if hasattr(beat_times, 'tolist') else list(beat_times),
        "duration": float(duration),
        "file_name": path.name,
        "sample_rate": int(sr),
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Использование: python beat_detect.py <путь_к_аудиофайлу>")
        sys.exit(1)
    
    result = analyze_track(sys.argv[1])
    print(f"Файл: {result['file_name']}")
    print(f"BPM: {result['bpm']:.2f}")
    print(f"Длительность: {result['duration']:.2f} сек")
    print(f"Найдено битов: {len(result['beat_times'])}")
    print(f"Первые 10 битов (сек): {[round(t, 2) for t in result['beat_times'][:10]]}")