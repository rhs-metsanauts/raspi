import mpu6050
import time

mpu6050 = mpu6050.mpu6050(0x68)

def read_sensor_data():
    try:
        accelerometer_data = mpu6050.get_accel_data()
        gyroscope_data = mpu6050.get_gyro_data()
        temperature = mpu6050.get_temp()
        return accelerometer_data, gyroscope_data, temperature
    except Exception as e:
        print(f"Sensor read error: {e}")
        return None, None, None

while True:
    accelerometer_data, gyroscope_data, temperature = read_sensor_data()
    
    if accelerometer_data is not None:
        print("Accelerometer data:", accelerometer_data)
        print("Gyroscope Data:", gyroscope_data)
        print("Temp:", temperature)
    else:
        print("Warning: Failed to read sensor data")
    
    time.sleep(1)