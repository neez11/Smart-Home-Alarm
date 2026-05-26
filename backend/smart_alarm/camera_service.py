from io import BytesIO
from threading import Lock
from time import sleep

from picamera2 import Picamera2
from PIL import Image

from config import ENABLE_CAMERA, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_JPEG_QUALITY


class CameraService:
    def __init__(self, state, logger=None):
        self.state = state
        self.logger = logger
        self.lock = Lock()
        self.picam2 = None
        self.ready = False

        if not ENABLE_CAMERA:
            self.state.camera_online = False
            return

        try:
            self.picam2 = Picamera2()
            config = self.picam2.create_video_configuration(
                main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT)}
            )
            self.picam2.configure(config)
            self.picam2.start()
            sleep(2)
            self.ready = True
            self.state.camera_online = True
            if self.logger:
                self.logger.info("Camera started successfully")
        except Exception as e:
            self.ready = False
            self.state.camera_online = False
            if self.logger:
                self.logger.error(f"Camera failed to start: {e}")

    def get_latest_image_bytes(self):
        if not self.ready or self.picam2 is None:
            return None

        try:
            with self.lock:
                frame = self.picam2.capture_array()
                image = Image.fromarray(frame).convert("RGB")
                output = BytesIO()
                image.save(output, format="JPEG", quality=CAMERA_JPEG_QUALITY)
                return output.getvalue()
        except Exception as e:
            self.state.camera_online = False
            if self.logger:
                self.logger.error(f"Failed to capture image: {e}")
            return None

    def close(self):
        try:
            if self.picam2 is not None:
                self.picam2.stop()
        except Exception:
            pass
