"""Import-friendly face recognition wrapper for app code and demos.

Smoke:
  python - <<'PY'
from runtime.face_wrapper import FaceWrapper
wrapper = FaceWrapper(gallery_dir='runtime/gallery')
print(type(wrapper.recognizer).__name__)
PY

Full:
  python runtime/web_backend/main.py --host 0.0.0.0 --port 5000 \
    --capture-mode webcam \
    --camera-source /dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0 \
    --gallery-dir runtime/gallery \
    --model-pack buffalo_m \
    --backend rknn \
    --model-zoo-root conversion/results/model_zoo

Main inputs:
  - `gallery_dir`: local gallery folder
  - `backend`: `onnx` or `rknn`
  - webcam or json frames from caller code

Main outputs:
  - per-frame recognition results
"""

from __future__ import annotations

import gc
from pathlib import Path

def load_onnx_recognizer():
    try:
        from .face_gallery_recognizer import FaceGalleryRecognizer
    except ImportError:
        from face_gallery_recognizer import FaceGalleryRecognizer
    return FaceGalleryRecognizer


def load_rknn_recognizer():
    try:
        from .rknn_face_gallery_recognizer import RknnFaceGalleryRecognizer
    except ImportError:
        from rknn_face_gallery_recognizer import RknnFaceGalleryRecognizer
    return RknnFaceGalleryRecognizer


class FaceWrapper:
    """Small wrapper surface that app code can import directly."""

    def __init__(
        self,
        gallery_dir: str,
        model_pack: str = "buffalo_m",
        backend: str = "rknn",
        provider: str = "CPUExecutionProvider",
        threshold: float = 0.7,
        det_size: int = 640,
        model_zoo_root: str | None = None,
    ):
        self.backend = backend
        self.gallery_dir = Path(gallery_dir)
        self.model_pack = model_pack
        self.provider = provider
        self.threshold = threshold
        self.det_size = det_size
        self.model_zoo_root = model_zoo_root
        if backend == "onnx":
            FaceGalleryRecognizer = load_onnx_recognizer()
            self.recognizer = FaceGalleryRecognizer(
                gallery_dir=gallery_dir,
                model_pack=model_pack,
                provider=provider,
                threshold=threshold,
                det_size=det_size,
            )
        elif backend == "rknn":
            RknnFaceGalleryRecognizer = load_rknn_recognizer()
            self.recognizer = RknnFaceGalleryRecognizer(
                gallery_dir=gallery_dir,
                model_pack=model_pack,
                threshold=threshold,
                det_size=det_size,
                model_zoo_root=model_zoo_root,
            )
        else:
            raise ValueError(f"지원하지 않는 backend 입니다: {backend}")

    def reload_gallery(self):
        return self.recognizer.reload_gallery()

    def infer(self, frame):
        return self.recognizer.recognize(frame)

    @property
    def gallery_count(self) -> int:
        gallery = getattr(self.recognizer, "gallery", {})
        return len(gallery)

    def describe(self):
        info = {
            "backend": self.backend,
            "model_pack": self.model_pack,
            "gallery_dir": str(self.gallery_dir),
            "gallery_count": self.gallery_count,
            "threshold": self.threshold,
            "det_size": self.det_size,
        }
        pack_info = getattr(self.recognizer, "pack_info", None)
        if pack_info:
            info["resolved_model_pack"] = pack_info.get("model_pack")
            info["alias_of"] = pack_info.get("alias_of")
            info["detector_path"] = str(pack_info.get("detector_path"))
            info["recognizer_path"] = str(pack_info.get("recognizer_path"))
        return info

    def close(self):
        close_fn = getattr(self.recognizer, "close", None)
        if callable(close_fn):
            close_fn()
        self.recognizer = None
        gc.collect()
