# Serial reader for LoRa receiver
# Reads serial output from the CircuitPython board and extracts JSON data.
# Run this on your computer (Windows or Raspberry Pi).
#
# Usage:
#   python serial_reader.py
#   python serial_reader.py --port COM5
#   python serial_reader.py --port /dev/ttyACM0
#   python serial_reader.py --port COM5 --output received.json

import serial
import serial.tools.list_ports
import json
import sys
import argparse
import time

DATA_PREFIX = "DATA_JSON:"

def find_circuitpython_port():
    """Auto-detect the CircuitPython serial port."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # CircuitPython boards typically show up with these identifiers
        desc = (port.description or '').lower()
        manufacturer = (port.manufacturer or '').lower()
        if 'circuitpython' in desc or 'adafruit' in manufacturer or 'feather' in desc:
            return port.device
    # If no match, return the first available port
    if ports:
        print(f"Could not auto-detect CircuitPython port.")
        print("Available ports:")
        for p in ports:
            print(f"  {p.device}: {p.description} [{p.manufacturer}]")
        return None
    return None

def main():
    parser = argparse.ArgumentParser(description='Serial reader for LoRa receiver')
    parser.add_argument('--port', type=str, help='Serial port (e.g., COM5, /dev/ttyACM0)')
    parser.add_argument('--baud', type=int, default=115200, help='Baud rate (default: 115200)')
    parser.add_argument('--output', type=str, default='received_message.json',
                        help='Output file for received JSON (default: received_message.json)')
    parser.add_argument('--verbose', action='store_true', help='Print all serial output')
    args = parser.parse_args()

    # Find the serial port
    port = args.port
    if port is None:
        port = find_circuitpython_port()
        if port is None:
            print("Error: No serial port found. Use --port to specify one.")
            sys.exit(1)

    print(f"Connecting to {port} at {args.baud} baud...")

    try:
        ser = serial.Serial(port, args.baud, timeout=1)
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        sys.exit(1)

    print(f"Connected. Waiting for data...")
    print(f"JSON messages will be saved to: {args.output}")
    print("-" * 50)

    try:
        while True:
            try:
                line = ser.readline().decode('utf-8', errors='replace').strip()
            except serial.SerialException:
                print("Serial connection lost. Reconnecting...")
                time.sleep(2)
                try:
                    ser.close()
                    ser = serial.Serial(port, args.baud, timeout=1)
                    print("Reconnected.")
                except serial.SerialException:
                    pass
                continue

            if not line:
                continue

            if args.verbose:
                print(f"[SERIAL] {line}")

            # Check if this line contains our JSON data
            if line.startswith(DATA_PREFIX):
                json_str = line[len(DATA_PREFIX):]
                try:
                    json_data = json.loads(json_str)
                    print(f"Received JSON: {json.dumps(json_data, indent=2)}")

                    # Save to file
                    with open(args.output, 'w') as f:
                        json.dump(json_data, f, indent=2)
                    print(f"Saved to {args.output}")
                    print("-" * 50)

                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")
                    print(f"Raw data: {json_str}")

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        ser.close()

if __name__ == '__main__':
    main()
