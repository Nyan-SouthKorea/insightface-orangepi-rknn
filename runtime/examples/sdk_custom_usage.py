"""Custom embedding example for the RKNN face SDK on OrangePI.

Smoke:
  source ../envs/ifr_rknn_lite2_cp310/bin/activate
  python runtime/examples/sdk_custom_usage.py --image-path-a path/to/frame_a.jpg --gallery-dir runtime/gallery --model-pack buffalo_m

Full:
  source ../envs/ifr_rknn_lite2_cp310/bin/activate
  python runtime/examples/sdk_custom_usage.py --image-path-a path/to/frame_a.jpg --image-path-b path/to/frame_b.jpg --gallery-dir runtime/gallery --model-pack buffalo_m --top-k 3 --model-zoo-root conversion/results/model_zoo

Main inputs:
  - `--image-path-a`: 얼굴을 감지하고 임베딩을 뽑을 첫 번째 이미지
  - `--image-path-b`: 선택 사항. 두 번째 이미지와 직접 유사도를 비교할 때 사용
  - `--gallery-dir`: gallery 루트

Main outputs:
  - detection summary
  - first-face embedding summary
  - gallery top-k match summary
  - optional pairwise cosine similarity
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime import FaceSDK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-path-a", required=True)
    parser.add_argument("--image-path-b")
    parser.add_argument("--gallery-dir", default="runtime/gallery")
    parser.add_argument("--model-pack", default="buffalo_m")
    parser.add_argument("--threshold", type=float, default=0.6)
    parser.add_argument("--det-size", type=int, default=640)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--model-zoo-root", default="conversion/results/model_zoo")
    return parser


def embedding_summary(embedding: np.ndarray | None):
    if embedding is None:
        return None
    return {
        "shape": list(embedding.shape),
        "dtype": str(embedding.dtype),
        "l2_norm": round(float(np.linalg.norm(embedding)), 6),
    }


def main():
    args = build_parser().parse_args()
    image_a = cv2.imread(args.image_path_a)
    if image_a is None:
        raise FileNotFoundError(f"이미지를 읽지 못했습니다: {args.image_path_a}")

    image_b = None
    if args.image_path_b:
        image_b = cv2.imread(args.image_path_b)
        if image_b is None:
            raise FileNotFoundError(f"이미지를 읽지 못했습니다: {args.image_path_b}")

    sdk = FaceSDK(
        gallery_dir=args.gallery_dir,
        model_pack=args.model_pack,
        threshold=args.threshold,
        det_size=args.det_size,
        model_zoo_root=args.model_zoo_root,
    )
    try:
        detections = sdk.detect_faces(image_a)
        embeddings = sdk.extract_face_embeddings(image_a)
        first_embedding = embeddings[0]["embedding"] if embeddings else None

        payload = {
            "sdk": sdk.describe(),
            "gallery_people": sdk.list_gallery_people(),
            "detections_on_a": detections,
            "embedding_count_on_a": len(embeddings),
            "first_embedding": embedding_summary(first_embedding),
            "top_gallery_matches": sdk.match_embedding(first_embedding, top_k=args.top_k) if first_embedding is not None else [],
        }

        if image_b is not None:
            embedding_b = sdk.extract_embedding(image_b)
            payload["second_embedding"] = embedding_summary(embedding_b)
            payload["pair_similarity"] = (
                round(float(FaceSDK.compare_embeddings(first_embedding, embedding_b)), 6)
                if first_embedding is not None and embedding_b is not None
                else None
            )

        print(json.dumps(payload, indent=2, ensure_ascii=False))
    finally:
        sdk.close()


if __name__ == "__main__":
    main()
