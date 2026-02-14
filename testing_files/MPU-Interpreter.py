#!/usr/bin/env python3
"""
MPU6050 Data Interpreter
Integrates with mpu6050 library to interpret accelerometer and gyroscope data
"""

import mpu6050
import time
import math

class MPU6050Interpreter:
    def __init__(self, address=0x68):
        """Initialize the MPU6050 sensor"""
        self.mpu = mpu6050.mpu6050(address)
        self.gyro_offset = {'x': 0, 'y': 0, 'z': 0}
        self.yaw = 0.0  # Accumulated yaw angle
        self.last_time = time.time()
        
    def read_sensor_data(self):
        """Read raw sensor data"""
        try:
            accelerometer_data = self.mpu.get_accel_data()
            gyroscope_data = self.mpu.get_gyro_data()
            temperature = self.mpu.get_temp()
            return accelerometer_data, gyroscope_data, temperature
        except Exception as e:
            print(f"Sensor read error: {e}")
            return None, None, None
    
    def calculate_tilt_angles(self, accel_data):
        """
        Calculate pitch and roll angles from accelerometer data
        Returns angles in degrees
        """
        x = accel_data['x']
        y = accel_data['y']
        z = accel_data['z']
        
        # Calculate pitch (rotation around Y-axis)
        pitch = math.atan2(x, math.sqrt(y**2 + z**2)) * 180 / math.pi
        
        # Calculate roll (rotation around X-axis)
        roll = math.atan2(y, math.sqrt(x**2 + z**2)) * 180 / math.pi
        
        return {'pitch': pitch, 'roll': roll}
    
    def update_yaw(self, gyro_data):
        """
        Calculate yaw angle by integrating gyroscope Z-axis data over time
        Note: Yaw drifts over time without magnetometer correction
        """
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # Get calibrated gyro Z reading (rotation around vertical axis)
        gyro_z = gyro_data['z'] - self.gyro_offset['z']
        
        # Integrate gyroscope reading to get yaw angle
        self.yaw += gyro_z * dt
        
        # Normalize yaw to -180 to 180 degrees
        self.yaw = ((self.yaw + 180) % 360) - 180
        
        return self.yaw
    
    def reset_yaw(self):
        """Reset yaw angle to zero"""
        self.yaw = 0.0
        self.last_time = time.time()
    
    def calculate_acceleration_magnitude(self, accel_data):
        """Calculate total acceleration magnitude in g's"""
        x = accel_data['x']
        y = accel_data['y']
        z = accel_data['z']
        
        magnitude = math.sqrt(x**2 + y**2 + z**2)
        return magnitude
    
    def detect_motion(self, accel_data, threshold=0.15):
        """
        Detect if device is in motion based on acceleration
        threshold: acceleration deviation from 1g (default 0.15g)
        """
        magnitude = self.calculate_acceleration_magnitude(accel_data)
        # Device at rest should read ~1g total
        deviation = abs(magnitude - 1.0)
        return deviation > threshold
    
    def detect_orientation(self, accel_data):
        """Detect device orientation based on accelerometer"""
        x = accel_data['x']
        y = accel_data['y']
        z = accel_data['z']
        
        # Find which axis has the strongest reading
        abs_x, abs_y, abs_z = abs(x), abs(y), abs(z)
        
        if abs_z > abs_x and abs_z > abs_y:
            if z > 0:
                return "Face Up"
            else:
                return "Face Down"
        elif abs_y > abs_x:
            if y > 0:
                return "Standing on Bottom Edge"
            else:
                return "Standing on Top Edge"
        else:
            if x > 0:
                return "Standing on Right Edge"
            else:
                return "Standing on Left Edge"
    
    def calculate_rotation_rate(self, gyro_data):
        """Calculate total rotation rate in degrees/second"""
        x = gyro_data['x']
        y = gyro_data['y']
        z = gyro_data['z']
        
        rotation_rate = math.sqrt(x**2 + y**2 + z**2)
        return rotation_rate
    
    def detect_rotation(self, gyro_data, threshold=10.0):
        """
        Detect if device is rotating
        threshold: rotation rate in degrees/second
        """
        rotation_rate = self.calculate_rotation_rate(gyro_data)
        return rotation_rate > threshold
    
    def calibrate_gyro(self, samples=100):
        """
        Calibrate gyroscope by calculating offset
        Device should be stationary during calibration
        """
        print("Calibrating gyroscope... Keep device still!")
        
        sum_x, sum_y, sum_z = 0, 0, 0
        
        for i in range(samples):
            _, gyro_data, _ = self.read_sensor_data()
            if gyro_data:
                sum_x += gyro_data['x']
                sum_y += gyro_data['y']
                sum_z += gyro_data['z']
            time.sleep(0.01)
        
        self.gyro_offset['x'] = sum_x / samples
        self.gyro_offset['y'] = sum_y / samples
        self.gyro_offset['z'] = sum_z / samples
        
        print(f"Calibration complete! Offsets: {self.gyro_offset}")
    
    def get_calibrated_gyro(self, gyro_data):
        """Apply calibration offset to gyroscope data"""
        return {
            'x': gyro_data['x'] - self.gyro_offset['x'],
            'y': gyro_data['y'] - self.gyro_offset['y'],
            'z': gyro_data['z'] - self.gyro_offset['z']
        }
    
    def interpret_data(self, accel_data, gyro_data, temperature):
        """Interpret all sensor data and return analysis"""
        if accel_data is None or gyro_data is None:
            return None
        
        # Calculate tilt angles
        tilt = self.calculate_tilt_angles(accel_data)
        
        # Update yaw angle
        yaw = self.update_yaw(gyro_data)
        
        # Calculate acceleration magnitude
        accel_magnitude = self.calculate_acceleration_magnitude(accel_data)
        
        # Detect motion
        in_motion = self.detect_motion(accel_data)
        
        # Detect orientation
        orientation = self.detect_orientation(accel_data)
        
        # Get calibrated gyro data
        calibrated_gyro = self.get_calibrated_gyro(gyro_data)
        
        # Calculate rotation rate
        rotation_rate = self.calculate_rotation_rate(calibrated_gyro)
        
        # Detect rotation
        is_rotating = self.detect_rotation(calibrated_gyro)
        
        return {
            'tilt': tilt,
            'yaw': yaw,
            'accel_magnitude': accel_magnitude,
            'in_motion': in_motion,
            'orientation': orientation,
            'rotation_rate': rotation_rate,
            'is_rotating': is_rotating,
            'calibrated_gyro': calibrated_gyro,
            'temperature_c': temperature
        }
    
    def print_interpretation(self, interpretation):
        """Pretty print the interpretation"""
        if interpretation is None:
            print("Warning: Failed to interpret sensor data")
            return
        
        print("\n" + "="*60)
        print("MPU6050 SENSOR INTERPRETATION")
        print("="*60)
        
        print(f"\n🌡️  Temperature: {interpretation['temperature_c']:.2f}°C")
        
        print(f"\n📐 Tilt Angles:")
        print(f"   Pitch: {interpretation['tilt']['pitch']:>7.2f}°")
        print(f"   Roll:  {interpretation['tilt']['roll']:>7.2f}°")
        print(f"   Yaw:   {interpretation['yaw']:>7.2f}° (integrated from gyro)")
        
        print(f"\n📍 Orientation: {interpretation['orientation']}")
        
        print(f"\n⚡ Acceleration:")
        print(f"   Magnitude: {interpretation['accel_magnitude']:.3f} g")
        print(f"   Motion Detected: {'YES ⚠️' if interpretation['in_motion'] else 'No'}")
        
        print(f"\n🔄 Rotation:")
        print(f"   Rate: {interpretation['rotation_rate']:.2f}°/s")
        print(f"   Rotating: {'YES ⚠️' if interpretation['is_rotating'] else 'No'}")
        print(f"   Gyro (calibrated):")
        print(f"      X: {interpretation['calibrated_gyro']['x']:>7.2f}°/s")
        print(f"      Y: {interpretation['calibrated_gyro']['y']:>7.2f}°/s")
        print(f"      Z: {interpretation['calibrated_gyro']['z']:>7.2f}°/s")


def main():
    """Main execution function"""
    print("Initializing MPU6050 Interpreter...")
    interpreter = MPU6050Interpreter(0x68)
    
    # Optional: Calibrate gyroscope
    calibrate = input("Calibrate gyroscope? (y/n): ").lower()
    if calibrate == 'y':
        interpreter.calibrate_gyro()
    
    print("\n⚠️  Note: Yaw angle is calculated by integrating gyroscope data.")
    print("    It will drift over time without magnetometer correction.")
    print("    Press 'r' during monitoring to reset yaw to 0°")
    print("\nStarting continuous monitoring... (Ctrl+C to stop)")
    
    try:
        while True:
            # Read sensor data
            accel_data, gyro_data, temperature = interpreter.read_sensor_data()
            
            if accel_data is not None:
                # Display raw data
                print("\n📊 Raw Sensor Data:")
                print(f"   Accelerometer: {accel_data}")
                print(f"   Gyroscope:     {gyro_data}")
                print(f"   Temperature:   {temperature}°C")
                
                # Interpret the data
                interpretation = interpreter.interpret_data(accel_data, gyro_data, temperature)
                
                # Display interpretation
                interpreter.print_interpretation(interpretation)
            else:
                print("Warning: Failed to read sensor data")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nStopping sensor monitoring...")
        print("Goodbye!")


if __name__ == "__main__":
    main()