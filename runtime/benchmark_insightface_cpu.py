"""CPU benchmark for InsightFace buffalo model packs.

Smoke:
  python runtime/benchmark_insightface_cpu.py \
    --image-path runtime/results/face_benchmark_input.jpg \
    --model-packs buffalo_sc,buffalo_s \
    --repeat 5 --warmup 2 --provider CPUExecutionProvider

Full:
  python runtime/benchmark_insightface_cpu.py \
    --image-path runtime/results/face_benchmark_input.jpg \
    --model-packs buffalo_sc,buffalo_s,buffalo_m,buffalo_l \
    --repeat 20 --warmup 5 --provider CPUExecutionProvider \
    --output-json runtime/results/260401_0000_ort_cpu_benchmark/summary.json

Main inputs:
  - `--image-path`: single-face benchmark image
  - `--model-packs`: comma-separated buffalo model pack names

Main outputs:
  - stdout markdown table
  - optional json summary via `--output-json`
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import cv2
from insightface.app import FaceAnalysis
from insightface.app.common import Face


RELEASE_PACK_SIZE_MB = {
    "buffalo_sc": 14.3,
    "buffalo_s": 121.7,
    "buffalo_m": 263.2,
    "buffalo_l": 275.3,
}


def summarize_ms(values: list[float]) -> dict[str, float]:
    return {
        "avg_ms": round(sum(values) / len(values), 2),
        "median_ms": round(statistics.median(values), 2),
        "min_ms": round(min(values), 2),
        "max_ms": round(max(values), 2),
    }


def build_face(bbox, kps, det_score):
    return Face(
        bbox=bbox.copy(),
        kps=kps.copy() if kps is not None else None,
        det_score=det_score,
    )


def benchmark_pack(image, model_pack: str, provider: str, det_size: int, warmup: int, repeat: int):
    app = FaceAnalysis(
        name=model_pack,
        providers=[provider],
        allowed_modules=["detection", "recognition"],
    )
    app.prepare(ctx_id=-1, det_size=(det_size, det_size))

    det_model = app.models["detection"]
    rec_model = app.models["recognition"]

    bboxes, kpss = det_model.detect(image, max_num=1, metric="default")
    if bboxes.shape[0] == 0:
        raise RuntimeError(f"{model_pack}: benchmark image에서 얼굴을 찾지 못했습니다.")

    bbox = bboxes[0, 0:4]
    det_score = float(bboxes[0, 4])
    kps = kpss[0] if kpss is not None else None

    for _ in range(warmup):
        det_model.detect(image, max_num=1, metric="default")
        face = build_face(bbox, kps, det_score)
        rec_model.get(image, face)
        app.get(image, max_num=1)

    detection_samples = []
    for _ in range(repeat):
        started = time.perf_counter()
        det_model.detect(image, max_num=1, metric="default")
        detection_samples.append((time.perf_counter() - started) * 1000.0)

    recognition_samples = []
    for _ in range(repeat):
        face = build_face(bbox, kps, det_score)
        started = time.perf_counter()
        rec_model.get(image, face)
        recognition_samples.append((time.perf_counter() - started) * 1000.0)

    pipeline_samples = []
    for _ in range(repeat):
        started = time.perf_counter()
        app.get(image, max_num=1)
        pipeline_samples.append((time.perf_counter() - started) * 1000.0)

    return {
        "model_pack": model_pack,
        "provider": provider,
        "release_pack_size_mb": RELEASE_PACK_SIZE_MB.get(model_pack),
        "detection_model_file": Path(det_model.model_file).name,
        "recognition_model_file": Path(rec_model.model_file).name,
        "repeat": repeat,
        "warmup": warmup,
        "face_count": 1,
        "detection": summarize_ms(detection_samples),
        "recognition": summarize_ms(recognition_samples),
        "pipeline": summarize_ms(pipeline_samples),
        "pipeline_fps": round(1000.0 / (sum(pipeline_samples) / len(pipeline_samples)), 2),
    }


def to_markdown(rows: list[dict]) -> str:
    lines = [
        "| model pack | zip size MB | detection model | recognition model | detection avg ms | recognition avg ms | pipeline avg ms | pipeline FPS |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {model_pack} | {release_pack_size_mb} | {detection_model_file} | {recognition_model_file} | "
            "{det_avg} | {rec_avg} | {pipe_avg} | {pipeline_fps} |".format(
                model_pack=row["model_pack"],
                release_pack_size_mb=row["release_pack_size_mb"],
                detection_model_file=row["detection_model_file"],
                recognition_model_file=row["recognition_model_file"],
                det_avg=row["detection"]["avg_ms"],
                rec_avg=row["recognition"]["avg_ms"],
                pipe_avg=row["pipeline"]["avg_ms"],
                pipeline_fps=row["pipeline_fps"],
            )
        )
    return "\n".join(lines)


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-path", required=True)
    parser.add_argument("--model-packs", default="buffalo_sc,buffalo_s,buffalo_m,buffalo_l")
    parser.add_argument("--provider", default="CPUExecutionProvider")
    parser.add_argument("--det-size", type=int, default=640)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--repeat", type=int, default=20)
    parser.add_argument("--output-json")
    return parser


def main():
    args = build_parser().parse_args()
    image = cv2.imread(args.image_path)
    if image is None:
        raise FileNotFoundError(f"이미지를 읽지 못했습니다: {args.image_path}")

    rows = []
    for model_pack in [item.strip() for item in args.model_packs.split(",") if item.strip()]:
        rows.append(
            benchmark_pack(
                image=image,
                model_pack=model_pack,
                provider=args.provider,
                det_size=args.det_size,
                warmup=args.warmup,
                repeat=args.repeat,
            )
        )

    summary = {
        "image_path": args.image_path,
        "provider": args.provider,
        "det_size": args.det_size,
        "warmup": args.warmup,
        "repeat": args.repeat,
        "results": rows,
        "markdown_table": to_markdown(rows),
    }

    print(summary["markdown_table"])

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
        print(f"\njson saved: {output_path}")


if __name__ == "__main__":
    main()
