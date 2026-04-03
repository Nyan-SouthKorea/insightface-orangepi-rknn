"""Quick start example for the RKNN face SDK on OrangePI.

Smoke:
  source ../envs/ifr_rknn_lite2_cp310/bin/activate
  python runtime/examples/sdk_quickstart.py \
    --image-path path/to/frame.jpg \
    --gallery-dir runtime/gallery \
    --model-pack buffalo_m

Full:
  source ../envs/ifr_rknn_lite2_cp310/bin/activate
  python runtime/examples/sdk_quickstart.py \
    --image-path path/to/frame.jpg \
    --gallery-dir runtime/gallery \
    --model-pack buffalo_m \
    --backend rknn \
    --model-zoo-root conversion/results/model_zoo

Main inputs:
  - `--image-path`: cv2로 읽을 단일 이미지 경로
  - `--gallery-dir`: `runtime/gallery/<person_id>/meta.json` 구조의 gallery 루트
  - `--model-pack`: `buffalo_m`, `buffalo_m_i8`, `buffalo_sc` 같은 pack 이름

Main outputs:
  - SDK describe payload
  - gallery summary
  - `sdk.infer(frame)` 결과
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime import FaceSDK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-path", required=True)
    parser.add_argument("--gallery-dir", default="runtime/gallery")
    parser.add_argument("--model-pack", default="buffalo_m")
    parser.add_argument("--backend", default="rknn")
    parser.add_argument("--provider", default="CPUExecutionProvider")
    parser.add_argument("--threshold", type=float, default=0.6)
    parser.add_argument("--det-size", type=int, default=640)
    parser.add_argument("--model-zoo-root", default="conversion/results/model_zoo")
    return parser


def main():
    args = build_parser().parse_args()
    frame = cv2.imread(args.image_path)
    if frame is None:
        raise FileNotFoundError(f"이미지를 읽지 못했습니다: {args.image_path}")

    sdk = FaceSDK(
        gallery_dir=args.gallery_dir,
        model_pack=args.model_pack,
        backend=args.backend,
        provider=args.provider,
        threshold=args.threshold,
        det_size=args.det_size,
        model_zoo_root=args.model_zoo_root,
    )
    try:
        payload = {
            "sdk": sdk.describe(),
            "gallery_people": sdk.list_gallery_people(),
            "results": sdk.infer(frame),
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    finally:
        sdk.close()


if __name__ == "__main__":
    main()
