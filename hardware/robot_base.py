import time
from abc import ABC, abstractmethod
from pathlib import Path

try:
    import cv2
except ImportError:
    cv2 = None


class DrivebaseBase(ABC):
    @abstractmethod
    def setLeft(self, power): pass

    @abstractmethod
    def setRight(self, power): pass

    @abstractmethod
    def cleanup(self): pass

    def drive_instant(self, left, right):
        self.setLeft(left)
        self.setRight(right)

    def drive(self, left, right, duration):
        self.setLeft(left)
        self.setRight(right)
        time.sleep(duration)
        self.setLeft(0)
        self.setRight(0)

    def forward(self, power, duration=None):
        if duration is None:
            self.drive_instant(power, power)
        else:
            self.drive(power, power, duration)

    def turn_left(self, power, duration=None):
        p = abs(power)
        if duration is None:
            self.drive_instant(-p, p)
        else:
            self.drive(-p, p, duration)

    def turn_right(self, power, duration=None):
        p = abs(power)
        if duration is None:
            self.drive_instant(p, -p)
        else:
            self.drive(p, -p, duration)

    def stop(self):
        self.drive_instant(0, 0)


class RockerBogieBase(ABC):
    @abstractmethod
    def setPositions(self, positions): pass

    def toSunPosition(self):
        self.setPositions([150, 35, 90, 90])

    def toRegularPosition(self):
        self.setPositions([90, 90, 150, 30])


class Camera:
    def __init__(self, camera_index=0):
        self.camera = cv2.VideoCapture(camera_index)
        if not self.camera.isOpened():
            raise RuntimeError(f"Failed to open camera at index {camera_index}")
        time.sleep(0.5)

    def capture(self):
        ret, frame = self.camera.read()
        if not ret:
            raise RuntimeError("Failed to capture frame from camera")
        return frame

    def save_as_png(self, image, filepath):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        png_path = f"{filepath}.png"
        cv2.imwrite(png_path, image)
        return png_path

    def capture_and_save(self, filepath):
        image = self.capture()
        return self.save_as_png(image, filepath)

    def release(self):
        if self.camera is not None:
            self.camera.release()


class Rover:
    def __init__(self, drivebase: DrivebaseBase, rocker_bogie: RockerBogieBase):
        self.drivebase = drivebase
        self.rocker_bogie = rocker_bogie
        self.camera = None

    def set_left_motor(self, power):
        self.drivebase.setLeft(power)

    def set_right_motor(self, power):
        self.drivebase.setRight(power)

    def drive_instant(self, left, right):
        self.drivebase.drive_instant(left, right)

    def drive(self, left, right, duration):
        self.drivebase.drive(left, right, duration)

    def forward(self, power, duration=None):
        self.drivebase.forward(power, duration)

    def turn_left(self, power, duration=None):
        self.drivebase.turn_left(power, duration)

    def turn_right(self, power, duration=None):
        self.drivebase.turn_right(power, duration)

    def stop(self):
        self.drivebase.stop()

    def set_servo_positions(self, positions):
        self.rocker_bogie.setPositions(positions)

    def setup_sun_position(self):
        self.rocker_bogie.toSunPosition()

    def setup_regular_position(self):
        self.rocker_bogie.toRegularPosition()

    def init_camera(self, camera_index=0):
        if self.camera is None:
            self.camera = Camera(camera_index)

    def take_picture(self, filepath):
        if self.camera is None:
            self.init_camera()
        return self.camera.capture_and_save(filepath)

    def cleanup(self):
        self.drivebase.cleanup()
        if self.camera is not None:
            self.camera.release()
