"""Import-friendly face recognition wrapper for app code and demos.

Smoke:
  python - <<'PY'
from runtime.face_wrapper import FaceWrapper
wrapper = FaceWrapper(gallery_dir='runtime/gallery')
print(type(wrapper.recognizer).__name__)
PY

Full:
  python runtime/face_gallery_web_demo.py --host 0.0.0.0 --port 5000 \
    --capture-mode webcam --camera-source /dev/video21 --gallery-dir runtime/gallery \
    --model-pack buffalo_s --backend onnx --provider CPUExecutionProvider

Main inputs:
  - `gallery_dir`: local gallery folder
  - `backend`: `onnx` or `rknn`
  - webcam or json frames from caller code

Main outputs:
  - per-frame recognition results
"""

from __future__ import annotations

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
        model_pack: str = "buffalo_s",
        backend: str = "onnx",
        provider: str = "CPUExecutionProvider",
        threshold: float = 0.7,
        det_size: int = 640,
        model_zoo_root: str | None = None,
    ):
        self.backend = backend
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
