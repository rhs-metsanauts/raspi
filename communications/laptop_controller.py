"""
Run on your laptop. Reads Logitech F310 and streams drive commands to a rover over UDP.

Usage:
    python laptop_controller.py --ip <jetson-or-pi-ip> [--port 5005]

Controls (tank drive):
    Left stick Y  -> left motors
    Right stick Y -> right motors
    Start button  -> emergency stop
"""

import argparse
import json
import socket
import sys
import time

try:
    import pygame
except ImportError:
    sys.exit("pygame not installed — run: pip install pygame")

SEND_HZ = 20
DEADZONE = 0.05
LEFT_AXIS = 1   # F310 left stick Y
RIGHT_AXIS = 3  # F310 right stick Y
STOP_BUTTON = 7  # Start button


def apply_deadzone(value: float) -> float:
    return 0.0 if abs(value) < DEADZONE else value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", required=True, help="Rover IP address")
    parser.add_argument("--port", type=int, default=5005)
    args = parser.parse_args()

    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        sys.exit("No controller detected. Plug in the F310 and retry.")

    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"Controller: {js.get_name()}")
    print(f"Streaming to {args.ip}:{args.port} at {SEND_HZ}Hz — Ctrl+C to quit")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    interval = 1.0 / SEND_HZ

    try:
        while True:
            start = time.monotonic()
            pygame.event.pump()

            if js.get_button(STOP_BUTTON):
                left, right = 0.0, 0.0
            else:
                # Y axes are inverted on pygame: up = -1, so negate for forward = positive
                left = apply_deadzone(-js.get_axis(LEFT_AXIS))
                right = apply_deadzone(-js.get_axis(RIGHT_AXIS))

            packet = json.dumps({"left": round(left, 3), "right": round(right, 3)}).encode()
            sock.sendto(packet, (args.ip, args.port))

            elapsed = time.monotonic() - start
            time.sleep(max(0, interval - elapsed))

    except KeyboardInterrupt:
        # Send one final stop before exiting
        sock.sendto(json.dumps({"left": 0.0, "right": 0.0}).encode(), (args.ip, args.port))
        print("\nStopped.")
    finally:
        sock.close()
        pygame.quit()


if __name__ == "__main__":
    main()
