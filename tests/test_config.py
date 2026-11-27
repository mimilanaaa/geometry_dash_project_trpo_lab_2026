import config


def test_cube_lands_before_next_obstacle():
    assert config.CUBE_AIR_TIME < config.MIN_SAFE_GAP


def test_cube_jumps_higher_than_spike():
    assert config.CUBE_JUMP_HEIGHT > config.OBJECT_SIZE * 1.5


def test_cube_flies_over_spike():
    distance = config.SCROLL_SPEED * config.CUBE_AIR_TIME
    assert distance > config.OBJECT_SIZE + config.PLAYER_SIZE


def test_jump_formula_gives_right_height():
    g = config.CUBE_GRAVITY
    v = config.CUBE_JUMP_SPEED
    height = v * v / (2 * g)
    assert abs(height - config.CUBE_JUMP_HEIGHT) < 0.01


def test_jump_formula_gives_right_air_time():
    air_time = 2 * config.CUBE_JUMP_SPEED / config.CUBE_GRAVITY
    assert abs(air_time - config.CUBE_AIR_TIME) < 0.001


def test_cube_turns_half_circle_in_air():
    angle = config.CUBE_ROTATE_SPEED * config.CUBE_AIR_TIME
    assert abs(angle - 180) < 0.01


def test_ship_has_room_between_floor_and_ceiling():
    room = config.CEILING_Y - (config.FLOOR_Y + config.OBJECT_SIZE)
    assert room >= config.PLAYER_SIZE * 4


def test_ship_can_rise():
    assert config.SHIP_THRUST > config.SHIP_GRAVITY


def test_portal_between_floor_and_ceiling():
    assert config.FLOOR_Y < config.PORTAL_HEIGHT < config.CEILING_Y


def test_player_fits_on_screen():
    assert 0 < config.PLAYER_X < config.SCREEN_WIDTH
    assert config.CEILING_Y + config.OBJECT_SIZE <= config.SCREEN_HEIGHT


def test_difficulties():
    steps = config.DIFFICULTY_STEPS
    assert steps["easy"] > steps["normal"] > steps["hard"] >= 1


def test_track_limits():
    assert config.MIN_TRACK_SECONDS < config.MAX_TRACK_SECONDS
    assert ".mp3" in config.AUDIO_FORMATS
