#!/usr/bin/env python3
"""
Light Intensity vs Yaw Angle Plotter
Combines LDR light sensor and MPU6050 gyroscope data
"""

import sys
import time
import RPi.GPIO as GPIO
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import mpu6050

# GPIO Setup
GPIO.setmode(GPIO.BOARD)
RESISTORPIN = 16

# MPU6050 Setup
class YawTracker:
    def __init__(self, address=0x68):
        """Initialize MPU6050 for yaw tracking"""
        self.mpu = mpu6050.mpu6050(address)
        self.gyro_offset_z = 0
        self.yaw = 0.0
        self.last_time = time.time()
    
    def calibrate(self, samples=100):
        """Calibrate gyroscope Z-axis"""
        print("Calibrating gyroscope... Keep device still!")
        sum_z = 0
        
        for i in range(samples):
            gyro_data = self.mpu.get_gyro_data()
            sum_z += gyro_data['z']
            time.sleep(0.01)
        
        self.gyro_offset_z = sum_z / samples
        print(f"Calibration complete! Z-offset: {self.gyro_offset_z:.2f}")
    
    def update_yaw(self):
        """Update yaw angle from gyroscope"""
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        gyro_data = self.mpu.get_gyro_data()
        gyro_z = gyro_data['z'] - self.gyro_offset_z
        
        # Integrate to get yaw
        self.yaw += gyro_z * dt
        
        # Normalize to -180 to 180
        self.yaw = ((self.yaw + 180) % 360) - 180
        
        return self.yaw
    
    def reset_yaw(self):
        """Reset yaw to zero"""
        self.yaw = 0.0
        self.last_time = time.time()


def read_light_intensity():
    """Read light intensity from LDR sensor"""
    try:
        # Discharge capacitor
        GPIO.setup(RESISTORPIN, GPIO.OUT)
        GPIO.output(RESISTORPIN, GPIO.LOW)
        time.sleep(0.1)
        
        # Measure charge time
        GPIO.setup(RESISTORPIN, GPIO.IN)
        currentTime = time.time()
        diff = 0
        
        while GPIO.input(RESISTORPIN) == GPIO.LOW:
            diff = time.time() - currentTime
        
        diff_ms = diff * 1000
        
        # Convert to light intensity (inverse of charge time)
        # Smaller diff_ms = faster charge = more light = higher value
        if diff_ms > 0:
            light = 1 / diff_ms
        else:
            light = 1000  # Very bright light (very fast charge)
            
        return light
    
    except Exception as e:
        print(f"Error reading light: {e}")
        return 0

def main():
    """Main execution with real-time plotting"""
    print("Initializing Light vs Yaw Plotter...")
    
    # Initialize yaw tracker
    yaw_tracker = YawTracker(0x68)
    
    # Calibrate
    calibrate = input("Calibrate gyroscope? (y/n): ").lower()
    if calibrate == 'y':
        yaw_tracker.calibrate()
    
    # Setup plot
    plt.ion()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Left plot: Light vs Yaw (scatter plot)
    yaw_data = []
    light_data = []
    scatter = ax1.scatter([], [], c='blue', alpha=0.6, s=50)
    ax1.set_xlabel("Yaw Angle (degrees)")
    ax1.set_ylabel("Light Intensity")
    ax1.set_title("Light Intensity vs Yaw Angle")
    ax1.grid(True, alpha=0.3)
    
    # Right plot: Time series
    times = []
    yaw_time = []
    light_time = []
    start_time = time.time()
    
    line_yaw, = ax2.plot([], [], 'r-', label='Yaw', linewidth=2)
    line_light, = ax2.plot([], [], 'b-', label='Light', linewidth=2)
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Value")
    ax2.set_title("Yaw and Light Over Time")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Create secondary y-axis for light
    ax2_twin = ax2.twinx()
    ax2_twin.set_ylabel("Light Intensity", color='b')
    
    print("\nStarting data collection... (Ctrl+C to stop)")
    print("Rotate the device and observe how light changes with yaw!")
    print("Press 'r' + Enter in terminal to reset yaw to 0°\n")
    
    try:
        while True:
            # Read sensors
            yaw = yaw_tracker.update_yaw()
            light = read_light_intensity()
            elapsed = time.time() - start_time
            
            # Store data
            yaw_data.append(yaw)
            light_data.append(light)
            times.append(elapsed)
            yaw_time.append(yaw)
            light_time.append(light)
            
            # Limit data points for performance
            max_points = 500
            if len(yaw_data) > max_points:
                yaw_data = yaw_data[-max_points:]
                light_data = light_data[-max_points:]
            
            if len(times) > 200:
                times = times[-200:]
                yaw_time = yaw_time[-200:]
                light_time = light_time[-200:]
            
            # Update scatter plot (Light vs Yaw)
            scatter.set_offsets(list(zip(yaw_data, light_data)))
            ax1.relim()
            ax1.autoscale_view()
            
            # Update time series plots
            line_yaw.set_data(times, yaw_time)
            line_light.set_data(times, light_time)
            
            ax2.relim()
            ax2.autoscale_view()
            ax2_twin.relim()
            ax2_twin.autoscale_view()
            
            # Update plot
            fig.canvas.draw()
            fig.canvas.flush_events()
            
            # Print current values with more detail
            print(f"Time: {elapsed:6.1f}s | Yaw: {yaw:7.2f}° | Light: {light:8.4f} | Range: [{min(light_data):.4f}, {max(light_data):.4f}]")
            
            time.sleep(0.1)  # Slower update for debugging
            
    except KeyboardInterrupt:
        print("\n\nStopping data collection...")
        
        # Save final plot
        plt.ioff()
        
        # Create final summary plot
        fig_final, ((ax_scatter, ax_yaw), (ax_light, ax_stats)) = plt.subplots(2, 2, figsize=(14, 10))
        
        # Scatter plot
        ax_scatter.scatter(yaw_data, light_data, c='blue', alpha=0.6, s=50)
        ax_scatter.set_xlabel("Yaw Angle (degrees)")
        ax_scatter.set_ylabel("Light Intensity")
        ax_scatter.set_title("Light Intensity vs Yaw Angle")
        ax_scatter.grid(True, alpha=0.3)
        
        # Yaw over time
        ax_yaw.plot(times, yaw_time, 'r-', linewidth=2)
        ax_yaw.set_xlabel("Time (s)")
        ax_yaw.set_ylabel("Yaw (degrees)")
        ax_yaw.set_title("Yaw Angle Over Time")
        ax_yaw.grid(True, alpha=0.3)
        
        # Light over time
        ax_light.plot(times, light_time, 'b-', linewidth=2)
        ax_light.set_xlabel("Time (s)")
        ax_light.set_ylabel("Light Intensity")
        ax_light.set_title("Light Intensity Over Time")
        ax_light.grid(True, alpha=0.3)
        
        # Statistics
        ax_stats.axis('off')
        stats_text = f"""
        Data Collection Summary
        ═══════════════════════════
        
        Total Duration: {elapsed:.1f} seconds
        Data Points: {len(yaw_data)}
        
        Yaw Angle:
          Min: {min(yaw_time):.2f}°
          Max: {max(yaw_time):.2f}°
          Range: {max(yaw_time) - min(yaw_time):.2f}°
        
        Light Intensity:
          Min: {min(light_time):.4f}
          Max: {max(light_time):.4f}
          Average: {sum(light_time)/len(light_time):.4f}
        """
        ax_stats.text(0.1, 0.5, stats_text, fontsize=12, family='monospace',
                     verticalalignment='center')
        
        plt.tight_layout()
        
        # Save plot
        filename = f"light_vs_yaw_{int(time.time())}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"Plot saved as: {filename}")
        
        plt.show()
        print("Goodbye!")
    
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()