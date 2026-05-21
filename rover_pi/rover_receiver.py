"""
Run on the rover (Jetson or Pi). Listens for UDP drive commands and controls motors.

Usage:
    python rover_receiver.py [--port 5005]

Auto-detects platform (Jetson vs Raspberry Pi) and imports the correct driver.
Safety: if no packet received within TIMEOUT seconds, motors stop automatically.
"""

import argparse
import json
import os
import socket
import sys
import threading
import time

# Make the sibling `hardware/` package importable when this script is run
# directly (e.g. `python rover_receiver.py`). The hardware drivers live in
# nasa-hera/hardware/ after the project reorganization.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hardware"))


TIMEOUT = 0.5  # seconds without a packet before emergency stop


def detect_and_import():
    try:
        from robot_jetson import make_rover
        print("Platform: Jetson Nano")
        return make_rover()
    except (ImportError, RuntimeError):
        pass
    try:
        from robot_rpi import make_rover
        print("Platform: Raspberry Pi")
        return make_rover()
    except (ImportError, RuntimeError) as e:
        raise RuntimeError("Could not load a rover driver. Is robot_jetson.py or robot_rpi.py present?") from e


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5005)
    args = parser.parse_args()

    rover = detect_and_import()
    rover.setup_regular_position()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", args.port))
    sock.settimeout(TIMEOUT)

    print(f"Listening on port {args.port} — drive commands expected at {1/TIMEOUT:.0f}+ Hz")

    last_packet = time.monotonic()
    watchdog_active = True

    def watchdog():
        while watchdog_active:
            if time.monotonic() - last_packet > TIMEOUT:
                rover.stop()
            time.sleep(0.1)

    t = threading.Thread(target=watchdog, daemon=True)
    t.start()

    try:
        while True:
            try:
                data, _ = sock.recvfrom(256)
                last_packet = time.monotonic()
                cmd = json.loads(data.decode())
                left = float(cmd.get("left", 0.0))
                right = float(cmd.get("right", 0.0))
                # Clamp to [-1, 1] so a bad packet can't overdrive motors
                left = max(-1.0, min(1.0, left))
                right = max(-1.0, min(1.0, right))
                rover.drive_instant(left, right)
            except socket.timeout:
                # Watchdog handles the stop; just loop
                pass
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        watchdog_active = False
        rover.stop()
        rover.cleanup()
        sock.close()


if __name__ == "__main__":
    main()
