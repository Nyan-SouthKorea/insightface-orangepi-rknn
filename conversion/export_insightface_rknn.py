"""Export a single InsightFace ONNX model to RKNN.

Smoke:
  source ../envs/ifr_rknn_host_cp310/bin/activate
  python conversion/export_insightface_rknn.py \
    --onnx-path ~/.insightface/models/buffalo_sc/det_500m.onnx \
    --output-rknn-path conversion/results/model_zoo/rk3588/buffalo_sc/det_500m_fp16.rknn \
    --model-kind detection \
    --input-shape 1,3,640,640 \
    --target-platform rk3588 \
    --dtype fp

Full:
  source ../envs/ifr_rknn_host_cp310/bin/activate
  python conversion/export_insightface_rknn.py \
    --onnx-path ~/.insightface/models/buffalo_sc/w600k_mbf.onnx \
    --output-rknn-path conversion/results/model_zoo/rk3588/buffalo_sc/w600k_mbf_fp16.rknn \
    --model-kind recognition \
    --input-shape 1,3,112,112 \
    --target-platform rk3588 \
    --dtype fp

Main inputs:
  - `--onnx-path`: source ONNX path
  - `--input-shape`: fixed input shape used for RKNN build
  - `--model-kind`: detection or recognition
  - `--dataset`: optional quantization dataset path

Main outputs:
  - `--output-rknn-path`: exported RKNN file
  - sibling `*.json`: export metadata
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import onnx
from rknn.api import RKNN


MODEL_PRESETS = {
    "detection": {
        "mean_values": [[127.5, 127.5, 127.5]],
        "std_values": [[128.0, 128.0, 128.0]],
    },
    "recognition": {
        "mean_values": [[127.5, 127.5, 127.5]],
        "std_values": [[127.5, 127.5, 127.5]],
    },
}


def parse_csv_ints(text: str) -> list[int]:
    return [int(item.strip()) for item in text.split(",") if item.strip()]


def parse_csv_names(text: str | None) -> list[str] | None:
    if not text:
        return None
    values = [item.strip() for item in text.split(",") if item.strip()]
    return values or None


def auto_inputs_for_dynamic_model(onnx_path: Path, cli_inputs: list[str] | None) -> list[str] | None:
    if cli_inputs:
        return cli_inputs

    model = onnx.load(str(onnx_path))
    if not model.graph.input:
        return None

    first_input = model.graph.input[0]
    dims = []
    dynamic_found = False
    for dim in first_input.type.tensor_type.shape.dim:
        if dim.dim_value:
            dims.append(dim.dim_value)
            continue
        dims.append(dim.dim_param or "?")
        dynamic_found = True

    if dynamic_found:
        print(f"auto inputs: dynamic input detected, use {first_input.name} with shape template {dims}")
        return [first_input.name]
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--onnx-path", required=True)
    parser.add_argument("--output-rknn-path", required=True)
    parser.add_argument("--model-kind", choices=sorted(MODEL_PRESETS), required=True)
    parser.add_argument("--input-shape", required=True, help="Example: 1,3,640,640")
    parser.add_argument("--target-platform", default="rk3588")
    parser.add_argument("--dtype", choices=["fp", "i8"], default="fp")
    parser.add_argument("--dataset")
    parser.add_argument("--inputs")
    parser.add_argument("--outputs")
    parser.add_argument("--float-dtype", default="float16")
    parser.add_argument("--optimization-level", type=int, default=3)
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    onnx_path = Path(args.onnx_path).expanduser().resolve()
    output_path = Path(args.output_rknn_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.dtype != "fp" and not args.dataset:
        raise ValueError("양자화 변환에는 --dataset 이 필요합니다.")

    preset = MODEL_PRESETS[args.model_kind]
    input_shape = parse_csv_ints(args.input_shape)
    inputs = auto_inputs_for_dynamic_model(onnx_path, parse_csv_names(args.inputs))
    outputs = parse_csv_names(args.outputs)

    rknn = RKNN(verbose=args.verbose)
    try:
        print("--> config")
        ret = rknn.config(
            mean_values=preset["mean_values"],
            std_values=preset["std_values"],
            target_platform=args.target_platform,
            float_dtype=args.float_dtype,
            optimization_level=args.optimization_level,
        )
        if ret != 0:
            raise RuntimeError(f"rknn.config 실패: {ret}")

        print("--> load onnx")
        ret = rknn.load_onnx(
            model=str(onnx_path),
            inputs=inputs,
            input_size_list=[input_shape],
            outputs=outputs,
        )
        if ret != 0:
            raise RuntimeError(f"rknn.load_onnx 실패: {ret}")

        print("--> build")
        ret = rknn.build(
            do_quantization=(args.dtype != "fp"),
            dataset=args.dataset,
        )
        if ret != 0:
            raise RuntimeError(f"rknn.build 실패: {ret}")

        print("--> export")
        ret = rknn.export_rknn(str(output_path))
        if ret != 0:
            raise RuntimeError(f"rknn.export_rknn 실패: {ret}")
    finally:
        rknn.release()

    metadata = {
        "onnx_path": str(onnx_path),
        "output_rknn_path": str(output_path),
        "model_kind": args.model_kind,
        "input_shape": input_shape,
        "target_platform": args.target_platform,
        "dtype": args.dtype,
        "dataset": args.dataset,
        "inputs": inputs,
        "outputs": outputs,
        "mean_values": preset["mean_values"],
        "std_values": preset["std_values"],
        "float_dtype": args.float_dtype,
        "optimization_level": args.optimization_level,
    }
    metadata_path = output_path.with_suffix(".json")
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

    print("done:", output_path)
    print("metadata:", metadata_path)


if __name__ == "__main__":
    main()
