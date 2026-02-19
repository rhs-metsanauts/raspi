from Robot import *

rover = Rover()

rover.setup_sun_position()

THRESHOLD = 0

for _ in range(15):
    rover.turn_left(0.5, 0.2)
    light = rover.read_light_level()
    print(f"Light level: {light}")
    if light < THRESHOLD:
        print("Facing the sun!")
        break