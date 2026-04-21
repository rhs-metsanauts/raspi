# save as code.py on the Lora receiver module

import board
import digitalio
import adafruit_rfm9x
import time
import json

endian = 'little'

# Define radio frequency in MHz. Must match your
# module. Can be a value like 915.0, 433.0, etc.
RADIO_FREQ_MHZ = 915.0

# Define Chip Select and Reset pins for the radio module.
CS = digitalio.DigitalInOut(board.RFM_CS)
RESET = digitalio.DigitalInOut(board.RFM_RST)

# Initialise RFM95 radio
rfm95 = adafruit_rfm9x.RFM9x(board.SPI(), CS, RESET, RADIO_FREQ_MHZ)
rfm95.tx_power = 23  # Max transmission power (5-23 dBm)

# Set this to your device's ID (0-255)
MY_ID = 0

# Storage for incoming packet data
# Key: packet_content_id, Value: dict with chunks and metadata
packet_buffer = {}

def parse_packet(packet):
    """
    Parse a received packet and extract its components.
    
    Returns:
        dict with keys: recipient_id, packet_content_id, index, total_chunks, data
        or None if packet is invalid
    """
    if len(packet) < 9:
        print(f"Invalid packet size: {len(packet)} bytes (expected at least 9)")
        return None
    
    try:
        recipient_id = packet[0]
        packet_content_id = int.from_bytes(packet[1:5], endian)
        index = int.from_bytes(packet[5:7], endian)
        total_chunks = int.from_bytes(packet[7:9], endian)
        data = packet[9:]  # Remaining bytes are data (up to 239 bytes)
        
        return {
            'recipient_id': recipient_id,
            'packet_content_id': packet_content_id,
            'index': index,
            'total_chunks': total_chunks,
            'data': data
        }
    except Exception as e:
        print(f"Error parsing packet: {e}")
        return None

def reassemble_message(packet_content_id):
    """
    Reassemble all chunks for a given packet_content_id into the original JSON.
    
    Returns:
        dict: The parsed JSON data, or None if reassembly failed
    """
    if packet_content_id not in packet_buffer:
        return None
    
    packet_info = packet_buffer[packet_content_id]
    chunks = packet_info['chunks']
    total_chunks = packet_info['total_chunks']
    
    # Check if we have all chunks
    if len(chunks) != total_chunks:
        return None
    
    # Reassemble in order
    full_data = bytearray()
    for i in range(total_chunks):
        if i not in chunks:
            return None
        full_data.extend(chunks[i])
    
    # Remove null byte padding
    full_data = bytes(full_data).rstrip(b'\x00')
    
    # Parse JSON
    try:
        json_str = full_data.decode('utf-8')
        json_data = json.loads(json_str)
        return json_data
    except Exception as e:
        print(f"Error decoding JSON: {e}")
        return None

print(f"Listening for packets on {RADIO_FREQ_MHZ} MHz...")
print(f"My ID: {MY_ID}")
print('-' * 50)

# Counter for heartbeat
loop_count = 0

# Main receive loop
while True:
    try:
        # Wait for a packet (library strips its 4-byte header automatically)
        packet = rfm95.receive(timeout=5.0)
        
        if packet is not None:
            print(f"✓ Packet received! Length: {len(packet)} bytes, RSSI: {rfm95.last_rssi} dB")
            # Parse the packet
            parsed = parse_packet(packet)
            
            if parsed is None:
                continue
            
            recipient_id = parsed['recipient_id']
            packet_content_id = parsed['packet_content_id']
            index = parsed['index']
            total_chunks = parsed['total_chunks']
            data = parsed['data']
            
            # Check if packet is for us (or broadcast to 255)
            if recipient_id != MY_ID and recipient_id != 255:
                print(f"⊗ Packet not for us (for ID {recipient_id})")
                continue
            
            print(f"⇓ Received packet {index + 1}/{total_chunks} (Content ID: {packet_content_id})")
            
            # Initialize buffer for this packet_content_id if needed
            if packet_content_id not in packet_buffer:
                packet_buffer[packet_content_id] = {
                    'total_chunks': total_chunks,
                    'chunks': {},
                    'timestamp': time.monotonic()
                }
            
            # Store the chunk
            packet_buffer[packet_content_id]['chunks'][index] = data
            
            # Check if we have all chunks
            received_chunks = len(packet_buffer[packet_content_id]['chunks'])
            if received_chunks == total_chunks:
                print(f"✓ All {total_chunks} chunks received!")
                print('-' * 50)
                # Reassemble the message
                json_data = reassemble_message(packet_content_id)
                if json_data is not None:
                    # Print with unique prefix so serial reader can filter this line
                    print(f"DATA_JSON:{json.dumps(json_data)}")
                    # Clean up buffer
                    del packet_buffer[packet_content_id]
                else:
                    print("✗ Failed to reassemble message")
            else:
                print(f"  Progress: {received_chunks}/{total_chunks} chunks")
        else:
            # No packet received - print heartbeat every 10 loops (50 seconds)
            loop_count += 1
            if loop_count % 10 == 0:
                print(f"Still listening... (loop {loop_count})")
        
        # Clean up old incomplete messages (older than 60 seconds)
        current_time = time.monotonic()
        expired_ids = []
        for pcid, info in packet_buffer.items():
            if current_time - info['timestamp'] > 60:
                expired_ids.append(pcid)
        
        for pcid in expired_ids:
            print(f"⚠ Timeout: Discarding incomplete message (Content ID: {pcid})")
            del packet_buffer[pcid]
    
    except Exception as e:
        print(f"Error in receive loop: {e}")
        time.sleep(1)
