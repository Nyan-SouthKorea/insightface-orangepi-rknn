"""Export one or more InsightFace face-recognition packs to RKNN.

Smoke:
  source ../envs/ifr_rknn_host_cp310/bin/activate
  python conversion/export_insightface_pack_rknn.py \
    --model-packs buffalo_sc \
    --target-platform rk3588 \
    --dtype fp \
    --skip-existing

Full:
  source ../envs/ifr_rknn_host_cp310/bin/activate
  python conversion/export_insightface_pack_rknn.py \
    --model-packs buffalo_m_i8 \
    --target-platform rk3588 \
    --dtype i8 \
    --detector-dataset conversion/results/calibration/buffalo_m_i8/detector_dataset.txt \
    --recognizer-dataset conversion/results/calibration/buffalo_m_i8/recognizer_dataset.txt

Main inputs:
  - `--model-packs`: comma-separated pack names
  - `--insightface-root`: source model root, default `~/.insightface`
  - `--dtype`: `fp` or `i8`
  - `--dataset`: shared INT8 calibration dataset
  - `--detector-dataset`, `--recognizer-dataset`: role-specific INT8 calibration dataset

Main outputs:
  - `conversion/results/model_zoo/<platform>/<pack>/*.rknn`
  - sibling `*.json`
  - `pack.json` manifest for runtime/model-zoo code
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from export_insightface_rknn import export_single_model
except ImportError:
    from .export_insightface_rknn import export_single_model


FACE_PACK_PRESETS = {
    "buffalo_sc": {
        "detector": {
            "onnx_filename": "det_500m.onnx",
            "output_filename": "det_500m_fp16.rknn",
            "model_kind": "detection",
            "input_shape": [1, 3, 640, 640],
        },
        "recognizer": {
            "onnx_filename": "w600k_mbf.onnx",
            "output_filename": "w600k_mbf_fp16.rknn",
            "model_kind": "recognition",
            "input_shape": [1, 3, 112, 112],
        },
    },
    "buffalo_s": {
        "alias_of": "buffalo_sc",
        "note": "face-only 기준 det_500m, w600k_mbf는 buffalo_sc와 동일 SHA256",
        "auxiliary_onnx": ["1k3d68.onnx", "2d106det.onnx", "genderage.onnx"],
    },
    "buffalo_m": {
        "detector": {
            "onnx_filename": "det_2.5g.onnx",
            "output_filename": "det_2.5g_fp16.rknn",
            "model_kind": "detection",
            "input_shape": [1, 3, 640, 640],
        },
        "recognizer": {
            "onnx_filename": "w600k_r50.onnx",
            "output_filename": "w600k_r50_fp16.rknn",
            "model_kind": "recognition",
            "input_shape": [1, 3, 112, 112],
        },
    },
    "buffalo_l": {
        "detector": {
            "onnx_filename": "det_10g.onnx",
            "output_filename": "det_10g_fp16.rknn",
            "model_kind": "detection",
            "input_shape": [1, 3, 640, 640],
        },
        "recognizer": {
            "onnx_filename": "w600k_r50.onnx",
            "output_filename": "w600k_r50_fp16.rknn",
            "model_kind": "recognition",
            "input_shape": [1, 3, 112, 112],
        },
    },
    "buffalo_m_i8": {
        "source_pack": "buffalo_m",
        "detector": {
            "onnx_filename": "det_2.5g.onnx",
            "output_filename": "det_2.5g_fp16.rknn",
            "model_kind": "detection",
            "input_shape": [1, 3, 640, 640],
        },
        "recognizer": {
            "onnx_filename": "w600k_r50.onnx",
            "output_filename": "w600k_r50_fp16.rknn",
            "model_kind": "recognition",
            "input_shape": [1, 3, 112, 112],
        },
    },
}


def parse_csv_names(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-packs", required=True, help="Example: buffalo_sc,buffalo_m")
    parser.add_argument("--insightface-root", default="~/.insightface")
    parser.add_argument("--output-root", default="conversion/results/model_zoo")
    parser.add_argument("--target-platform", default="rk3588")
    parser.add_argument("--dtype", choices=["fp", "i8"], default="fp")
    parser.add_argument("--dataset")
    parser.add_argument("--detector-dataset")
    parser.add_argument("--recognizer-dataset")
    parser.add_argument("--float-dtype", default="float16")
    parser.add_argument("--optimization-level", type=int, default=3)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def resolve_pack_source_dir(insightface_root: Path, model_pack: str) -> Path:
    base_dir = insightface_root.expanduser().resolve() / "models" / model_pack
    if not base_dir.exists():
        raise FileNotFoundError(f"InsightFace pack 경로를 찾지 못했습니다: {base_dir}")

    direct_onnx = sorted(base_dir.glob("*.onnx"))
    if direct_onnx:
        return base_dir

    nested_dirs = []
    for child in sorted(base_dir.iterdir()):
        if child.is_dir() and any(child.glob("*.onnx")):
            nested_dirs.append(child)
    if len(nested_dirs) == 1:
        return nested_dirs[0]
    raise FileNotFoundError(f"ONNX 파일이 있는 pack 경로를 찾지 못했습니다: {base_dir}")


def load_existing_model_metadata(output_path: Path) -> dict | None:
    metadata_path = output_path.with_suffix(".json")
    if output_path.exists() and metadata_path.exists():
        return json.loads(metadata_path.read_text())
    return None


def output_filename_for_dtype(output_filename: str, dtype: str) -> str:
    if dtype == "fp":
        return output_filename
    return output_filename.replace("_fp16.rknn", "_int8.rknn")


def dataset_for_role(args: argparse.Namespace, role: str) -> str | None:
    if role == "detector":
        return args.detector_dataset or args.dataset
    if role == "recognizer":
        return args.recognizer_dataset or args.dataset
    return args.dataset


def export_pack_models(args: argparse.Namespace, model_pack: str) -> dict:
    preset = FACE_PACK_PRESETS[model_pack]
    pack_dir = Path(args.output_root).resolve() / args.target_platform / model_pack
    pack_dir.mkdir(parents=True, exist_ok=True)

    if "alias_of" in preset:
        manifest = {
            "model_pack": model_pack,
            "target_platform": args.target_platform,
            "dtype": args.dtype,
            "alias_of": preset["alias_of"],
            "face_only_alias": True,
            "note": preset["note"],
            "auxiliary_onnx": preset.get("auxiliary_onnx", []),
        }
        manifest_path = pack_dir / "pack.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        print("alias manifest:", manifest_path)
        return manifest

    source_pack = preset.get("source_pack", model_pack)
    source_dir = resolve_pack_source_dir(Path(args.insightface_root), source_pack)
    exported_models = {}

    for role in ("detector", "recognizer"):
        role_info = preset[role]
        onnx_path = source_dir / role_info["onnx_filename"]
        output_path = pack_dir / output_filename_for_dtype(role_info["output_filename"], args.dtype)
        role_dataset = dataset_for_role(args, role)

        metadata = None
        if args.skip_existing:
            metadata = load_existing_model_metadata(output_path)
            if metadata is not None:
                print("skip existing:", output_path)

        if metadata is None:
            metadata = export_single_model(
                onnx_path=onnx_path,
                output_rknn_path=output_path,
                model_kind=role_info["model_kind"],
                input_shape=role_info["input_shape"],
                target_platform=args.target_platform,
                dtype=args.dtype,
                dataset=role_dataset,
                float_dtype=args.float_dtype,
                optimization_level=args.optimization_level,
                verbose=args.verbose,
            )

        exported_models[role] = {
            "onnx_filename": role_info["onnx_filename"],
            "onnx_path": str(onnx_path),
            "output_filename": output_path.name,
            "output_rknn_path": str(output_path),
            "metadata_filename": output_path.with_suffix(".json").name,
            "model_kind": role_info["model_kind"],
            "input_shape": role_info["input_shape"],
            "dataset": role_dataset,
            "metadata": metadata,
        }

    manifest = {
        "model_pack": model_pack,
        "target_platform": args.target_platform,
        "dtype": args.dtype,
        "source_pack": source_pack,
        "source_pack_dir": str(source_dir),
        "models": exported_models,
    }
    manifest_path = pack_dir / "pack.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print("pack manifest:", manifest_path)
    return manifest


def main() -> None:
    args = parse_args()
    if args.dtype != "fp" and not (args.dataset or args.detector_dataset or args.recognizer_dataset):
        raise ValueError("양자화 변환에는 --dataset 또는 role별 dataset 인자가 필요합니다.")

    manifests = []
    for model_pack in parse_csv_names(args.model_packs):
        if model_pack not in FACE_PACK_PRESETS:
            raise ValueError(f"지원하지 않는 model pack 입니다: {model_pack}")
        print(f"==> export pack: {model_pack}")
        manifests.append(export_pack_models(args, model_pack))

    print("done packs:", ", ".join(item["model_pack"] for item in manifests))


if __name__ == "__main__":
    main()
