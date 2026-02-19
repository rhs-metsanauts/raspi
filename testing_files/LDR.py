import sys

import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt

GPIO.setmode(GPIO.BOARD)

RESISTORPIN = 16
COVEREDTHRESHOLD = 8

#print('seen')
while True:
    GPIO.setup(RESISTORPIN, GPIO.OUT)
    GPIO.output(RESISTORPIN, GPIO.LOW)
    time.sleep(0.1)
    
    GPIO.setup(RESISTORPIN, GPIO.IN)
    currentTime = time.time()
    diff = 0
    
    while(GPIO.input(RESISTORPIN) == GPIO.LOW):
        diff = time.time() - currentTime
        
    print(diff * 1000)
    if (diff * 1000) > COVEREDTHRESHOLD:
        print("covered")

    time.sleep(0.1)
