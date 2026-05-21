# Serial reader for LoRa receiver
# Reads serial output from the CircuitPython board, extracts JSON data,
# and executes commands directly on the rover.
#
# Supported command types via LoRa: bash_command, edit_file, basic_action
#
# Usage:
#   python serial_reader.py
#   python serial_reader.py --port COM5
#   python serial_reader.py --port /dev/ttyACM0

import serial
import serial.tools.list_ports
import json
import sys
import argparse
import time

from command_executor import execute_command

DATA_PREFIX = "DATA_JSON:"
SERIAL_SUPPORTED_TYPES = ["bash_command", "edit_file", "basic_action"]


def find_circuitpython_port():
    """Auto-detect the CircuitPython serial port."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        desc = (port.description or '').lower()
        manufacturer = (port.manufacturer or '').lower()
        if 'circuitpython' in desc or 'adafruit' in manufacturer or 'feather' in desc:
            return port.device
    if ports:
        print("Could not auto-detect CircuitPython port.")
        print("Available ports:")
        for p in ports:
            print(f"  {p.device}: {p.description} [{p.manufacturer}]")
        return None
    return None


def handle_command(payload: dict) -> dict:
    """Validate and execute a command received over LoRa serial."""
    cmd_type = payload.get("type")

    if cmd_type not in SERIAL_SUPPORTED_TYPES:
        print(f"[WARN] Unsupported command type for serial: '{cmd_type}'. "
              f"Supported: {', '.join(SERIAL_SUPPORTED_TYPES)}")
        return {
            "status": "error",
            "type": cmd_type,
            "message": f"Unsupported type for serial mode. Supported: {', '.join(SERIAL_SUPPORTED_TYPES)}"
        }

    return execute_command(payload)


def main():
    parser = argparse.ArgumentParser(description='Serial reader & executor for LoRa receiver')
    parser.add_argument('--port', type=str, help='Serial port (e.g., COM5, /dev/ttyACM0)')
    parser.add_argument('--baud', type=int, default=115200, help='Baud rate (default: 115200)')
    parser.add_argument('--verbose', action='store_true', help='Print all serial output')
    args = parser.parse_args()

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

    print(f"Connected. Waiting for commands...")
    print(f"Supported command types: {', '.join(SERIAL_SUPPORTED_TYPES)}")
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

            if line.startswith(DATA_PREFIX):
                json_str = line[len(DATA_PREFIX):]
                try:
                    payload = json.loads(json_str)
                    print(f"Received command: {json.dumps(payload, indent=2)}")

                    # Execute the command directly
                    result = handle_command(payload)

                    # Log the result
                    status = result.get("status", "unknown")
                    cmd_type = result.get("type", "unknown")
                    if status == "success":
                        print(f"[OK] {cmd_type} executed successfully")
                        if result.get("stdout"):
                            print(f"  stdout: {result['stdout'].strip()}")
                        if result.get("output"):
                            print(f"  output: {result['output'].strip()}")
                        if result.get("message"):
                            print(f"  message: {result['message']}")
                    else:
                        print(f"[ERR] {cmd_type} failed: {result.get('error_message', 'unknown error')}")

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
