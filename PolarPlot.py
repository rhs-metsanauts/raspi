#!/usr/bin/env python3
"""
MPU6050 Polar Plot - Yaw Angle vs Light Intensity
Plots light intensity on a polar plot where theta is the yaw angle
"""

import mpu6050
import time
import math
import RPi.GPIO as GPIO
import matplotlib.pyplot as plt
import numpy as np
from collections import deque

# GPIO Setup
GPIO.setmode(GPIO.BOARD)
RESISTORPIN = 16
MAX_INTENSITY = 10.0

class PolarPlot:
    def __init__(self, address=0x68, max_points=360):
        """Initialize the MPU6050 sensor and plotting"""
        self.mpu = mpu6050.mpu6050(address)
        self.gyro_offset = {'x': 0, 'y': 0, 'z': 0}
        self.yaw = 0.0
        self.last_time = time.time()
        
        # Store data points
        self.max_points = max_points
        self.yaw_data = deque(maxlen=max_points)
        self.intensity_data = deque(maxlen=max_points)
        
        # Setup plot
        plt.ion()  # Interactive mode
        self.fig, self.ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))
        self.line, = self.ax.plot([], [], 'b-', linewidth=2)
        self.scatter = self.ax.scatter([], [], c='red', s=100, zorder=5)
        
        # Configure polar plot
        self.ax.set_theta_zero_location('N')  # 0° at top (North)
        self.ax.set_theta_direction(-1)  # Clockwise
        self.ax.set_title("Light Intensity vs Yaw Angle", va='bottom', fontsize=14, pad=20)
        self.ax.set_xlabel("Yaw Angle (degrees)", fontsize=10)
        
        # Set radial limits (will be updated based on data)
        self.ax.set_rmax(100)
        self.ax.set_rmin(0)
        self.ax.grid(True)

        plt.show(block=False)
        
    def calibrate_gyro(self, samples=100):
        """Calibrate gyroscope by calculating offset"""
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
    
    def update_yaw(self, gyro_data):
        """Calculate yaw angle by integrating gyroscope Z-axis data"""
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # Get calibrated gyro Z reading
        gyro_z = gyro_data['z'] - self.gyro_offset['z']
        
        # Integrate gyroscope reading
        self.yaw += gyro_z * dt
        
        # Normalize yaw to 0 to 360 degrees for polar plot
        self.yaw = self.yaw % 360
        
        return self.yaw
    
    def reset_yaw(self):
        """Reset yaw angle to zero"""
        self.yaw = 0.0
        self.last_time = time.time()

    def read_light_intensity(self, timeout=0.5):
        try:
            GPIO.setup(RESISTORPIN, GPIO.OUT)
            GPIO.output(RESISTORPIN, GPIO.LOW)
            time.sleep(0.01)

            GPIO.setup(RESISTORPIN, GPIO.IN)
            start = time.time()

            while GPIO.input(RESISTORPIN) == GPIO.LOW:
                if (time.time() - start) > timeout:
                    return 0.0

            diff_ms = (time.time() - start) * 1000.0
            light = 1.0 / diff_ms if diff_ms > 0 else 1000.0

            return min(light, MAX_INTENSITY)

        except Exception as e:
            print(f"Error reading light: {e}")
            return 0.0




    
    def update_plot(self):
        if len(self.yaw_data) == 0:
            return

        theta = np.radians(list(self.yaw_data))
        r = np.array(list(self.intensity_data), dtype=float)

        # Update line
        self.line.set_data(theta, r)

        # Update current-point marker (theta,r) in polar data coords
        self.scatter.set_offsets(np.c_[theta[-1], r[-1]])

        # Auto-scale radial axis
        max_r = float(np.max(r)) if len(r) else 1.0
        self.ax.set_rmax(max_r * 1.1 if max_r > 0 else 1.0)

        self.fig.canvas.draw_idle()
        plt.pause(0.001)  # <-- this is what makes it animate

    
    def add_data_point(self, yaw, intensity):
        """Add a new data point to the plot"""
        self.yaw_data.append(yaw)
        self.intensity_data.append(intensity)
    
    def clear_data(self):
        """Clear all stored data points"""
        self.yaw_data.clear()
        self.intensity_data.clear()
        print("Data cleared!")
    
    def run(self, update_interval=0.1):
        """Main loop to continuously update the plot"""
        print("\nPolar Plot Controls:")
        print("  - Plot updates in real-time")
        print("  - Yaw angle = theta (0° at top, clockwise)")
        print("  - Light intensity = radius")
        print("  - Press Ctrl+C to stop")
        print(f"\nCollecting data every {update_interval}s...")
        
        try:
            while True:
                # Read sensor data
                _, gyro_data, _ = self.read_sensor_data()
                
                if gyro_data is not None:
                    # Update yaw
                    yaw = self.update_yaw(gyro_data)
                    
                    # Read light intensity
                    intensity = self.read_light_intensity()
                    
                    # Add data point
                    self.add_data_point(yaw, intensity)
                    
                    # Update plot
                    self.update_plot()
                    
                    # Print current values
                    print(f"\rYaw: {yaw:6.2f}°  |  Light: {intensity:6.2f}  |  Points: {len(self.yaw_data)}", end='')
                
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping data collection...")
        finally:
            GPIO.cleanup()
            plt.ioff()
            plt.show()



def main():
    """Main execution function"""
    print("="*60)
    print("MPU6050 Polar Plot - Yaw vs Light Intensity")
    print("="*60)
    
    # Initialize plotter
    plotter = PolarPlot(address=0x68, max_points=360)
    
    # Optional: Calibrate gyroscope
    calibrate = input("\nCalibrate gyroscope? (y/n): ").lower()
    if calibrate == 'y':
        plotter.calibrate_gyro()
    
    print("\n⚠️  Note: Replace read_light_intensity() with your actual light sensor code!")
    print("    Currently using simulated data for demonstration.\n")
    
    # Get update interval
    try:
        interval = float(input("Update interval in seconds (default 0.1): ") or "0.1")
    except:
        interval = 0.1
    
    # Run the plotter
    plotter.run(update_interval=interval)


if __name__ == "__main__":
    main()