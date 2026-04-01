"""Gallery-based face recognition using InsightFace on ONNX Runtime.

Smoke:
  python runtime/face_gallery_web_demo.py --host 0.0.0.0 --port 5000 \
    --capture-mode webcam --camera-id 0 --gallery-dir runtime/gallery \
    --model-pack buffalo_s --provider CPUExecutionProvider

Full:
  python runtime/face_gallery_web_demo.py --host 0.0.0.0 --port 5000 \
    --capture-mode json --json-path cam_info.json --cam-key camera1 \
    --image-dir cam_images --gallery-dir runtime/gallery \
    --model-pack buffalo_s --provider CPUExecutionProvider

Main inputs:
  - `runtime/gallery/`: user folders with face images
  - camera frames or JSON image frames from the entry script

Main outputs:
  - recognition results for the web demo overlay
"""

from __future__ import annotations

from pathlib import Path

import onnxruntime as ort
from insightface.app import FaceAnalysis
from tqdm import tqdm

try:
    from .gallery_utils import average_top_similarity, imread_local, parse_identity
except ImportError:
    from gallery_utils import average_top_similarity, imread_local, parse_identity


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
        folders = sorted(path for path in self.gallery_dir.iterdir() if path.is_dir())
        for folder in tqdm(folders, desc="gallery load", leave=False):
            kr_name, en_name = parse_identity(folder.name)
            embeddings = []
            for image_path in sorted(folder.iterdir()):
                if not image_path.is_file():
                    continue
                image = imread_local(image_path)
                if image is None:
                    continue
                faces = self.app.get(image)
                if not faces:
                    print(f"경고: {image_path}에서 얼굴을 찾지 못했습니다.")
                    continue
                embeddings.append(faces[0].embedding)
            if embeddings:
                loaded[en_name] = {
                    "kr_name": kr_name,
                    "en_name": en_name,
                    "embeddings": embeddings,
                }

        self.gallery = loaded
        return loaded

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

            best_en_name = "Unknown"
            best_similarity = 0.0
            for en_name, info in self.gallery.items():
                average_similarity = average_top_similarity(face.embedding, info["embeddings"])
                if average_similarity > best_similarity:
                    best_similarity = average_similarity
                    best_en_name = en_name

            if best_similarity >= self.threshold:
                identity = self.gallery[best_en_name]
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
