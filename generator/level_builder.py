import random
import sys
from pathlib import Path

from generator.level_format import Level, Obstacle, Portal, ObjectType, FormType
from music.beat_detect import analyze_track

SCROLL_SPEED = 500.0
FLOOR_Y = 100.0
MIN_SAFE_GAP = 0.45
PORTAL_HEIGHT = 300.0

