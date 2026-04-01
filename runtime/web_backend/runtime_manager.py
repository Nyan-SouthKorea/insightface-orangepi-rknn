from __future__ import annotations

import copy
import gc
import os
import threading
import time
from pathlib import Path

import cv2
import numpy as np

try:
    from ..face_sdk import FaceSDK
    from ..gallery_store import GalleryStore
    from ..image_capture import JsonImageReader, open_webcam
except ImportError:
    from face_sdk import FaceSDK
    from gallery_store import GalleryStore
    from image_capture import JsonImageReader, open_webcam


class LiveRuntimeManager:
    def __init__(self, args):
        self.args = args
        self.gallery_dir = Path(args.gallery_dir)
        self.gallery_store = GalleryStore(self.gallery_dir)
        self.camera_source = args.camera_source or str(args.camera_id)
        self.stop_event = threading.Event()
        self.state_lock = threading.Lock()
        self.sdk_lock = threading.Lock()
        self.switch_lock = threading.Lock()

        self.capture = None
        self.json_reader = None
        self.sdk = None

        self.latest_raw_frame = None
        self.last_results = []
        self.last_frame_time = ""
        self.last_result_time = ""
        self.last_error = ""
        self.capture_fps = 0.0
        self.inference_fps = 0.0
        self.stream_fps = 0.0
        self.frame_width = 0
        self.frame_height = 0
        self.last_result_count = 0
        self.capture_revision = 0
        self.result_revision = 0
        self.last_inference_duration_ms = 0.0
        self.avg_inference_duration_ms = 0.0
        self.max_inference_fps = max(0, int(args.inference_fps))

        self.current_model_pack = args.model_pack
        self.switch_in_progress = False
        self.last_switch_error = ""
        self.last_switch_summary = {}

        self.capture_worker = None
        self.inference_worker = None

        if args.capture_mode == "json":
            self.json_reader = JsonImageReader(
                json_path=args.json_path,
                cam_key=args.cam_key,
                image_dir=args.image_dir,
            )

    def start(self):
        self._load_initial_sdk()
        self.capture_worker = threading.Thread(target=self._capture_loop, daemon=True)
        self.inference_worker = threading.Thread(target=self._inference_loop, daemon=True)
        self.capture_worker.start()
        self.inference_worker.start()

    def stop(self):
        self.stop_event.set()
        if self.capture_worker is not None:
            self.capture_worker.join(timeout=2.0)
        if self.inference_worker is not None:
            self.inference_worker.join(timeout=2.0)
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        with self.sdk_lock:
            if self.sdk is not None:
                self.sdk.close()
                self.sdk = None
        gc.collect()

    def _load_initial_sdk(self):
        self.sdk = self._build_sdk(self.current_model_pack)

    def _build_sdk(self, model_pack: str):
        return FaceSDK(
            gallery_dir=str(self.gallery_dir),
            model_pack=model_pack,
            backend=self.args.backend,
            provider=self.args.provider,
            threshold=self.args.threshold,
            det_size=self.args.det_size,
            model_zoo_root=self.args.model_zoo_root,
        )

    def _capture_loop(self):
        last_capture_ts = None
        while not self.stop_event.is_set():
            try:
                ok, frame = self._read_frame()
                if not ok or frame is None:
                    time.sleep(0.05)
                    continue

                if self.args.capture_mode == "webcam":
                    frame = cv2.flip(frame, 1)

                now = time.perf_counter()
                if last_capture_ts is not None:
                    interval = max(1e-6, now - last_capture_ts)
                    self.capture_fps = (self.capture_fps * 0.9) + ((1.0 / interval) * 0.1)
                last_capture_ts = now

                with self.state_lock:
                    self.latest_raw_frame = frame.copy()
                    self.frame_height, self.frame_width = frame.shape[:2]
                    self.last_frame_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    self.capture_revision += 1
            except Exception as exc:
                self.last_error = str(exc)
                time.sleep(0.2)

    def _read_frame(self):
        if self.args.capture_mode == "json":
            return self.json_reader.read()

        if self.capture is None or not self.capture.isOpened():
            self.capture = open_webcam(
                camera_source=self.camera_source,
                width=self.args.camera_width,
                height=self.args.camera_height,
                fps=self.args.camera_fps,
            )
            if not self.capture.isOpened():
                self.last_error = f"카메라 {self.camera_source}를 열지 못했습니다."
                return False, None

        ok, frame = self.capture.read()
        if not ok:
            self.last_error = "카메라 프레임을 읽지 못했습니다."
            return False, None
        return True, frame

    def _inference_loop(self):
        last_inference_ts = None
        processed_capture_revision = -1
        while not self.stop_event.is_set():
            with self.state_lock:
                frame = None if self.latest_raw_frame is None else self.latest_raw_frame.copy()
                capture_revision = self.capture_revision

            if frame is None or capture_revision == processed_capture_revision:
                time.sleep(0.005)
                continue

            started = time.perf_counter()
            try:
                with self.sdk_lock:
                    results = [] if self.sdk is None else self.sdk.infer(frame)
                duration_ms = (time.perf_counter() - started) * 1000.0
                with self.state_lock:
                    self.last_results = copy.deepcopy(results)
                    self.last_result_count = len(results)
                    self.last_result_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    self.last_error = ""
                    self.result_revision += 1
                    self.last_inference_duration_ms = round(duration_ms, 2)
                    if self.avg_inference_duration_ms <= 0:
                        self.avg_inference_duration_ms = duration_ms
                    else:
                        self.avg_inference_duration_ms = (self.avg_inference_duration_ms * 0.9) + (duration_ms * 0.1)
            except Exception as exc:
                self.last_error = str(exc)
                with self.state_lock:
                    self.last_results = []
                    self.last_result_count = 0
                    self.result_revision += 1
                duration_ms = (time.perf_counter() - started) * 1000.0
                self.last_inference_duration_ms = round(duration_ms, 2)

            now = time.perf_counter()
            if last_inference_ts is not None:
                interval = max(1e-6, now - last_inference_ts)
                self.inference_fps = (self.inference_fps * 0.9) + ((1.0 / interval) * 0.1)
            last_inference_ts = now
            processed_capture_revision = capture_revision

            if self.max_inference_fps > 0:
                min_interval = 1.0 / float(self.max_inference_fps)
                elapsed = time.perf_counter() - started
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)

    def get_stream_frame(self) -> bytes:
        with self.state_lock:
            frame = None if self.latest_raw_frame is None else self.latest_raw_frame.copy()

        if frame is None:
            frame = self._placeholder_frame("입력 프레임 대기 중입니다.")

        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            encoded = np.zeros((1,), dtype=np.uint8)

        self._tick_stream_fps()
        return encoded.tobytes()

    def _tick_stream_fps(self):
        now = time.perf_counter()
        previous = getattr(self, "_last_stream_ts", None)
        if previous is not None:
            interval = max(1e-6, now - previous)
            self.stream_fps = (self.stream_fps * 0.9) + ((1.0 / interval) * 0.1)
        self._last_stream_ts = now

    def _placeholder_frame(self, message: str) -> np.ndarray:
        canvas = np.zeros((720, 1280, 3), dtype=np.uint8)
        canvas[:] = (14, 18, 24)
        cv2.putText(
            canvas,
            message,
            (48, 96),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (205, 233, 255),
            2,
            cv2.LINE_AA,
        )
        return canvas

    def list_model_packs(self) -> list[dict]:
        items = FaceSDK.list_model_packs(
            backend=self.args.backend,
            target_platform=self.args.target_platform,
            model_zoo_root=self.args.model_zoo_root,
        )
        normalized = []
        for item in items:
            normalized.append(
                {
                    "model_pack": item["model_pack"],
                    "requested_model_pack": item.get("requested_model_pack", item["model_pack"]),
                    "resolved_model_pack": item.get("resolved_model_pack", item["model_pack"]),
                    "alias_of": item.get("alias_of"),
                    "detector_path": str(item.get("detector_path", "")),
                    "recognizer_path": str(item.get("recognizer_path", "")),
                    "error": item.get("error"),
                }
            )
        return normalized

    def _looks_like_memory_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        keywords = [
            "memory",
            "mem",
            "cma",
            "out of memory",
            "cannot allocate",
            "cannot mmap",
            "insufficient",
            "failed to submit",
        ]
        return isinstance(exc, MemoryError) or any(keyword in message for keyword in keywords)

    def switch_model(self, model_pack: str) -> dict:
        with self.switch_lock:
            if model_pack == self.current_model_pack and self.sdk is not None:
                return self.describe_runtime()

            self.switch_in_progress = True
            self.last_switch_error = ""
            before_rss_mb = self.process_memory_mb()
            previous_model_pack = self.current_model_pack
            new_sdk = None
            released_old_for_retry = False
            start = time.perf_counter()

            try:
                switch_mode = "warm"
                try:
                    new_sdk = self._build_sdk(model_pack)
                except Exception as exc:
                    if not self._looks_like_memory_error(exc):
                        raise
                    switch_mode = "cold_retry"
                    with self.sdk_lock:
                        old_sdk = self.sdk
                        self.sdk = None
                    if old_sdk is not None:
                        old_sdk.close()
                    gc.collect()
                    released_old_for_retry = True
                    new_sdk = self._build_sdk(model_pack)

                with self.sdk_lock:
                    old_sdk = self.sdk
                    self.sdk = new_sdk
                    self.current_model_pack = model_pack

                if old_sdk is not None:
                    old_sdk.close()
                gc.collect()

                after_rss_mb = self.process_memory_mb()
                self.last_switch_summary = {
                    "requested_model_pack": model_pack,
                    "resolved_model_pack": self.sdk.describe().get("resolved_model_pack"),
                    "duration_ms": round((time.perf_counter() - start) * 1000.0, 2),
                    "memory_before_mb": before_rss_mb,
                    "memory_after_mb": after_rss_mb,
                    "switch_mode": switch_mode,
                    "released_old_for_retry": released_old_for_retry,
                }
                return self.describe_runtime()
            except Exception as exc:
                if new_sdk is not None:
                    new_sdk.close()
                restore_error = ""
                with self.sdk_lock:
                    sdk_missing = self.sdk is None
                if released_old_for_retry and sdk_missing:
                    try:
                        restored_sdk = self._build_sdk(previous_model_pack)
                        with self.sdk_lock:
                            self.sdk = restored_sdk
                            self.current_model_pack = previous_model_pack
                    except Exception as restore_exc:
                        restore_error = f" / restore failed: {restore_exc}"
                self.last_switch_error = f"{exc}{restore_error}"
                raise RuntimeError(self.last_switch_error) from exc
            finally:
                self.switch_in_progress = False

    def reload_gallery(self):
        with self.sdk_lock:
            if self.sdk is None:
                return []
            return self.sdk.reload_gallery()

    def list_people(self) -> list[dict]:
        return self.gallery_store.list_people()

    def create_person(self, name_ko: str, name_en: str) -> dict:
        person = self.gallery_store.create_person(name_ko=name_ko, name_en=name_en)
        self.reload_gallery()
        return person

    def update_person(self, person_id: str, name_ko: str, name_en: str) -> dict:
        person = self.gallery_store.update_person(person_id=person_id, name_ko=name_ko, name_en=name_en)
        self.reload_gallery()
        return person

    def delete_person(self, person_id: str) -> None:
        self.gallery_store.delete_person(person_id)
        self.reload_gallery()

    def save_uploaded_image(self, person_id: str, content: bytes, filename: str) -> dict:
        suffix = Path(filename).suffix or ".jpg"
        image = self.gallery_store.save_image_bytes(
            person_id,
            content,
            extension=suffix,
            filename_prefix="upload",
        )
        self.reload_gallery()
        return image

    def capture_person_image(self, person_id: str) -> dict:
        with self.state_lock:
            frame = None if self.latest_raw_frame is None else self.latest_raw_frame.copy()
        if frame is None:
            raise RuntimeError("현재 저장할 카메라 프레임이 없습니다.")
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        if not ok:
            raise RuntimeError("캡처 프레임 JPEG 인코딩에 실패했습니다.")
        image = self.gallery_store.save_image_bytes(
            person_id,
            encoded.tobytes(),
            extension=".jpg",
            filename_prefix="capture",
        )
        self.reload_gallery()
        return image

    def delete_person_image(self, person_id: str, image_id: str) -> None:
        self.gallery_store.delete_image(person_id, image_id)
        self.reload_gallery()

    def get_person_image_path(self, person_id: str, image_id: str) -> Path:
        return self.gallery_store.get_image_path(person_id, image_id)

    def get_snapshot_bytes(self) -> bytes:
        with self.state_lock:
            frame = None if self.latest_raw_frame is None else self.latest_raw_frame.copy()
        if frame is None:
            frame = self._placeholder_frame("입력 프레임 대기 중입니다.")
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not ok:
            raise RuntimeError("스냅샷 인코딩에 실패했습니다.")
        return encoded.tobytes()

    def process_memory_mb(self) -> float:
        try:
            for line in Path("/proc/self/status").read_text().splitlines():
                if not line.startswith("VmRSS:"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    return round(int(parts[1]) / 1024.0, 2)
        except Exception:
            return 0.0
        return 0.0

    def status_provider_name(self) -> str:
        if self.args.backend == "rknn":
            return "RKNNLite"
        return self.args.provider

    def describe_runtime(self) -> dict:
        with self.sdk_lock:
            sdk_info = {} if self.sdk is None else self.sdk.describe()
        with self.state_lock:
            results = copy.deepcopy(self.last_results)
            frame_width = self.frame_width
            frame_height = self.frame_height

        return {
            "backend": self.args.backend,
            "provider": self.status_provider_name(),
            "capture_mode": self.args.capture_mode,
            "camera_source": self.camera_source,
            "model_pack": self.current_model_pack,
            "resolved_model_pack": sdk_info.get("resolved_model_pack"),
            "alias_of": sdk_info.get("alias_of"),
            "gallery_dir": str(self.gallery_dir),
            "gallery_count": sdk_info.get("gallery_count", 0),
            "capture_fps": round(self.capture_fps, 2),
            "inference_fps": round(self.inference_fps, 2),
            "stream_fps": round(self.stream_fps, 2),
            "last_result_count": self.last_result_count,
            "last_frame_time": self.last_frame_time,
            "last_error": self.last_error,
            "last_switch_error": self.last_switch_error,
            "last_switch_summary": self.last_switch_summary,
            "switch_in_progress": self.switch_in_progress,
            "frame_width": frame_width,
            "frame_height": frame_height,
            "memory_rss_mb": self.process_memory_mb(),
            "capture_revision": self.capture_revision,
            "result_revision": self.result_revision,
            "last_result_time": self.last_result_time,
            "last_inference_duration_ms": round(self.last_inference_duration_ms, 2),
            "avg_inference_duration_ms": round(self.avg_inference_duration_ms, 2),
            "max_inference_fps": self.max_inference_fps,
            "latest_results": results,
            "sdk": sdk_info,
        }

    def describe_live_state(self) -> dict:
        with self.sdk_lock:
            sdk_info = {} if self.sdk is None else self.sdk.describe()
        with self.state_lock:
            results = copy.deepcopy(self.last_results)
            frame_width = self.frame_width
            frame_height = self.frame_height
            last_frame_time = self.last_frame_time
            last_result_time = self.last_result_time
            last_result_count = self.last_result_count
            capture_revision = self.capture_revision
            result_revision = self.result_revision

        return {
            "model_pack": self.current_model_pack,
            "resolved_model_pack": sdk_info.get("resolved_model_pack"),
            "alias_of": sdk_info.get("alias_of"),
            "gallery_count": sdk_info.get("gallery_count", 0),
            "capture_fps": round(self.capture_fps, 2),
            "inference_fps": round(self.inference_fps, 2),
            "stream_fps": round(self.stream_fps, 2),
            "memory_rss_mb": self.process_memory_mb(),
            "frame_width": frame_width,
            "frame_height": frame_height,
            "last_frame_time": last_frame_time,
            "last_result_time": last_result_time,
            "last_result_count": last_result_count,
            "last_error": self.last_error,
            "last_switch_error": self.last_switch_error,
            "last_switch_summary": self.last_switch_summary,
            "switch_in_progress": self.switch_in_progress,
            "capture_revision": capture_revision,
            "result_revision": result_revision,
            "last_inference_duration_ms": round(self.last_inference_duration_ms, 2),
            "avg_inference_duration_ms": round(self.avg_inference_duration_ms, 2),
            "max_inference_fps": self.max_inference_fps,
            "latest_results": results,
        }
