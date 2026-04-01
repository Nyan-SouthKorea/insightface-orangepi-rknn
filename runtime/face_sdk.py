"""Stable SDK-style surface for app code.

Smoke:
  python - <<'PY'
from runtime.face_sdk import FaceSDK
print([item['model_pack'] for item in FaceSDK.list_model_packs()])
PY

Full:
  python - <<'PY'
import cv2
from runtime.face_sdk import FaceSDK

sdk = FaceSDK(
    gallery_dir='runtime/gallery',
    model_pack='buffalo_m',
    backend='rknn',
)
frame = cv2.imread('runtime/results/face_benchmark_input.jpg')
print(sdk.describe())
print(sdk.infer(frame))
PY

Main inputs:
  - `gallery_dir`: local gallery folder
  - `backend`: `onnx` or `rknn`
  - `model_pack`: pack name such as `buffalo_sc`, `buffalo_m`

Main outputs:
  - per-frame recognition results
  - model pack inventory for UI or service code
"""

from __future__ import annotations

try:
    from .face_wrapper import FaceWrapper
    from .rknn_model_zoo import list_rknn_model_packs
except ImportError:
    from face_wrapper import FaceWrapper
    from rknn_model_zoo import list_rknn_model_packs


class FaceSDK(FaceWrapper):
    """SDK-style alias on top of FaceWrapper."""

    @staticmethod
    def list_model_packs(backend: str = "rknn", target_platform: str = "rk3588", model_zoo_root=None):
        if backend != "rknn":
            return []
        return list_rknn_model_packs(target_platform=target_platform, model_zoo_root=model_zoo_root)
