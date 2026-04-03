"""Gallery-based face recognition using InsightFace on ONNX Runtime.

Smoke:
  python runtime/benchmark_insightface_cpu.py \
    --image-path runtime/results/face_benchmark_input.jpg \
    --model-packs buffalo_sc \
    --repeat 1 --warmup 1 \
    --provider CPUExecutionProvider

Full:
  python runtime/benchmark_insightface_cpu.py \
    --image-path runtime/results/face_benchmark_input.jpg \
    --model-packs buffalo_sc,buffalo_s,buffalo_m,buffalo_l \
    --repeat 20 --warmup 5 \
    --provider CPUExecutionProvider \
    --output-json runtime/results/ort_cpu_benchmark/summary.json

Main inputs:
  - `runtime/gallery/`: user folders with face images
  - camera frames or benchmark image input from the entry script

Main outputs:
  - recognition results for CPU benchmark or fallback runtime
"""

from __future__ import annotations

from pathlib import Path

import onnxruntime as ort
from insightface.app import FaceAnalysis
from tqdm import tqdm

try:
    from .gallery_store import GalleryStore
    from .gallery_utils import average_top_similarity, imread_local, similarity_score
except ImportError:
    from gallery_store import GalleryStore
    from gallery_utils import average_top_similarity, imread_local, similarity_score


class FaceGalleryRecognizer:
    def __init__(
        self,
        gallery_dir: str,
        model_pack: str = "buffalo_s",
        provider: str = "CPUExecutionProvider",
        threshold: float = 0.7,
        det_size: int = 640,
    ):
        self.gallery_dir = Path(gallery_dir)
        self.model_pack = model_pack
        self.provider = provider
        self.threshold = threshold
        self.det_size = det_size

        self.gallery_dir.mkdir(parents=True, exist_ok=True)
        self.gallery_store = GalleryStore(self.gallery_dir)

        available_providers = ort.get_available_providers()
        if provider not in available_providers:
            raise RuntimeError(
                f"요청한 provider `{provider}`를 찾지 못했습니다. "
                f"현재 사용 가능한 provider: {available_providers}"
            )

        providers = [provider]
        if provider != "CPUExecutionProvider":
            providers.append("CPUExecutionProvider")

        ctx_id = -1 if provider == "CPUExecutionProvider" else 0
        self.app = FaceAnalysis(name=model_pack, providers=providers)
        self.app.prepare(ctx_id=ctx_id, det_size=(det_size, det_size))

        self.gallery = {}
        self.reload_gallery()

    def reload_gallery(self):
        """Reload all gallery embeddings from disk."""
        loaded = {}
        targets = list(self.gallery_store.iter_embedding_targets())
        for target in tqdm(targets, desc="gallery load", leave=False):
            embeddings = []
            for image_path in target["image_paths"]:
                image = imread_local(image_path)
                if image is None:
                    continue
                faces = self.app.get(image)
                if not faces:
                    print(f"경고: {image_path}에서 얼굴을 찾지 못했습니다.")
                    continue
                embeddings.append(faces[0].embedding)
            if embeddings:
                loaded[target["person_id"]] = {
                    "person_id": target["person_id"],
                    "kr_name": target["name_ko"],
                    "en_name": target["name_en"],
                    "embeddings": embeddings,
                }

        self.gallery = loaded
        return loaded

    def list_gallery_people(self):
        return [
            {
                "person_id": info["person_id"],
                "kr_name": info["kr_name"],
                "en_name": info["en_name"],
                "embedding_count": len(info["embeddings"]),
            }
            for info in self.gallery.values()
        ]

    def detect_faces(self, frame, max_num: int = 0):
        faces = self.app.get(frame)
        if max_num > 0:
            faces = faces[:max_num]
        detections = []
        for face in faces:
            detections.append(
                {
                    "bbox": [int(value) for value in face.bbox],
                    "det_score": float(face.det_score),
                    "kps": face.kps.astype(float).tolist() if getattr(face, "kps", None) is not None else None,
                }
            )
        return detections

    def extract_face_embeddings(self, frame, max_num: int = 0):
        faces = self.app.get(frame)
        if max_num > 0:
            faces = faces[:max_num]
        embeddings = []
        for face in faces:
            embeddings.append(
                {
                    "bbox": [int(value) for value in face.bbox],
                    "det_score": float(face.det_score),
                    "kps": face.kps.astype(float).tolist() if getattr(face, "kps", None) is not None else None,
                    "embedding": face.embedding.copy(),
                }
            )
        return embeddings

    def extract_embedding(self, frame, face_index: int = 0):
        embeddings = self.extract_face_embeddings(frame, max_num=face_index + 1)
        if face_index >= len(embeddings):
            return None
        return embeddings[face_index]["embedding"]

    def match_embedding(self, embedding, top_k: int = 5):
        matches = []
        for info in self.gallery.values():
            matches.append(
                {
                    "person_id": info["person_id"],
                    "kr_name": info["kr_name"],
                    "en_name": info["en_name"],
                    "similarity": average_top_similarity(embedding, info["embeddings"]),
                    "embedding_count": len(info["embeddings"]),
                }
            )
        matches.sort(key=lambda item: item["similarity"], reverse=True)
        return matches[: max(1, top_k)]

    @staticmethod
    def compare_embeddings(embedding_1, embedding_2) -> float:
        return similarity_score(embedding_1, embedding_2)

    def recognize(self, frame):
        faces = self.app.get(frame)
        results = []
        for face in faces:
            bbox = [int(value) for value in face.bbox]
            if not self.gallery:
                results.append(
                    {
                        "kr_name": "미등록",
                        "en_name": "Unknown",
                        "similarity": 0.0,
                        "bbox": bbox,
                        "det_score": float(face.det_score),
                    }
                )
                continue

            matches = self.match_embedding(face.embedding, top_k=1)
            best_match = matches[0] if matches else None
            best_similarity = best_match["similarity"] if best_match else 0.0

            if best_match and best_similarity >= self.threshold:
                identity = self.gallery[best_match["person_id"]]
                kr_name = identity["kr_name"]
                en_name = identity["en_name"]
            else:
                kr_name = "미등록"
                en_name = "Unknown"

            results.append(
                {
                    "kr_name": kr_name,
                    "en_name": en_name,
                    "similarity": best_similarity,
                    "bbox": bbox,
                    "det_score": float(face.det_score),
                }
            )

        return results

    def close(self):
        self.app = None
