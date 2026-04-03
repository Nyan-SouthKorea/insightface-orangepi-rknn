"""Probe a single RKNN model on OrangePI with RKNN Lite2.

Smoke:
  source ../envs/ifr_rknn_lite2_cp310/bin/activate
  python runtime/probe_rknn_lite2.py \
    --rknn-path conversion/results/model_zoo/rk3588/buffalo_sc/det_500m_fp16.rknn \
    --input-image path/to/frame.jpg \
    --model-kind detection \
    --input-size 640,640

Full:
  source ../envs/ifr_rknn_lite2_cp310/bin/activate
  python runtime/probe_rknn_lite2.py \
    --rknn-path conversion/results/model_zoo/rk3588/buffalo_sc/w600k_mbf_fp16.rknn \
    --input-image path/to/frame.jpg \
    --model-kind recognition \
    --input-size 112,112 \
    --output-json runtime/results/rknn_probe.json

Main inputs:
  - `--rknn-path`: exported RKNN file
  - `--input-image`: smoke image path
  - `--model-kind`: detection or recognition

Main outputs:
  - stdout output tensor summary
  - optional `--output-json`
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from rknnlite.api import RKNNLite


MODEL_PRESETS = {
    "detection": {"mean": 127.5, "std": 128.0},
    "recognition": {"mean": 127.5, "std": 127.5},
}


def parse_hw(text: str) -> tuple[int, int]:
    values = [int(item.strip()) for item in text.split(",") if item.strip()]
    if len(values) != 2:
        raise ValueError("--input-size 는 width,height 형식이어야 합니다.")
    return values[0], values[1]


def prepare_image(image_path: Path, model_kind: str, input_size: tuple[int, int]) -> np.ndarray:
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"이미지를 읽지 못했습니다: {image_path}")

    width, height = input_size
    if model_kind == "detection":
        src_h, src_w = image.shape[:2]
        im_ratio = float(src_h) / float(src_w)
        model_ratio = float(height) / float(width)
        if im_ratio > model_ratio:
            new_h = height
            new_w = int(new_h / im_ratio)
        else:
            new_w = width
            new_h = int(new_w * im_ratio)
        resized = cv2.resize(image, (new_w, new_h))
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        canvas[:new_h, :new_w, :] = resized
        image = canvas
    else:
        image = cv2.resize(image, (width, height))

    mean = MODEL_PRESETS[model_kind]["mean"]
    std = MODEL_PRESETS[model_kind]["std"]
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32)
    nchw = np.transpose(rgb, (2, 0, 1))[None, ...]
    return (nchw - mean) / std


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rknn-path", required=True)
    parser.add_argument("--input-image", required=True)
    parser.add_argument("--model-kind", choices=sorted(MODEL_PRESETS), required=True)
    parser.add_argument("--input-size", required=True, help="width,height")
    parser.add_argument("--output-json")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    input_size = parse_hw(args.input_size)
    tensor = prepare_image(Path(args.input_image), args.model_kind, input_size)

    rknn = RKNNLite(verbose=False)
    ret = rknn.load_rknn(args.rknn_path)
    if ret != 0:
        raise RuntimeError(f"load_rknn 실패: {ret}")

    ret = rknn.init_runtime()
    if ret != 0:
        raise RuntimeError(f"init_runtime 실패: {ret}")

    outputs = rknn.inference(inputs=[tensor])
    summary = {
        "rknn_path": args.rknn_path,
        "input_image": args.input_image,
        "model_kind": args.model_kind,
        "input_size": input_size,
        "num_outputs": len(outputs),
        "outputs": [
            {
                "index": index,
                "shape": list(output.shape),
                "dtype": str(output.dtype),
                "min": float(np.min(output)),
                "max": float(np.max(output)),
            }
            for index, output in enumerate(outputs)
        ],
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if args.output_json:
        output_json = Path(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    rknn.release()


if __name__ == "__main__":
    main()
