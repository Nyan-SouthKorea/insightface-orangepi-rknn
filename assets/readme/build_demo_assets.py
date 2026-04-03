"""Build README demo assets from local demo media.

Smoke:
  python assets/readme/build_demo_assets.py --dry-run

Full:
  python assets/readme/build_demo_assets.py

Main inputs:
  - `사용자 추가 폴더/*.mp4`
  - `사용자 추가 폴더/*.png`

Main outputs:
  - `assets/readme/*.gif`
  - `assets/readme/*.png`
  - `assets/readme/demo_assets.json`
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = REPO_ROOT / "사용자 추가 폴더"
OUTPUT_DIR = REPO_ROOT / "assets" / "readme"
TMP_DIR = OUTPUT_DIR / ".tmp"


VIDEO_SPECS = [
    {
        "source": "1_데모 영상.mp4",
        "output": "demo_live-recognition_ryan.gif",
        "title": "Live Recognition",
        "caption": "실시간 얼굴 인식 화면. 동일 인물을 `라이언 / Ryan`으로 안정적으로 식별하는 데모.",
        "identity": {"name_ko": "라이언", "name_en": "Ryan", "confidence": "high"},
        "identity_basis": [
            "등록 영상에서 동일 인물 프로필 `라이언 / Ryan`이 생성된다.",
            "샘플링한 프레임의 overlay 라벨이 `라이언 / Ryan`으로 반복된다.",
            "현재 OrangePI gallery metadata도 `라이언 / Ryan` 1명으로 일치한다.",
        ],
        "sampled_frame_indices": [30, 120, 240],
        "start_seconds": 0.6,
        "duration_seconds": 5.0,
        "gif_fps": 7,
        "width": 840,
    },
    {
        "source": "2_모델 변경.mp4",
        "output": "demo_model-switching_ryan.gif",
        "title": "Model Switching",
        "caption": "web console에서 `buffalo_l`, `buffalo_m_i8`, `buffalo_sc`를 바꿔 가며 같은 인물을 유지하는 데모.",
        "identity": {"name_ko": "라이언", "name_en": "Ryan", "confidence": "high"},
        "identity_basis": [
            "모델 변경 전후 프레임에서 동일 인물 face box와 overlay 이름이 유지된다.",
            "프레임 샘플에 `Ryan` 라벨이 반복적으로 나타난다.",
        ],
        "sampled_frame_indices": [30, 150, 280],
        "start_seconds": 0.6,
        "duration_seconds": 6.4,
        "gif_fps": 7,
        "width": 840,
    },
    {
        "source": "3_인물 등록.mp4",
        "output": "demo_gallery-registration_ryan.gif",
        "title": "Gallery Registration",
        "caption": "갤러리에서 새 인물을 만들고 `라이언 / Ryan` 이름으로 저장한 뒤 같은 세션에서 바로 인식에 반영하는 데모.",
        "identity": {"name_ko": "라이언", "name_en": "Ryan", "confidence": "high"},
        "identity_basis": [
            "등록 폼에 `라이언 / Ryan`이 직접 입력되고 저장된다.",
            "저장 직후 live stream overlay가 `라이언 / Ryan`으로 갱신된다.",
        ],
        "sampled_frame_indices": [30, 180, 330],
        "start_seconds": 0.4,
        "duration_seconds": 7.8,
        "gif_fps": 7,
        "width": 840,
    },
    {
        "source": "4_오렌지파이 리소스 모니터링.mp4",
        "output": "demo_npu-monitoring_ryan.gif",
        "title": "NPU Monitoring",
        "caption": "터미널 `rknpu/load`와 web console을 함께 띄워 RKNN 추론 중 NPU load 변화를 확인하는 데모.",
        "identity": {"name_ko": "라이언", "name_en": "Ryan", "confidence": "high"},
        "identity_basis": [
            "모니터링 영상의 live stream overlay 역시 `라이언 / Ryan`을 유지한다.",
            "동일한 서비스 세션에서 모델을 바꾸며 NPU load를 비교하는 장면이다.",
        ],
        "sampled_frame_indices": [60, 360, 720],
        "start_seconds": 0.5,
        "duration_seconds": 8.0,
        "gif_fps": 7,
        "width": 840,
    },
]


IMAGE_SPECS = [
    {
        "source": "orange pi information img.png",
        "output": "orangepi-5-ultra-overview.png",
        "title": "Orange Pi 5 Ultra Overview",
    },
    {
        "source": "RK3588s img.png",
        "output": "rk3588-family-badge.png",
        "title": "Rockchip RK3588 Family Badge",
    },
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_command(command: list[str], *, dry_run: bool = False) -> None:
    if dry_run:
        print("$", " ".join(command))
        return
    subprocess.run(command, check=True)


def ffprobe_video(path: Path) -> dict:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,duration,nb_frames",
        "-of",
        "json",
        str(path),
    ]
    output = subprocess.check_output(command)
    payload = json.loads(output)
    streams = payload.get("streams", [])
    if not streams:
        raise RuntimeError(f"비디오 메타데이터를 읽지 못했습니다: {path}")
    return streams[0]


def build_gif(spec: dict, *, dry_run: bool = False) -> dict:
    source_path = INPUT_DIR / spec["source"]
    output_path = OUTPUT_DIR / spec["output"]
    palette_path = TMP_DIR / f"{output_path.stem}_palette.png"
    video_meta = ffprobe_video(source_path)
    filter_expr = f"fps={spec['gif_fps']},scale={spec['width']}:-1:flags=lanczos"

    palette_command = [
        "ffmpeg",
        "-y",
        "-ss",
        str(spec["start_seconds"]),
        "-t",
        str(spec["duration_seconds"]),
        "-i",
        str(source_path),
        "-vf",
        f"{filter_expr},palettegen=stats_mode=diff",
        str(palette_path),
    ]
    gif_command = [
        "ffmpeg",
        "-y",
        "-ss",
        str(spec["start_seconds"]),
        "-t",
        str(spec["duration_seconds"]),
        "-i",
        str(source_path),
        "-i",
        str(palette_path),
        "-lavfi",
        f"{filter_expr}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5",
        "-loop",
        "0",
        str(output_path),
    ]
    run_command(palette_command, dry_run=dry_run)
    run_command(gif_command, dry_run=dry_run)
    if not dry_run and palette_path.exists():
        palette_path.unlink()

    return {
        "kind": "video_gif",
        "title": spec["title"],
        "caption": spec["caption"],
        "source_filename": spec["source"],
        "output_filename": spec["output"],
        "source_metadata": video_meta,
        "gif_config": {
            "start_seconds": spec["start_seconds"],
            "duration_seconds": spec["duration_seconds"],
            "gif_fps": spec["gif_fps"],
            "width": spec["width"],
        },
        "sampled_frame_indices": spec["sampled_frame_indices"],
        "inferred_identity": spec["identity"],
        "identity_basis": spec["identity_basis"],
    }


def copy_image(spec: dict, *, dry_run: bool = False) -> dict:
    source_path = INPUT_DIR / spec["source"]
    output_path = OUTPUT_DIR / spec["output"]
    if dry_run:
        print("$", "cp", source_path, output_path)
    else:
        shutil.copy2(source_path, output_path)
    return {
        "kind": "image_copy",
        "title": spec["title"],
        "source_filename": spec["source"],
        "output_filename": spec["output"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    manifest_items = []
    for spec in VIDEO_SPECS:
        manifest_items.append(build_gif(spec, dry_run=args.dry_run))
    for spec in IMAGE_SPECS:
        manifest_items.append(copy_image(spec, dry_run=args.dry_run))

    manifest = {
        "generated_at": utc_now_iso(),
        "input_dir": str(INPUT_DIR),
        "output_dir": str(OUTPUT_DIR),
        "items": manifest_items,
    }

    manifest_path = OUTPUT_DIR / "demo_assets.json"
    if args.dry_run:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
