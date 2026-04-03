"""Gallery-based face recognition on RKNN Lite2.

Smoke:
  python - <<'PY'
from runtime.face_wrapper import FaceWrapper
wrapper = FaceWrapper(
    gallery_dir='runtime/gallery',
    model_pack='buffalo_sc',
    backend='rknn',
)
print(type(wrapper.recognizer).__name__)
PY

Full:
  python - <<'PY'
import cv2
from runtime.face_wrapper import FaceWrapper

wrapper = FaceWrapper(
    gallery_dir='runtime/gallery',
    model_pack='buffalo_sc',
    backend='rknn',
)
frame = cv2.imread('runtime/results/face_benchmark_input.jpg')
print(wrapper.infer(frame))
PY

Main inputs:
  - `conversion/results/model_zoo/<platform>/<pack>/`
  - `runtime/gallery/`
  - image frames

Main outputs:
  - per-frame recognition results
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

try:
    from rknnlite.api import RKNNLite
except ImportError:
    RKNNLite = None

try:
    from .gallery_store import GalleryStore
    from .gallery_utils import average_top_similarity, imread_local, similarity_score
    from .rknn_model_zoo import resolve_rknn_model_pack
except ImportError:
    from gallery_store import GalleryStore
    from gallery_utils import average_top_similarity, imread_local, similarity_score
    from rknn_model_zoo import resolve_rknn_model_pack


ARCFACE_DST = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float32,
)


def distance2bbox(points, distance):
    x1 = points[:, 0] - distance[:, 0]
    y1 = points[:, 1] - distance[:, 1]
    x2 = points[:, 0] + distance[:, 2]
    y2 = points[:, 1] + distance[:, 3]
    return np.stack([x1, y1, x2, y2], axis=-1)


def distance2kps(points, distance):
    preds = []
    for index in range(0, distance.shape[1], 2):
        px = points[:, index % 2] + distance[:, index]
        py = points[:, (index % 2) + 1] + distance[:, index + 1]
        preds.append(px)
        preds.append(py)
    return np.stack(preds, axis=-1)


def estimate_norm(landmark: np.ndarray, image_size: int = 112) -> np.ndarray:
    if image_size % 112 == 0:
        ratio = float(image_size) / 112.0
        diff_x = 0.0
    else:
        ratio = float(image_size) / 128.0
        diff_x = 8.0 * ratio
    dst = ARCFACE_DST * ratio
    dst[:, 0] += diff_x
    matrix, _ = cv2.estimateAffinePartial2D(
        landmark.astype(np.float32),
        dst.astype(np.float32),
        method=cv2.LMEDS,
    )
    if matrix is None:
        raise RuntimeError("얼굴 정렬 affine matrix 계산에 실패했습니다.")
    return matrix


def norm_crop(image: np.ndarray, landmark: np.ndarray, image_size: int = 112) -> np.ndarray:
    matrix = estimate_norm(landmark, image_size=image_size)
    return cv2.warpAffine(image, matrix, (image_size, image_size), borderValue=0.0)


class RknnLiteModel:
    def __init__(self, model_path: str | Path):
        if RKNNLite is None:
            raise ImportError(
                "rknnlite.api 를 찾지 못했습니다. "
                "OrangePI에서는 runtime/setup_orangepi_rknn_lite2_env.sh 환경을 사용하세요."
            )
        self.model_path = Path(model_path)
        self.runtime = RKNNLite(verbose=False)
        ret = self.runtime.load_rknn(str(self.model_path))
        if ret != 0:
            raise RuntimeError(f"load_rknn 실패: {self.model_path} / code={ret}")
        ret = self.runtime.init_runtime()
        if ret != 0:
            raise RuntimeError(f"init_runtime 실패: {self.model_path} / code={ret}")

    def infer(self, tensor: np.ndarray):
        return self.runtime.inference(inputs=[tensor], data_format="nhwc")

    def release(self):
        self.runtime.release()


class RknnScrfdDetector:
    def __init__(self, model_path: str | Path, metadata: dict | None = None):
        self.model = RknnLiteModel(model_path)
        self.metadata = metadata or {}
        input_shape = self.metadata.get("input_shape") or [1, 3, 640, 640]
        self.input_height = int(input_shape[2])
        self.input_width = int(input_shape[3])
        self.fmc = 3
        self.feat_stride_fpn = [8, 16, 32]
        self.num_anchors = 2
        self.use_kps = True
        self.nms_thresh = 0.4
        self.det_thresh = 0.5
        self.center_cache = {}

    def _prepare(self, image: np.ndarray):
        input_size = (self.input_width, self.input_height)
        im_ratio = float(image.shape[0]) / float(image.shape[1])
        model_ratio = float(input_size[1]) / float(input_size[0])
        if im_ratio > model_ratio:
            new_height = input_size[1]
            new_width = int(new_height / im_ratio)
        else:
            new_width = input_size[0]
            new_height = int(new_width * im_ratio)
        det_scale = float(new_height) / float(image.shape[0])
        resized = cv2.resize(image, (new_width, new_height))
        det_image = np.zeros((input_size[1], input_size[0], 3), dtype=np.uint8)
        det_image[:new_height, :new_width, :] = resized

        tensor = cv2.cvtColor(det_image, cv2.COLOR_BGR2RGB)[None, ...]
        return tensor, det_scale

    def _anchor_centers(self, height: int, width: int, stride: int):
        key = (height, width, stride)
        if key in self.center_cache:
            return self.center_cache[key]
        anchor_centers = np.stack(np.mgrid[:height, :width][::-1], axis=-1).astype(np.float32)
        anchor_centers = (anchor_centers * stride).reshape((-1, 2))
        if self.num_anchors > 1:
            anchor_centers = np.stack([anchor_centers] * self.num_anchors, axis=1).reshape((-1, 2))
        if len(self.center_cache) < 100:
            self.center_cache[key] = anchor_centers
        return anchor_centers

    def forward(self, image: np.ndarray, threshold: float):
        tensor, _ = self._prepare(image)
        outputs = self.model.infer(tensor)

        scores_list = []
        bboxes_list = []
        kpss_list = []
        input_height = self.input_height
        input_width = self.input_width

        for index, stride in enumerate(self.feat_stride_fpn):
            scores = outputs[index].reshape(-1)
            bbox_preds = outputs[index + self.fmc].reshape(-1, 4) * stride
            kps_preds = outputs[index + self.fmc * 2].reshape(-1, 10) * stride

            height = input_height // stride
            width = input_width // stride
            anchor_centers = self._anchor_centers(height, width, stride)

            pos_inds = np.where(scores >= threshold)[0]
            if pos_inds.size == 0:
                continue

            bboxes = distance2bbox(anchor_centers, bbox_preds)
            pos_scores = scores[pos_inds][:, None]
            pos_bboxes = bboxes[pos_inds]
            scores_list.append(pos_scores)
            bboxes_list.append(pos_bboxes)

            kpss = distance2kps(anchor_centers, kps_preds).reshape((-1, 5, 2))
            pos_kpss = kpss[pos_inds]
            kpss_list.append(pos_kpss)

        return scores_list, bboxes_list, kpss_list

    def detect(self, image: np.ndarray, max_num: int = 0, metric: str = "default"):
        tensor, det_scale = self._prepare(image)
        outputs = self.model.infer(tensor)
        scores_list = []
        bboxes_list = []
        kpss_list = []
        input_height = self.input_height
        input_width = self.input_width

        for index, stride in enumerate(self.feat_stride_fpn):
            scores = outputs[index].reshape(-1)
            bbox_preds = outputs[index + self.fmc].reshape(-1, 4) * stride
            kps_preds = outputs[index + self.fmc * 2].reshape(-1, 10) * stride

            height = input_height // stride
            width = input_width // stride
            anchor_centers = self._anchor_centers(height, width, stride)
            pos_inds = np.where(scores >= self.det_thresh)[0]
            if pos_inds.size == 0:
                continue

            bboxes = distance2bbox(anchor_centers, bbox_preds)
            scores_list.append(scores[pos_inds][:, None])
            bboxes_list.append(bboxes[pos_inds])
            kpss = distance2kps(anchor_centers, kps_preds).reshape((-1, 5, 2))
            kpss_list.append(kpss[pos_inds])

        if not scores_list:
            return np.zeros((0, 5), dtype=np.float32), np.zeros((0, 5, 2), dtype=np.float32)

        scores = np.vstack(scores_list)
        scores_ravel = scores.ravel()
        order = scores_ravel.argsort()[::-1]
        bboxes = np.vstack(bboxes_list) / det_scale
        kpss = np.vstack(kpss_list) / det_scale

        pre_det = np.hstack((bboxes, scores)).astype(np.float32, copy=False)
        pre_det = pre_det[order, :]
        keep = self.nms(pre_det)
        det = pre_det[keep, :]
        kpss = kpss[order, :, :]
        kpss = kpss[keep, :, :]

        if max_num > 0 and det.shape[0] > max_num:
            area = (det[:, 2] - det[:, 0]) * (det[:, 3] - det[:, 1])
            img_center = image.shape[0] // 2, image.shape[1] // 2
            offsets = np.vstack(
                [
                    (det[:, 0] + det[:, 2]) / 2 - img_center[1],
                    (det[:, 1] + det[:, 3]) / 2 - img_center[0],
                ]
            )
            offset_dist_squared = np.sum(np.power(offsets, 2.0), axis=0)
            values = area if metric == "max" else area - (offset_dist_squared * 2.0)
            selected = np.argsort(values)[::-1][:max_num]
            det = det[selected, :]
            kpss = kpss[selected, :, :]
        return det, kpss

    def nms(self, dets: np.ndarray):
        x1 = dets[:, 0]
        y1 = dets[:, 1]
        x2 = dets[:, 2]
        y2 = dets[:, 3]
        scores = dets[:, 4]

        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = scores.argsort()[::-1]

        keep = []
        while order.size > 0:
            current = order[0]
            keep.append(current)
            xx1 = np.maximum(x1[current], x1[order[1:]])
            yy1 = np.maximum(y1[current], y1[order[1:]])
            xx2 = np.minimum(x2[current], x2[order[1:]])
            yy2 = np.minimum(y2[current], y2[order[1:]])

            width = np.maximum(0.0, xx2 - xx1 + 1)
            height = np.maximum(0.0, yy2 - yy1 + 1)
            inter = width * height
            overlap = inter / (areas[current] + areas[order[1:]] - inter)
            inds = np.where(overlap <= self.nms_thresh)[0]
            order = order[inds + 1]
        return keep

    def close(self):
        self.model.release()


class RknnArcFaceRecognizer:
    def __init__(self, model_path: str | Path, metadata: dict | None = None):
        self.model = RknnLiteModel(model_path)
        self.metadata = metadata or {}
        input_shape = self.metadata.get("input_shape") or [1, 3, 112, 112]
        self.input_height = int(input_shape[2])
        self.input_width = int(input_shape[3])
        self.input_size = (self.input_width, self.input_height)

    def get_feat(self, image: np.ndarray):
        tensor = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)[None, ...]
        return self.model.infer(tensor)[0]

    def close(self):
        self.model.release()


class RknnFaceGalleryRecognizer:
    def __init__(
        self,
        gallery_dir: str,
        model_pack: str = "buffalo_sc",
        threshold: float = 0.7,
        det_size: int = 640,
        model_zoo_root: str | Path | None = None,
    ):
        self.gallery_dir = Path(gallery_dir)
        self.model_pack = model_pack
        self.threshold = threshold
        self.det_size = det_size
        self.gallery_dir.mkdir(parents=True, exist_ok=True)
        self.gallery_store = GalleryStore(self.gallery_dir)

        pack_info = resolve_rknn_model_pack(model_pack=model_pack, model_zoo_root=model_zoo_root)
        self.pack_info = pack_info
        self.detector = RknnScrfdDetector(pack_info["detector_path"], metadata=pack_info["detector_meta"])
        self.recognizer = RknnArcFaceRecognizer(
            pack_info["recognizer_path"],
            metadata=pack_info["recognizer_meta"],
        )
        self.gallery = {}
        self.reload_gallery()

    def _extract_embedding(self, image: np.ndarray):
        dets, kpss = self.detector.detect(image, max_num=1)
        if dets.shape[0] == 0:
            return None
        aligned = norm_crop(image, kpss[0], image_size=self.recognizer.input_size[0])
        return self.recognizer.get_feat(aligned).flatten()

    def reload_gallery(self):
        loaded = {}
        for target in self.gallery_store.iter_embedding_targets():
            embeddings = []
            for image_path in target["image_paths"]:
                image = imread_local(image_path)
                if image is None:
                    continue
                embedding = self._extract_embedding(image)
                if embedding is None:
                    print(f"경고: {image_path}에서 얼굴을 찾지 못했습니다.")
                    continue
                embeddings.append(embedding)
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

    def detect_faces(self, frame: np.ndarray, max_num: int = 0, metric: str = "default"):
        dets, kpss = self.detector.detect(frame, max_num=max_num, metric=metric)
        items = []
        for index, det in enumerate(dets):
            items.append(
                {
                    "bbox": [int(value) for value in det[:4]],
                    "det_score": float(det[4]),
                    "kps": np.asarray(kpss[index], dtype=np.float32).tolist(),
                }
            )
        return items

    def extract_face_embeddings(self, frame: np.ndarray, max_num: int = 0, metric: str = "default"):
        dets, kpss = self.detector.detect(frame, max_num=max_num, metric=metric)
        items = []
        for index, det in enumerate(dets):
            aligned = norm_crop(frame, kpss[index], image_size=self.recognizer.input_size[0])
            embedding = self.recognizer.get_feat(aligned).flatten()
            items.append(
                {
                    "bbox": [int(value) for value in det[:4]],
                    "det_score": float(det[4]),
                    "kps": np.asarray(kpss[index], dtype=np.float32).tolist(),
                    "embedding": embedding,
                }
            )
        return items

    def extract_embedding(self, frame: np.ndarray, face_index: int = 0):
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

    def recognize(self, frame: np.ndarray):
        dets, kpss = self.detector.detect(frame, max_num=0)
        results = []
        for index, det in enumerate(dets):
            bbox = [int(value) for value in det[:4]]
            det_score = float(det[4])
            if not self.gallery:
                results.append(
                    {
                        "kr_name": "미등록",
                        "en_name": "Unknown",
                        "similarity": 0.0,
                        "bbox": bbox,
                        "det_score": det_score,
                    }
                )
                continue

            aligned = norm_crop(frame, kpss[index], image_size=self.recognizer.input_size[0])
            embedding = self.recognizer.get_feat(aligned).flatten()

            matches = self.match_embedding(embedding, top_k=1)
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
                    "det_score": det_score,
                }
            )
        return results

    def close(self):
        self.detector.close()
        self.recognizer.close()
