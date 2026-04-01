# runtime

## 역할

- 이 모듈은 `OrangePI RK3588`에서 돌아가는 얼굴 인식 런타임을 맡는다.
- 핵심 산출물은 `import해서 쓰는 RKNN face SDK`와 `front / back 분리형 web console`이다.
- 현재 canonical runtime 경로는 `buffalo_m` 기본 pack과 `RKNN Lite2` 기준으로 맞춘다.

## 현재 사용 형태

- 앱 코드에서는 `runtime.FaceSDK` 또는 `runtime.face_wrapper.FaceWrapper`를 import해서 쓴다.
- 운영 화면은 `runtime/web_backend/main.py`와 `runtime/web_frontend/dist/`를 함께 띄워 쓴다.
- service 설치는 `runtime/install_orangepi_rknn_web_service.sh`가 맡는다.

```python
from runtime import FaceSDK

sdk = FaceSDK(
    gallery_dir="runtime/gallery",
    model_pack="buffalo_m",
    backend="rknn",
)
results = sdk.infer(frame)
```

## 이 모듈이 맡는 것

- `RKNN face SDK` 표면
- gallery 자동 로드와 임베딩 비교
- 카메라 또는 JSON 입력 연결
- `FastAPI` backend
- `React` frontend
- 모델 전환과 메모리 정리
- `live-state` 상태 스트림과 최신 결과 overlay
- 갤러리 등록, 촬영 저장, 업로드, 삭제
- 실시간 FPS와 메모리 상태 표시
- OrangePI `systemd` service

## 이 모듈이 맡지 않는 것

- 원본 모델 선택과 `RKNN` 변환
- calibration 입력 묶음 관리
- canonical model zoo 생성

## gallery 저장 규칙

- 기본 구조는 `runtime/gallery/<person_id>/meta.json`, `runtime/gallery/<person_id>/images/*`다.
- `meta.json`에는 `person_id`, `name_ko`, `name_en`, `created_at`, `updated_at`를 둔다.
- 웹 UI는 현재 프레임 저장과 다중 업로드를 모두 이 구조로 저장한다.
- 이전 `한글이름, EnglishName/` 폴더 구조는 읽기 호환만 유지한다.

## OrangePI 실행 순서

1. `bash runtime/setup_orangepi_rknn_lite2_env.sh`
2. `bash runtime/setup_orangepi_rknn_web_env.sh`
3. `bash runtime/build_web_frontend.sh`
4. 필요하면 `source ../envs/ifr_rknn_lite2_cp310/bin/activate`
5. 수동 smoke:
   `python runtime/web_backend/main.py --host 0.0.0.0 --port 5050 --camera-source /dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0 --gallery-dir runtime/gallery --model-pack buffalo_m --backend rknn --inference-fps 0 --model-zoo-root conversion/results/model_zoo --frontend-dist runtime/web_frontend/dist`
6. service 설치:
   `bash runtime/install_orangepi_rknn_web_service.sh`

## 현재 고정 결정

- 기본 SDK backend는 `rknn`, 기본 pack은 `buffalo_m`이다.
- `buffalo_sc`, `buffalo_s(alias)`, `buffalo_m`, `buffalo_m_i8`, `buffalo_l` 다섯 pack 이름을 web UI에서 전환 가능하게 유지한다.
- 모델 전환은 기본적으로 warm switch로 처리하고, 메모리 계열 실패가 나면 old SDK를 비운 뒤 cold retry와 복구를 시도한다.
- 실시간 결과는 `/api/live-state/stream`으로 밀어 주고, frontend는 이 상태 스트림으로 overlay를 갱신한다.
- backend 기본 추론 상한은 `0`, 즉 제한 없이 최신 프레임 우선 처리다.
- 상태 표시 글자는 `cv2` overlay가 아니라 web UI 레이어에서 그린다.
- 서비스 포트는 최종적으로 `5000`을 유지한다.
- OrangePI service는 `camera-id`보다 `camera-source`를 우선 사용한다.
- 현재 주 카메라 경로는 `/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0`다.
- CPU 경로는 `benchmark_insightface_cpu.py`와 `../envs/ifr_ort_cpu_probe`로만 유지한다.

## 현재 entry script

- `runtime/face_sdk.py`
  - 앱 코드와 backend가 공용으로 쓰는 SDK-style 표면
- `runtime/face_wrapper.py`
  - import해서 쓰는 얇은 공용 wrapper
- `runtime/web_backend/main.py`
  - `FastAPI` backend entry
- `runtime/web_backend/app.py`
  - API route와 정적 frontend 연결
- `runtime/web_backend/runtime_manager.py`
  - 카메라, SDK, FPS, 모델 전환, gallery 작업을 묶는 런타임 관리자
- `runtime/benchmark_rknn_face_sdk.py`
  - OrangePI에서 `FP16 / INT8` pack 비교 benchmark
- `runtime/web_frontend/`
  - 운영용 web UI source와 build 결과
- `runtime/install_orangepi_rknn_web_service.sh`
  - OrangePI service 설치 entry
- `runtime/setup_orangepi_rknn_web_env.sh`
  - web backend 실행 패키지까지 포함한 Lite2 env 준비
- `runtime/build_web_frontend.sh`
  - frontend build entry
- `runtime/benchmark_insightface_cpu.py`
  - CPU 비교 benchmark
- `runtime/probe_rknn_lite2.py`
  - `.rknn` 단건 smoke

## 관련 문서

- [root README](../README.md)
- [project logbook](../docs/logbook.md)
- [module logbook](docs/logbook.md)
