"""Frame sources for webcam and JSON image polling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

import cv2


class JsonImageReader:
    def __init__(self, json_path: str, cam_key: str, image_dir: str):
        self.json_path = Path(json_path)
        self.cam_key = cam_key
        self.image_dir = Path(image_dir)
        self.last_timestamp = 0

    def read(self):
        if not self.json_path.exists():
            return False, None

        try:
            payload = json.loads(self.json_path.read_text())
        except Exception:
            return False, None

        if self.cam_key not in payload:
            return False, None

        camera_info = payload[self.cam_key]
        timestamp = int(camera_info.get("timestamp", 0))
        if timestamp <= self.last_timestamp:
            return False, None

        image_name = camera_info.get("image_name")
        if not image_name:
            return False, None

        image_path = self.image_dir / image_name
        if not image_path.exists():
            return False, None

        frame = cv2.imread(str(image_path))
        if frame is None:
            return False, None

        self.last_timestamp = timestamp
        return True, frame


def _normalize_camera_source(camera_source: Union[str, int]) -> Union[str, int]:
    if isinstance(camera_source, int):
        return camera_source

    text = str(camera_source).strip()
    if text.isdigit():
        return int(text)
    return text


def open_webcam(camera_source: Union[str, int], width: int, height: int, fps: int):
    backend_candidates = []
    if hasattr(cv2, "CAP_V4L2"):
        backend_candidates.append(cv2.CAP_V4L2)
    backend_candidates.append(None)

    source = _normalize_camera_source(camera_source)
    last_capture = None
    for backend in backend_candidates:
        if backend is None:
            capture = cv2.VideoCapture(source)
        else:
            capture = cv2.VideoCapture(source, backend)
        last_capture = capture
        if not capture.isOpened():
            continue

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        capture.set(cv2.CAP_PROP_FPS, fps)
        if hasattr(cv2, "CAP_PROP_BUFFERSIZE"):
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return capture

    if last_capture is None:
        last_capture = cv2.VideoCapture(source)
    return last_capture
