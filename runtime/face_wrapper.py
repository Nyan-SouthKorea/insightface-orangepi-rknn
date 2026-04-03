"""Import-friendly RKNN face recognition wrapper for app code and demos.

Smoke:
  python - <<'PY'
from runtime.face_wrapper import FaceWrapper
wrapper = FaceWrapper(gallery_dir='runtime/gallery')
print(type(wrapper.recognizer).__name__)
wrapper.close()
PY

Full:
  python runtime/web_backend/main.py --host 0.0.0.0 --port 5000 --capture-mode webcam --camera-source /dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0 --gallery-dir runtime/gallery --model-pack buffalo_m --model-zoo-root conversion/results/model_zoo

Main inputs:
  - `gallery_dir`: local gallery folder
  - `model_pack`: RKNN pack name such as `buffalo_m`
  - webcam or json frames from caller code

Main outputs:
  - per-frame recognition results
  - detection, embedding extraction, gallery matching helpers
"""

from __future__ import annotations

import gc
from pathlib import Path


def load_rknn_recognizer():
    try:
        from .rknn_face_gallery_recognizer import RknnFaceGalleryRecognizer
    except ImportError:
        from rknn_face_gallery_recognizer import RknnFaceGalleryRecognizer
    return RknnFaceGalleryRecognizer


def load_similarity_score():
    try:
        from .gallery_utils import similarity_score
    except ImportError:
        from gallery_utils import similarity_score
    return similarity_score


class FaceWrapper:
    """Small RKNN wrapper surface that app code can import directly."""

    def __init__(
        self,
        gallery_dir: str,
        model_pack: str = "buffalo_m",
        threshold: float = 0.7,
        det_size: int = 640,
        model_zoo_root: str | None = None,
    ):
        self.backend = "rknn"
        self.gallery_dir = Path(gallery_dir)
        self.model_pack = model_pack
        self.threshold = threshold
        self.det_size = det_size
        self.model_zoo_root = model_zoo_root

        RknnFaceGalleryRecognizer = load_rknn_recognizer()
        self.recognizer = RknnFaceGalleryRecognizer(
            gallery_dir=gallery_dir,
            model_pack=model_pack,
            threshold=threshold,
            det_size=det_size,
            model_zoo_root=model_zoo_root,
        )

    def reload_gallery(self):
        return self.recognizer.reload_gallery()

    def infer(self, frame):
        return self.recognizer.recognize(frame)

    def detect_faces(self, frame, max_num: int = 0):
        return self.recognizer.detect_faces(frame, max_num=max_num)

    def extract_face_embeddings(self, frame, max_num: int = 0):
        return self.recognizer.extract_face_embeddings(frame, max_num=max_num)

    def extract_embedding(self, frame, face_index: int = 0):
        return self.recognizer.extract_embedding(frame, face_index=face_index)

    def match_embedding(self, embedding, top_k: int = 5):
        return self.recognizer.match_embedding(embedding, top_k=top_k)

    def list_gallery_people(self):
        return self.recognizer.list_gallery_people()

    @staticmethod
    def compare_embeddings(embedding_1, embedding_2) -> float:
        return load_similarity_score()(embedding_1, embedding_2)

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
