"""Prepare a local-only RKNN INT8 calibration image bundle.

Smoke:
  source ../envs/ifr_rknn_host_cp310/bin/activate
  python conversion/prepare_rknn_calibration_dataset.py \
    --output-dir conversion/results/calibration/buffalo_m_i8 \
    --source-glob 'path/to/calibration/*.jpg' \
    --snapshot-url http://<orangepi-host>:5000/api/snapshot.jpg \
    --snapshot-count 4 \
    --snapshot-interval 0.2

Full:
  source ../envs/ifr_rknn_host_cp310/bin/activate
  python conversion/prepare_rknn_calibration_dataset.py \
    --output-dir conversion/results/calibration/buffalo_m_i8 \
    --source-glob 'path/to/calibration/*.jpg' \
    --source-glob runtime/gallery/*/images/* \
    --snapshot-url http://<orangepi-host>:5000/api/snapshot.jpg \
    --snapshot-count 24 \
    --snapshot-interval 0.25

Main inputs:
  - `--source-glob`: existing local image glob, repeatable
  - `--snapshot-url`: optional live snapshot endpoint
  - `--snapshot-count`: number of live frames to capture
  - `--output-dir`: local-only calibration bundle directory

Main outputs:
  - `<output-dir>/images/*`
  - `<output-dir>/detector_dataset.txt`
  - `<output-dir>/recognizer_dataset.txt`
  - `<output-dir>/manifest.json`
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
import urllib.request
from pathlib import Path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--source-glob", action="append", default=[])
    parser.add_argument("--snapshot-url")
    parser.add_argument("--snapshot-count", type=int, default=0)
    parser.add_argument("--snapshot-interval", type=float, default=0.25)
    parser.add_argument("--snapshot-timeout", type=float, default=5.0)
    return parser


def iter_source_paths(patterns: list[str]) -> list[Path]:
    items: list[Path] = []
    for pattern in patterns:
        items.extend(sorted(Path().glob(pattern)))
    filtered = []
    for path in items:
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        filtered.append(path.resolve())
    return filtered


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_source_images(paths: list[Path], target_dir: Path) -> list[Path]:
    copied = []
    for index, source_path in enumerate(paths, start=1):
        target_path = target_dir / f"source-{index:03d}{source_path.suffix.lower()}"
        shutil.copy2(source_path, target_path)
        copied.append(target_path.resolve())
    return copied


def capture_snapshot_images(
    snapshot_url: str,
    count: int,
    interval: float,
    timeout: float,
    target_dir: Path,
) -> list[Path]:
    captured = []
    for index in range(1, count + 1):
        target_path = target_dir / f"snapshot-{index:03d}.jpg"
        with urllib.request.urlopen(snapshot_url, timeout=timeout) as response:
            content = response.read()
        target_path.write_bytes(content)
        captured.append(target_path.resolve())
        if index != count and interval > 0:
            time.sleep(interval)
    return captured


def write_dataset(path: Path, image_paths: list[Path]) -> None:
    lines = [str(image_path) for image_path in image_paths]
    path.write_text("\n".join(lines) + ("\n" if lines else ""))


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    image_dir = output_dir / "images"
    ensure_clean_dir(output_dir)
    image_dir.mkdir(parents=True, exist_ok=True)

    source_paths = iter_source_paths(args.source_glob)
    image_paths = copy_source_images(source_paths, image_dir)

    if args.snapshot_url and args.snapshot_count > 0:
        image_paths.extend(
            capture_snapshot_images(
                snapshot_url=args.snapshot_url,
                count=args.snapshot_count,
                interval=args.snapshot_interval,
                timeout=args.snapshot_timeout,
                target_dir=image_dir,
            )
        )

    if not image_paths:
        raise ValueError("캘리브레이션용 이미지를 하나도 확보하지 못했습니다.")

    detector_dataset_path = output_dir / "detector_dataset.txt"
    recognizer_dataset_path = output_dir / "recognizer_dataset.txt"
    write_dataset(detector_dataset_path, image_paths)
    write_dataset(recognizer_dataset_path, image_paths)

    manifest = {
        "output_dir": str(output_dir),
        "image_count": len(image_paths),
        "source_glob": args.source_glob,
        "snapshot_url": args.snapshot_url,
        "snapshot_count": args.snapshot_count,
        "snapshot_interval": args.snapshot_interval,
        "detector_dataset": str(detector_dataset_path),
        "recognizer_dataset": str(recognizer_dataset_path),
        "images": [str(path) for path in image_paths],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    print(f"images: {len(image_paths)}")
    print(f"detector dataset: {detector_dataset_path}")
    print(f"recognizer dataset: {recognizer_dataset_path}")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
