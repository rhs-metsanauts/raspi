import pi_servo_hat
import time

test = pi_servo_hat.PiServoHat()

test.restart()

# Moves servo position to 0 degrees (1ms), Channel 0


#right main, left main, right back, left back
servo_positions = [150, 30, 80, 100]
for index, pos in enumerate(servo_positions):
    test.move_servo_position(index, pos)

print('moved')

time.sleep(10)