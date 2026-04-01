"""Face-only real-time web demo for gallery-based recognition.

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
  - `runtime/gallery/`: gallery user folders
  - webcam frames or JSON image frames

Main outputs:
  - `http://<device-ip>:5000/`: status page with MJPEG stream
  - `http://<device-ip>:5000/stream.mjpg`: direct MJPEG stream
"""

from __future__ import annotations

import argparse
import signal
import threading
import time

import cv2
import numpy as np
import onnxruntime as ort
from flask import Flask, Response, jsonify

from face_gallery_recognizer import FaceGalleryRecognizer
from image_capture import JsonImageReader, open_webcam


HTML_INDEX = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>InsightFace Gallery Demo</title>
  <style>
    body { font-family: sans-serif; margin: 0; background: #111; color: #eee; }
    header { padding: 16px 20px; background: #181818; border-bottom: 1px solid #333; }
    main { padding: 20px; display: grid; gap: 16px; }
    .panel { background: #1b1b1b; border: 1px solid #333; border-radius: 12px; overflow: hidden; }
    .stream { width: 100%; display: block; background: #000; }
    .meta { padding: 14px 16px; line-height: 1.7; }
    code { color: #8fd3ff; }
  </style>
</head>
<body>
  <header>
    <strong>InsightFace Gallery Demo</strong>
  </header>
  <main>
    <section class="panel">
      <img class="stream" src="/stream.mjpg" alt="stream">
      <div class="meta">
        <div id="status">상태 확인 중...</div>
      </div>
    </section>
  </main>
  <script>
    async function refreshStatus() {
      const response = await fetch('/api/status');
      const data = await response.json();
      const error = data.last_error ? `<br>마지막 오류: <code>${data.last_error}</code>` : '';
      document.getElementById('status').innerHTML =
        `입력: <code>${data.capture_mode}</code><br>` +
        `gallery 인원 수: <code>${data.gallery_count}</code><br>` +
        `provider: <code>${data.provider}</code><br>` +
        `사용 가능한 ORT provider: <code>${data.available_providers.join(', ')}</code><br>` +
        `최근 결과 수: <code>${data.last_result_count}</code><br>` +
        `최근 프레임 시각: <code>${data.last_frame_time}</code>` + error;
    }
    refreshStatus();
    setInterval(refreshStatus, 2000);
  </script>
</body>
</html>
"""


class FaceGalleryWebDemo:
    def __init__(self, args):
        self.args = args
        self.stop_event = threading.Event()
        self.frame_lock = threading.Lock()

        self.last_encoded_frame = self._encode_placeholder(
            "서비스 준비 중입니다. 잠시만 기다려 주세요."
        )
        self.last_result_count = 0
        self.last_frame_time = ""
        self.last_error = ""

        self.recognizer = FaceGalleryRecognizer(
            gallery_dir=args.gallery_dir,
            model_pack=args.model_pack,
            provider=args.provider,
            threshold=args.threshold,
            det_size=args.det_size,
        )

        self.capture = None
        self.json_reader = None
        if args.capture_mode == "json":
            self.json_reader = JsonImageReader(
                json_path=args.json_path,
                cam_key=args.cam_key,
                image_dir=args.image_dir,
            )

        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker.start()

    def _worker_loop(self):
        while not self.stop_event.is_set():
            if self.args.capture_mode == "json":
                ok, frame = self.json_reader.read()
                if not ok:
                    time.sleep(0.03)
                    continue
            else:
                if self.capture is None or not self.capture.isOpened():
                    self.capture = open_webcam(
                        camera_id=self.args.camera_id,
                        width=self.args.camera_width,
                        height=self.args.camera_height,
                        fps=self.args.camera_fps,
                    )
                    if not self.capture.isOpened():
                        self.last_error = (
                            f"카메라 {self.args.camera_id}를 열지 못했습니다. "
                            "카메라 연결 상태를 확인하세요."
                        )
                        self._set_placeholder(self.last_error)
                        time.sleep(2.0)
                        continue

                ok, frame = self.capture.read()
                if not ok:
                    self.last_error = "카메라 프레임을 읽지 못했습니다."
                    self._set_placeholder(self.last_error)
                    time.sleep(0.2)
                    continue

                frame = cv2.flip(frame, 1)

            try:
                results = self.recognizer.recognize(frame)
                annotated = self._draw_results(frame, results)
                encoded = self._encode_frame(annotated)
                self.last_result_count = len(results)
                self.last_frame_time = time.strftime("%Y-%m-%d %H:%M:%S")
                self.last_error = ""
            except Exception as exc:
                self.last_error = str(exc)
                encoded = self._encode_placeholder(f"인식 중 오류: {exc}")

            with self.frame_lock:
                self.last_encoded_frame = encoded

            time.sleep(max(0.0, 1.0 / max(1, self.args.max_fps)))

    def _draw_results(self, frame, results):
        drawn = frame.copy()
        for result in results:
            x1, y1, x2, y2 = result["bbox"]
            label = f'{result["en_name"]} {result["similarity"]:.2f}'
            color = (0, 255, 0) if result["en_name"] != "Unknown" else (0, 0, 255)
            cv2.rectangle(drawn, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                drawn,
                label,
                (x1, max(25, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
                cv2.LINE_AA,
            )

        summary = (
            f"gallery={len(self.recognizer.gallery)}  "
            f"provider={self.args.provider}  "
            f"model={self.args.model_pack}"
        )
        cv2.putText(
            drawn,
            summary,
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        return drawn

    def _encode_frame(self, frame):
        ok, encoded = cv2.imencode(".jpg", frame)
        if not ok:
            raise RuntimeError("JPEG 인코딩에 실패했습니다.")
        return encoded.tobytes()

    def _encode_placeholder(self, message):
        canvas = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.putText(
            canvas,
            message[:96],
            (40, 360),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        return self._encode_frame(canvas)

    def _set_placeholder(self, message):
        with self.frame_lock:
            self.last_encoded_frame = self._encode_placeholder(message)

    def frame_generator(self):
        while not self.stop_event.is_set():
            with self.frame_lock:
                payload = self.last_encoded_frame
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + payload + b"\r\n"
            )
            time.sleep(0.03)

    def status_payload(self):
        return {
            "capture_mode": self.args.capture_mode,
            "gallery_count": len(self.recognizer.gallery),
            "provider": self.args.provider,
            "available_providers": ort.get_available_providers(),
            "last_result_count": self.last_result_count,
            "last_frame_time": self.last_frame_time,
            "last_error": self.last_error,
        }

    def shutdown(self):
        self.stop_event.set()
        if self.capture is not None and self.capture.isOpened():
            self.capture.release()


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--capture-mode", choices=["webcam", "json"], default="webcam")
    parser.add_argument("--camera-id", type=int, default=0)
    parser.add_argument("--camera-width", type=int, default=1280)
    parser.add_argument("--camera-height", type=int, default=720)
    parser.add_argument("--camera-fps", type=int, default=30)
    parser.add_argument("--json-path", default="cam_info.json")
    parser.add_argument("--cam-key", default="camera1")
    parser.add_argument("--image-dir", default="cam_images")
    parser.add_argument("--gallery-dir", default="runtime/gallery")
    parser.add_argument("--model-pack", default="buffalo_s")
    parser.add_argument("--provider", default="CPUExecutionProvider")
    parser.add_argument("--threshold", type=float, default=0.7)
    parser.add_argument("--det-size", type=int, default=640)
    parser.add_argument("--max-fps", type=int, default=15)
    return parser


def main():
    args = build_parser().parse_args()
    demo = FaceGalleryWebDemo(args)

    app = Flask(__name__)

    @app.route("/")
    def index():
        return HTML_INDEX

    @app.route("/stream.mjpg")
    def stream():
        return Response(
            demo.frame_generator(),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )

    @app.route("/api/status")
    def api_status():
        return jsonify(demo.status_payload())

    def handle_signal(signum, frame):
        del signum, frame
        demo.shutdown()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()
