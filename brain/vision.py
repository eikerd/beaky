"""Vision module — webcam capture and scene description via Ollama vision model."""

import base64
import io
import logging

import cv2
import ollama
from PIL import Image

import config

log = logging.getLogger(__name__)


class Vision:
    def __init__(self, model: str = config.VISION_MODEL, camera_index: int = config.WEBCAM_INDEX):
        self.model = model
        self.camera_index = camera_index
        self.client = ollama.Client(host=config.OLLAMA_HOST)
        self._cap: cv2.VideoCapture | None = None

    def open_camera(self):
        if self._cap is None or not self._cap.isOpened():
            self._cap = cv2.VideoCapture(self.camera_index)
            if not self._cap.isOpened():
                log.error("Failed to open webcam %s", self.camera_index)
                raise RuntimeError(f"Cannot open webcam {self.camera_index}")
            log.info("Webcam %s opened", self.camera_index)

    def close_camera(self):
        if self._cap and self._cap.isOpened():
            self._cap.release()
            self._cap = None
            log.info("Webcam closed")

    def capture_frame(self) -> bytes:
        """Capture a single frame and return it as JPEG bytes."""
        self.open_camera()
        ret, frame = self._cap.read()
        if not ret:
            raise RuntimeError("Failed to capture frame from webcam")
        # Convert BGR → RGB, then encode as JPEG
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()

    def capture_frame_raw(self):
        """Capture a single frame and return it as a numpy BGR array (for face_recognition)."""
        self.open_camera()
        ret, frame = self._cap.read()
        if not ret:
            raise RuntimeError("Failed to capture frame from webcam")
        return frame

    def describe_scene(self, image_bytes: bytes | None = None) -> str:
        """Take a snapshot (or use provided bytes) and return a text description."""
        if image_bytes is None:
            image_bytes = self.capture_frame()

        b64 = base64.b64encode(image_bytes).decode("utf-8")

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": config.VISION_PROMPT,
                    "images": [b64],
                }
            ],
        )
        description = response["message"]["content"]
        log.info("Scene description: %s", description)
        return description

    def __del__(self):
        self.close_camera()
