"""FastAPI backend entry for the new RKNN web demo.

Smoke:
  source ../envs/ifr_rknn_lite2_cp310/bin/activate
  python runtime/web_backend/main.py \
    --host 0.0.0.0 --port 5050 \
    --camera-source /dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0 \
    --gallery-dir runtime/gallery \
    --model-pack buffalo_m \
    --backend rknn

Full:
  source ../envs/ifr_rknn_lite2_cp310/bin/activate
  python runtime/web_backend/main.py \
    --host 0.0.0.0 --port 5000 \
    --camera-source /dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0 \
    --gallery-dir runtime/gallery \
    --model-pack buffalo_m \
    --backend rknn \
    --model-zoo-root conversion/results/model_zoo

Main inputs:
  - `runtime/gallery/`
  - `conversion/results/model_zoo/`
  - webcam or JSON image frames

Main outputs:
  - `http://<device-ip>:<port>/`
  - `http://<device-ip>:<port>/api/*`
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import uvicorn

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.web_backend.app import create_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--capture-mode", choices=["webcam", "json"], default="webcam")
    parser.add_argument("--camera-id", type=int, default=0)
    parser.add_argument("--camera-source")
    parser.add_argument("--camera-width", type=int, default=1280)
    parser.add_argument("--camera-height", type=int, default=720)
    parser.add_argument("--camera-fps", type=int, default=30)
    parser.add_argument("--json-path", default="cam_info.json")
    parser.add_argument("--cam-key", default="camera1")
    parser.add_argument("--image-dir", default="cam_images")
    parser.add_argument("--gallery-dir", default="runtime/gallery")
    parser.add_argument("--model-pack", default="buffalo_m")
    parser.add_argument("--backend", default="rknn")
    parser.add_argument("--provider", default="CPUExecutionProvider")
    parser.add_argument("--threshold", type=float, default=0.6)
    parser.add_argument("--det-size", type=int, default=640)
    parser.add_argument("--inference-fps", type=int, default=12)
    parser.add_argument("--stream-fps", type=int, default=15)
    parser.add_argument("--model-zoo-root", default="conversion/results/model_zoo")
    parser.add_argument("--target-platform", default="rk3588")
    parser.add_argument("--frontend-dist", default="runtime/web_frontend/dist")
    return parser


def main():
    args = build_parser().parse_args()
    args.frontend_dist = str(Path(args.frontend_dist))
    app = create_app(args)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
