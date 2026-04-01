"""Benchmark RKNN face packs on OrangePI with the SDK runtime path.

Smoke:
  source ../envs/ifr_rknn_lite2_cp310/bin/activate
  python runtime/benchmark_rknn_face_sdk.py \
    --image-path runtime/results/face_benchmark_input.jpg \
    --gallery-dir runtime/gallery \
    --model-packs buffalo_m,buffalo_m_i8 \
    --repeat 5 --warmup 2

Full:
  source ../envs/ifr_rknn_lite2_cp310/bin/activate
  python runtime/benchmark_rknn_face_sdk.py \
    --image-path runtime/results/face_benchmark_input.jpg \
    --gallery-dir runtime/gallery \
    --model-packs buffalo_sc,buffalo_m,buffalo_m_i8,buffalo_l \
    --repeat 20 --warmup 5 \
    --output-json runtime/results/260401_0000_rknn_face_sdk_benchmark/summary.json

Main inputs:
  - `--image-path`: single-face benchmark image
  - `--gallery-dir`: gallery root used by runtime SDK
  - `--model-packs`: comma-separated RKNN pack names

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

from runtime.rknn_face_gallery_recognizer import RknnFaceGalleryRecognizer, norm_crop


def summarize_ms(values: list[float]) -> dict[str, float]:
    return {
        "avg_ms": round(sum(values) / len(values), 2),
        "median_ms": round(statistics.median(values), 2),
        "min_ms": round(min(values), 2),
        "max_ms": round(max(values), 2),
    }


def benchmark_pack(
    image,
    gallery_dir: str,
    model_pack: str,
    det_size: int,
    warmup: int,
    repeat: int,
    threshold: float,
    model_zoo_root: str,
):
    load_started = time.perf_counter()
    recognizer = RknnFaceGalleryRecognizer(
        gallery_dir=gallery_dir,
        model_pack=model_pack,
        threshold=threshold,
        det_size=det_size,
        model_zoo_root=model_zoo_root,
    )
    load_ms = (time.perf_counter() - load_started) * 1000.0

    try:
        dets, kpss = recognizer.detector.detect(image, max_num=1)
        if dets.shape[0] == 0:
            raise RuntimeError(f"{model_pack}: benchmark image에서 얼굴을 찾지 못했습니다.")

        aligned = norm_crop(image, kpss[0], image_size=recognizer.recognizer.input_size[0])

        for _ in range(warmup):
            recognizer.detector.detect(image, max_num=1)
            recognizer.recognizer.get_feat(aligned)
            recognizer.recognize(image)

        detection_samples = []
        for _ in range(repeat):
            started = time.perf_counter()
            recognizer.detector.detect(image, max_num=1)
            detection_samples.append((time.perf_counter() - started) * 1000.0)

        recognition_samples = []
        for _ in range(repeat):
            started = time.perf_counter()
            recognizer.recognizer.get_feat(aligned)
            recognition_samples.append((time.perf_counter() - started) * 1000.0)

        pipeline_samples = []
        latest_result = []
        for _ in range(repeat):
            started = time.perf_counter()
            latest_result = recognizer.recognize(image)
            pipeline_samples.append((time.perf_counter() - started) * 1000.0)

        top_result = latest_result[0] if latest_result else {}
        return {
            "model_pack": model_pack,
            "status": "ok",
            "resolved_model_pack": recognizer.pack_info.get("model_pack"),
            "dtype": recognizer.pack_info.get("pack_manifest", {}).get("dtype"),
            "load_ms": round(load_ms, 2),
            "warmup": warmup,
            "repeat": repeat,
            "gallery_count": len(recognizer.gallery),
            "detector_model": Path(recognizer.pack_info["detector_path"]).name,
            "recognizer_model": Path(recognizer.pack_info["recognizer_path"]).name,
            "detection": summarize_ms(detection_samples),
            "recognition": summarize_ms(recognition_samples),
            "pipeline": summarize_ms(pipeline_samples),
            "pipeline_fps": round(1000.0 / (sum(pipeline_samples) / len(pipeline_samples)), 2),
            "top_name": top_result.get("en_name", "Unknown"),
            "top_similarity": round(float(top_result.get("similarity", 0.0)), 4),
            "top_det_score": round(float(top_result.get("det_score", 0.0)), 4),
        }
    finally:
        recognizer.close()


def to_markdown(rows: list[dict]) -> str:
    lines = [
        "| model pack | status | resolved | dtype | load ms | detection avg ms | recognition avg ms | pipeline avg ms | pipeline FPS | top result | similarity |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in rows:
        if row["status"] != "ok":
            lines.append(
                f"| {row['model_pack']} | {row['status']} | - | - | - | - | - | - | - | - | - |"
            )
            continue
        lines.append(
            "| {model_pack} | {status} | {resolved_model_pack} | {dtype} | {load_ms} | {det_avg} | {rec_avg} | {pipe_avg} | {pipeline_fps} | {top_name} | {top_similarity} |".format(
                model_pack=row["model_pack"],
                status=row["status"],
                resolved_model_pack=row["resolved_model_pack"],
                dtype=row["dtype"],
                load_ms=row["load_ms"],
                det_avg=row["detection"]["avg_ms"],
                rec_avg=row["recognition"]["avg_ms"],
                pipe_avg=row["pipeline"]["avg_ms"],
                pipeline_fps=row["pipeline_fps"],
                top_name=row["top_name"],
                top_similarity=row["top_similarity"],
            )
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-path", required=True)
    parser.add_argument("--gallery-dir", default="runtime/gallery")
    parser.add_argument("--model-packs", default="buffalo_m,buffalo_m_i8")
    parser.add_argument("--det-size", type=int, default=640)
    parser.add_argument("--threshold", type=float, default=0.6)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--repeat", type=int, default=20)
    parser.add_argument("--model-zoo-root", default="conversion/results/model_zoo")
    parser.add_argument("--output-json")
    return parser


def main():
    args = build_parser().parse_args()
    image = cv2.imread(args.image_path)
    if image is None:
        raise FileNotFoundError(f"이미지를 읽지 못했습니다: {args.image_path}")

    rows = []
    for model_pack in [item.strip() for item in args.model_packs.split(",") if item.strip()]:
        try:
            rows.append(
                benchmark_pack(
                    image=image,
                    gallery_dir=args.gallery_dir,
                    model_pack=model_pack,
                    det_size=args.det_size,
                    warmup=args.warmup,
                    repeat=args.repeat,
                    threshold=args.threshold,
                    model_zoo_root=args.model_zoo_root,
                )
            )
        except Exception as exc:
            rows.append({"model_pack": model_pack, "status": f"error: {exc}"})

    summary = {
        "image_path": args.image_path,
        "gallery_dir": args.gallery_dir,
        "model_zoo_root": args.model_zoo_root,
        "threshold": args.threshold,
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
