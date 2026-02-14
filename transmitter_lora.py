# save as code.py on the Lora module


import board
import digitalio
import keypad
import adafruit_rfm9x
import time
import json
import random

endian = 'little'

# Define radio frequency in MHz. Must match your
# module. Can be a value like 915.0, 433.0, etc.
RADIO_FREQ_MHZ = 915.0

# Define Chip Select and Reset pins for the radio module.
CS = digitalio.DigitalInOut(board.RFM_CS)
RESET = digitalio.DigitalInOut(board.RFM_RST)

# Initialise RFM95 radio
rfm95 = adafruit_rfm9x.RFM9x(board.SPI(), CS, RESET, RADIO_FREQ_MHZ)

def create_packets(json_data, recipient_id, packet_content_id):
    """
    Create packets from JSON data with the specified structure.
    
    Packet structure (252 bytes total):
    - Byte 0: Recipient ID (1 byte)
    - Bytes 1-4: Unique Packet Content ID (4 bytes)
    - Bytes 5-6: Index (2 bytes, 0-65535)
    - Bytes 7-8: Total number of indexes (2 bytes)
    - Bytes 9-251: Message content (243 bytes per chunk)
    """
    # Convert JSON to bytes
    json_bytes = json.dumps(json_data).encode('utf-8')
    
    # Calculate number of chunks needed
    chunk_size = 243
    total_chunks = (len(json_bytes) + chunk_size - 1) // chunk_size
    
    if total_chunks > 65535:
        raise ValueError(f"Data too large: {total_chunks} chunks needed, max is 65535")
    
    packets = []
    for index in range(total_chunks):
        # Extract chunk of data
        start = index * chunk_size
        end = min(start + chunk_size, len(json_bytes))
        chunk = json_bytes[start:end]
        
        # Pad chunk to 243 bytes if it's the last one and shorter
        chunk = chunk.ljust(chunk_size, b'\x00')
        
        # Build packet
        packet = bytearray()
        packet.append(recipient_id & 0xFF)  # Byte 0: Recipient ID (1 byte)
        packet.extend(packet_content_id.to_bytes(4, endian))  # Bytes 1-4: Packet Content ID
        packet.extend(index.to_bytes(2, endian))  # Bytes 5-6: Index
        packet.extend(total_chunks.to_bytes(2, endian))  # Bytes 7-8: Total chunks
        packet.extend(chunk)  # Bytes 9-251: Content (243 bytes)
        
        packets.append(bytes(packet))
    
    return packets

# Read JSON from file
with open('message.json', 'r') as f:
    json_data = json.load(f)

# Extract recipient ID from JSON
recipient_id = json_data.get('Recipient', 0)

# Packet content ID starts at 0 and increments for each transmission
packet_content_id = 0

# Create packets
packets = create_packets(json_data, recipient_id, packet_content_id)

# Send packets
print(f'Sending {len(packets)} packet(s) to recipient {recipient_id}')
print(f'Packet Content ID: {packet_content_id}')
print(f'Total data size: {len(json.dumps(json_data))} bytes')
print('-' * 50)

for i, packet in enumerate(packets):
    rfm95.send(packet)
    print(f'✓ Sent packet {i+1}/{len(packets)} (Index: {i})')
    time.sleep(0.05)

print('-' * 50)
print(f'Successfully sent all packets to recipient {recipient_id}')
