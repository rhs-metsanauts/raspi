import RPi.GPIO as GPIO
import time
from enum import Enum

class MotorDirection(Enum):
    """Enum for motor rotation directions"""
    FORWARD = 1
    BACKWARD = 2
    STOPPED = 0

class Motor:
    """Represents a single DC motor controlled by two GPIO pins"""
    
    def __init__(self, pin1, pin2, name="Motor"):
        self.pin1 = pin1
        self.pin2 = pin2
        self.name = name
        
    def set_direction(self, direction):
        """Set the motor direction"""
        if direction == MotorDirection.FORWARD:
            GPIO.output(self.pin1, GPIO.LOW)
            GPIO.output(self.pin2, GPIO.HIGH)
        elif direction == MotorDirection.BACKWARD:
            GPIO.output(self.pin1, GPIO.HIGH)
            GPIO.output(self.pin2, GPIO.LOW)
        else:  # STOPPED
            GPIO.output(self.pin1, GPIO.LOW)
            GPIO.output(self.pin2, GPIO.LOW)

class RobotController:
    """Main robot controller managing two motors"""
    
    # GPIO Pin Configuration
    LEFT_MOTOR_PIN1 = 17
    LEFT_MOTOR_PIN2 = 27
    RIGHT_MOTOR_PIN1 = 22
    RIGHT_MOTOR_PIN2 = 24
    
    def __init__(self):
        self.left_motor = Motor(self.LEFT_MOTOR_PIN1, self.LEFT_MOTOR_PIN2, "Left Motor")
        self.right_motor = Motor(self.RIGHT_MOTOR_PIN1, self.RIGHT_MOTOR_PIN2, "Right Motor")
        self._initialize_gpio()
        
    def _initialize_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup all motor pins as outputs
        for motor in [self.left_motor, self.right_motor]:
            GPIO.setup(motor.pin1, GPIO.OUT)
            GPIO.setup(motor.pin2, GPIO.OUT)
            
    def stop(self):
        """Stop both motors"""
        self.left_motor.set_direction(MotorDirection.STOPPED)
        self.right_motor.set_direction(MotorDirection.STOPPED)
        
    def forward(self, duration):
        """Move forward for specified duration"""
        print(f"Moving forward for {duration}s")
        self.left_motor.set_direction(MotorDirection.FORWARD)
        self.right_motor.set_direction(MotorDirection.FORWARD)
        time.sleep(duration)
        self.stop()
        
    def reverse(self, duration):
        """Move backward for specified duration"""
        print(f"Moving backward for {duration}s")
        self.left_motor.set_direction(MotorDirection.BACKWARD)
        self.right_motor.set_direction(MotorDirection.BACKWARD)
        time.sleep(duration)
        self.stop()
        
    def turn_left(self, duration):
        """Turn left for specified duration"""
        print(f"Turning left for {duration}s")
        self.left_motor.set_direction(MotorDirection.BACKWARD)
        self.right_motor.set_direction(MotorDirection.FORWARD)
        time.sleep(duration)
        self.stop()
        
    def turn_right(self, duration):
        """Turn right for specified duration"""
        print(f"Turning right for {duration}s")
        self.left_motor.set_direction(MotorDirection.FORWARD)
        self.right_motor.set_direction(MotorDirection.BACKWARD)
        time.sleep(duration)
        self.stop()
        
    def execute_sequence(self, commands):
        """
        Execute a sequence of commands
        Commands format: [(action, duration, pause_after), ...]
        """
        for action, duration, pause_after in commands:
            action(duration)
            if pause_after > 0:
                time.sleep(pause_after)
                
    def cleanup(self):
        """Clean up GPIO resources"""
        self.stop()
        GPIO.cleanup()
        print("GPIO cleanup complete")

def main():
    """Main program execution"""
    # Configuration variables
    MOVE_DURATION = 3
    TURN_DURATION = 3
    PAUSE_BETWEEN_MOVES = 1
    INITIAL_DELAY = 3
    
    # Create robot controller
    robot = RobotController()
    
    try:
        # Initial delay
        print(f"Starting in {INITIAL_DELAY} seconds...")
        time.sleep(INITIAL_DELAY)
        
        robot.forward(10)

        
        print("Sequence complete!")
        
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        robot.cleanup()

if __name__ == "__main__":
    main()