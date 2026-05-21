import RPi.GPIO as GPIO
import pi_servo_hat
from robot_base import DrivebaseBase, RockerBogieBase, Rover


class DrivebaseRPi(DrivebaseBase):
    def __init__(self):
        self.IN1 = 22
        self.IN2 = 24
        self.IN3 = 17
        self.IN4 = 27
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.IN1, self.IN2, self.IN3, self.IN4], GPIO.OUT)
        self.pwm1 = GPIO.PWM(self.IN1, 1000)
        self.pwm2 = GPIO.PWM(self.IN2, 1000)
        self.pwm3 = GPIO.PWM(self.IN3, 1000)
        self.pwm4 = GPIO.PWM(self.IN4, 1000)
        self.pwm1.start(0)
        self.pwm2.start(0)
        self.pwm3.start(0)
        self.pwm4.start(0)

    def setLeft(self, power):
        if power > 0:
            self.pwm1.ChangeDutyCycle(power * 100)
            self.pwm2.ChangeDutyCycle(0)
        elif power < 0:
            self.pwm1.ChangeDutyCycle(0)
            self.pwm2.ChangeDutyCycle(abs(power) * 100)
        else:
            self.pwm1.ChangeDutyCycle(0)
            self.pwm2.ChangeDutyCycle(0)

    def setRight(self, power):
        if power > 0:
            self.pwm3.ChangeDutyCycle(power * 100)
            self.pwm4.ChangeDutyCycle(0)
        elif power < 0:
            self.pwm3.ChangeDutyCycle(0)
            self.pwm4.ChangeDutyCycle(abs(power) * 100)
        else:
            self.pwm3.ChangeDutyCycle(0)
            self.pwm4.ChangeDutyCycle(0)

    def cleanup(self):
        self.pwm1.stop()
        self.pwm2.stop()
        self.pwm3.stop()
        self.pwm4.stop()
        GPIO.cleanup()


class RockerBogieRPi(RockerBogieBase):
    def __init__(self):
        self.hat = pi_servo_hat.PiServoHat()
        self.hat.restart()

    def setPositions(self, positions):
        for index, pos in enumerate(positions):
            self.hat.move_servo_position(index, pos)


def make_rover() -> Rover:
    return Rover(DrivebaseRPi(), RockerBogieRPi())
