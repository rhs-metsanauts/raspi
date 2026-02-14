import sys
import time
import RPi.GPIO as GPIO
import matplotlib.pyplot as plt

GPIO.setmode(GPIO.BOARD)

RESISTORPIN = 16
SUNTHRESHOLD = 0.6

# --- Plot setup ---
plt.ion()  # interactive mode
fig, ax = plt.subplots()
times = []
values = []
line, = ax.plot(times, values)

ax.set_xlabel("Time (s)")
ax.set_ylabel("Light")
ax.set_title("Light over time")

start_time = time.time()

try:
    while True:
        # Discharge capacitor
        GPIO.setup(RESISTORPIN, GPIO.OUT)
        GPIO.output(RESISTORPIN, GPIO.LOW)
        time.sleep(0.1)

        # Measure charge time
        GPIO.setup(RESISTORPIN, GPIO.IN)
        currentTime = time.time()
        diff = 0  # Initialize diff variable
        
        # Add timeout to prevent infinite loop
        while GPIO.input(RESISTORPIN) == GPIO.LOW:
            diff = time.time() - currentTime
            if diff > 2.0:  # 2 second timeout for very dark conditions
                break

        diff_ms = diff * 1000
        elapsed = time.time() - start_time

        # Avoid division by zero
        if diff_ms > 0.001:
            light = 1/diff_ms
        else:
            light = 1000  # Very bright (very fast charge)
            
        print(light)

        if light > SUNTHRESHOLD:
            print("SUN DETECTED")

        # --- Store data ---
        times.append(elapsed)
        values.append(light)

        # Limit points (keeps plot fast)
        times = times[-100:]
        values = values[-100:]

        # --- Update plot ---
        line.set_xdata(times)
        line.set_ydata(values)
        ax.relim()
        ax.autoscale_view()

        plt.pause(0.01)
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    GPIO.cleanup()
    plt.ioff()
    plt.show()