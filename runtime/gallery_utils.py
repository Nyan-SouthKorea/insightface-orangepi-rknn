from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def imread_local(path: Path):
    """Read local images while tolerating Korean filenames."""
    try:
        return cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception:
        return cv2.imread(str(path))


def parse_identity(folder_name: str):
    """Parse `한글이름, EnglishName` and also accept a single-name folder."""
    parts = [part.strip() for part in folder_name.split(",", 1)]
    if len(parts) == 2 and parts[0] and parts[1]:
        return parts[0], parts[1]
    single_name = folder_name.strip()
    return single_name, single_name


def similarity_score(embedding_1, embedding_2) -> float:
    normalized_1 = embedding_1 / np.linalg.norm(embedding_1)
    normalized_2 = embedding_2 / np.linalg.norm(embedding_2)
    cosine_similarity = float(np.dot(normalized_1, normalized_2))
    return max(0.0, min(1.0, (cosine_similarity + 1.0) / 2.0))


def average_top_similarity(embedding, gallery_embeddings, top_k: int = 2) -> float:
    similarities = sorted(
        (similarity_score(embedding, gallery_embedding) for gallery_embedding in gallery_embeddings),
        reverse=True,
    )
    top_similarities = similarities[: max(1, min(top_k, len(similarities)))]
    return float(np.mean(top_similarities))
