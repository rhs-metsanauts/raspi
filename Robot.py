import pi_servo_hat
import RPi.GPIO as GPIO
import time

class RockerBogie:
    def __init__(self):
        self.hat = pi_servo_hat.PiServoHat()
        self.hat.restart()
    
    def setPositions(self, positions):
        for index, pos in enumerate(positions):
            self.hat.move_servo_position(index, pos)

    def toSunPosition(self):
        self.setPositions([150, 35, 90, 90])
    
    def toRegularPosition(self):
        self.setPositions([90, 90, 150, 30])

class Drivebase:
    def __init__(self):
        self.IN1 = 17
        self.IN2 = 27
        self.IN3 = 22
        self.IN4 = 24
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
        """power: -1.0 to 1.0"""
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
        """power: -1.0 to 1.0"""
        if power > 0:
            self.pwm3.ChangeDutyCycle(power * 100)
            self.pwm4.ChangeDutyCycle(0)
        elif power < 0:
            self.pwm3.ChangeDutyCycle(0)
            self.pwm4.ChangeDutyCycle(abs(power) * 100)
        else:
            self.pwm3.ChangeDutyCycle(0)
            self.pwm4.ChangeDutyCycle(0)

    def drive_instant(self, left, right):
        self.setLeft(left)
        self.setRight(right)

    def drive(self, left, right, duration):
        self.setLeft(left)
        self.setRight(right)
        time.sleep(duration)
        self.setLeft(0)
        self.setRight(0)

    def cleanup(self):
        self.pwm1.stop()
        self.pwm2.stop()
        self.pwm3.stop()
        self.pwm4.stop()
        GPIO.cleanup()

    # Convenience movement methods
    def forward(self, power, duration=None):
        """Drive forward at given power (-1.0..1.0). If duration provided, stop after. Otherwise, keep driving until stop() is called."""
        if duration is None:
            self.drive_instant(power, power)
        else:
            self.drive(power, power, duration)

    def turn_left(self, power, duration=None):
        """Turn left in place. power is magnitude (0..1). If duration provided, stop after. Otherwise, keep turning until stop() is called."""
        p = abs(power)
        if duration is None:
            self.drive_instant(-p, p)
        else:
            self.drive(-p, p, duration)

    def turn_right(self, power, duration=None):
        """Turn right in place. power is magnitude (0..1). If duration provided, stop after. Otherwise, keep turning until stop() is called."""
        p = abs(power)
        if duration is None:
            self.drive_instant(p, -p)
        else:
            self.drive(p, -p, duration)

    def stop(self):
        """Immediately stop both motors."""
        self.drive_instant(0, 0)


class Rover:
    """
    Rover class that combines Drivebase and RockerBogie functionality.
    
    This class provides a unified interface to control the complete rover system,
    including both the drivetrain (motor control) and suspension system (rocker-bogie
    servo positioning). It encapsulates all functionality from both subsystems.
    
    Attributes:
        drivebase (Drivebase): The motor control subsystem for driving the rover.
        rocker_bogie (RockerBogie): The servo control subsystem for suspension positioning.
    
    Example:
        >>> rover = Rover()
        >>> rover.setup_regular_position()  # Initialize suspension to regular position
        >>> rover.forward(0.5, duration=2)   # Drive forward at 50% power for 2 seconds
        >>> rover.turn_left(0.5, duration=1) # Turn left for 1 second
        >>> rover.setup_sun_position()       # Adjust suspension for sun positioning
        >>> rover.cleanup()                   # Clean up GPIO resources
    """
    
    def __init__(self):
        """
        Initialize the Rover by instantiating both Drivebase and RockerBogie subsystems.
        
        This constructor sets up the GPIO pins for motor control and initializes
        the servo hat for rocker-bogie positioning. Both subsystems are ready
        to use immediately after initialization.
        """
        self.drivebase = Drivebase()
        self.rocker_bogie = RockerBogie()
    
    # ==================== Drivebase Methods ====================
    
    def set_left_motor(self, power):
        """
        Set the power for the left motor.
        
        Args:
            power (float): Motor power from -1.0 (full reverse) to 1.0 (full forward).
                          0 stops the motor.
        """
        self.drivebase.setLeft(power)
    
    def set_right_motor(self, power):
        """
        Set the power for the right motor.
        
        Args:
            power (float): Motor power from -1.0 (full reverse) to 1.0 (full forward).
                          0 stops the motor.
        """
        self.drivebase.setRight(power)
    
    def drive_instant(self, left, right):
        """
        Set both motors immediately without stopping.
        
        This method sets motor powers and continues indefinitely until changed.
        Use stop() to halt the motors.
        
        Args:
            left (float): Left motor power (-1.0 to 1.0).
            right (float): Right motor power (-1.0 to 1.0).
        """
        self.drivebase.drive_instant(left, right)
    
    def drive(self, left, right, duration):
        """
        Drive with specified motor powers for a given duration, then stop.
        
        This is a blocking call that sets motor powers, waits for the specified
        duration, and then automatically stops both motors.
        
        Args:
            left (float): Left motor power (-1.0 to 1.0).
            right (float): Right motor power (-1.0 to 1.0).
            duration (float): Time in seconds to drive before stopping.
        """
        self.drivebase.drive(left, right, duration)
    
    def forward(self, power, duration=None):
        """
        Drive the rover forward.
        
        Args:
            power (float): Forward power from -1.0 (backward) to 1.0 (forward).
            duration (float, optional): Time in seconds to drive. If None, continues
                                       until stop() is called.
        
        Example:
            >>> rover.forward(0.7, duration=3)  # Drive forward at 70% for 3 seconds
            >>> rover.forward(0.5)               # Drive forward at 50% continuously
            >>> rover.stop()                     # Stop the continuous movement
        """
        self.drivebase.forward(power, duration)
    
    def turn_left(self, power, duration=None):
        """
        Turn the rover left in place.
        
        Args:
            power (float): Turn power magnitude (0 to 1.0). The sign is ignored.
            duration (float, optional): Time in seconds to turn. If None, continues
                                       until stop() is called.
        
        Example:
            >>> rover.turn_left(0.5, duration=2)  # Turn left at 50% for 2 seconds
            >>> rover.turn_left(0.3)              # Turn left at 30% continuously
        """
        self.drivebase.turn_left(power, duration)
    
    def turn_right(self, power, duration=None):
        """
        Turn the rover right in place.
        
        Args:
            power (float): Turn power magnitude (0 to 1.0). The sign is ignored.
            duration (float, optional): Time in seconds to turn. If None, continues
                                       until stop() is called.
        
        Example:
            >>> rover.turn_right(0.5, duration=2)  # Turn right at 50% for 2 seconds
            >>> rover.turn_right(0.3)              # Turn right at 30% continuously
        """
        self.drivebase.turn_right(power, duration)
    
    def stop(self):
        """
        Immediately stop both motors.
        
        This method sets both motor powers to 0, bringing the rover to a halt.
        It's useful for emergency stops or ending continuous motion commands.
        """
        self.drivebase.stop()
    
    # ==================== Rocker-Bogie Methods ====================
    
    def set_servo_positions(self, positions):
        """
        Set the servo positions for the rocker-bogie suspension system.
        
        Args:
            positions (list): List of servo positions (in degrees, typically 0-180).
                            The list should contain 4 values corresponding to the
                            4 servos in the rocker-bogie system.
        
        Example:
            >>> rover.set_servo_positions([90, 90, 90, 90])  # All servos to center
        """
        self.rocker_bogie.setPositions(positions)
    
    def setup_sun_position(self):
        """
        Configure the rocker-bogie suspension to the "sun position".
        
        This position is optimized for solar panel orientation.
        Servos are set to: [150, 35, 90, 90].
        """
        self.rocker_bogie.toSunPosition()
    
    def setup_regular_position(self):
        """
        Configure the rocker-bogie suspension to the standard driving position.
        
        This is the normal operating position for traversal and general movement.
        Servos are set to: [90, 90, 150, 30].
        """
        self.rocker_bogie.toRegularPosition()
    
    # ==================== System Management ====================
    
    def cleanup(self):
        """
        Clean up all GPIO resources used by the rover.
        
        This method should be called when you're done using the rover to properly
        release GPIO pins and PWM resources. It's important to call this before
        program termination to avoid leaving the GPIO in an inconsistent state.
        
        Note:
            After calling cleanup(), the rover instance should not be used further
            without reinitializing GPIO resources.
        """
        self.drivebase.cleanup()


if __name__ == '__main__':
    rover = Rover()
    rover.setup_regular_position()  # Initialize rocker bogie to regular position
    rover.forward(0.5, duration=2)   # Drive forward
    rover.turn_left(0.5, duration=1) # Turn left
    rover.stop()                     # Stop motors
    rover.cleanup()                  # Clean up GPIO
    