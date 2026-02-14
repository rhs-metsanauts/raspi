# save as code.py on the Lora module


import board
import digitalio
import keypad
import adafruit_rfm9x
import time

endian = 'little'

# Define radio frequency in MHz. Must match your
# module. Can be a value like 915.0, 433.0, etc.
RADIO_FREQ_MHZ = 915.0

# Define Chip Select and Reset pins for the radio module.
CS = digitalio.DigitalInOut(board.RFM_CS)
RESET = digitalio.DigitalInOut(board.RFM_RST)

# Initialise RFM95 radio
rfm95 = adafruit_rfm9x.RFM9x(board.SPI(), CS, RESET, RADIO_FREQ_MHZ)

def split_bytes(inputbytes):
    length=250
    l=[]

    index=0

    for i in range(0, len(inputbytes), length):
        l.append(index.to_bytes(252-length, endian)+inputbytes[i:i+length])
        index+=1
    return l

#   print((10).to_bytes(2, 'little'))

text = open('message.txt', 'r').read()
for i in split_bytes(bytes(text, 'utf-8')):
    rfm95.send(i)
    index = int.from_bytes(i[0:2], endian)
    print('block index: '+ str(index))
    print('block content: '+ i[2::].decode())
    time.sleep(0.05)
print('sent: '+text)
