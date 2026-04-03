# runtime

## 역할

- 이 모듈은 `OrangePI RK3588`에서 돌아가는 얼굴 인식 런타임을 맡는다.
- 핵심 산출물은 `import해서 쓰는 RKNN face SDK`와 `front / back 분리형 web console`이다.
- 현재 canonical runtime 경로는 `buffalo_m` 기본 pack과 `RKNN Lite2` 기준으로 맞춘다.

## OrangePI 실행 안내

### 1. 환경이 아직 설치되지 않았을 때

아래 세 명령은 처음 1회 환경을 만들거나, 패키지 구성이 바뀌었을 때 다시 실행한다.

```bash
bash runtime/setup_orangepi_rknn_lite2_env.sh
bash runtime/setup_orangepi_rknn_web_env.sh
bash runtime/build_web_frontend.sh
```

- `setup_orangepi_rknn_lite2_env.sh`
  - RKNN Lite2와 SDK 기본 실행 환경을 준비한다.
- `setup_orangepi_rknn_web_env.sh`
  - web backend 실행에 필요한 패키지를 맞춘다.
- `build_web_frontend.sh`
  - frontend를 실제 배포용 정적 파일로 다시 빌드한다.

### 2. 매번 수동으로 web demo를 실행할 때

환경이 이미 준비되어 있다면 아래 두 줄만 실행하면 된다. 이 방식은 현재 SSH 터미널 foreground에서 직접 띄우는 형태라서, 세션을 끊으면 함께 종료된다. 설정을 자주 바꾸며 확인할 때 가장 단순하다.

```bash
source ../envs/ifr_rknn_lite2_cp310/bin/activate
python runtime/web_backend/main.py \
  --host 0.0.0.0 \
  --port 5000 \
  --camera-source /dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0 \
  --gallery-dir runtime/gallery \
  --model-pack buffalo_m \
  --backend rknn \
  --inference-fps 0 \
  --model-zoo-root conversion/results/model_zoo \
  --frontend-dist runtime/web_frontend/dist
```

### 3. service로 등록해서 실행할 때

여기서 `service`는 OrangePI의 `systemd`가 web demo를 백그라운드에서 계속 관리하는 실행 방식이다. 즉, 사람이 로그인한 셸에서 직접 띄우는 것이 아니라 장치 운영용 프로세스로 등록해 두는 의미다.

- SSH 연결이 끊겨도 demo가 계속 살아 있다.
- 재부팅 뒤에도 자동 시작되도록 같은 unit를 유지한다.
- 상태 확인, 재시작, 중지는 `systemctl`로 통일한다.
- 실행 로그는 `journalctl`로 확인한다.
- `runtime/install_orangepi_rknn_web_service.sh`는 unit 파일을 설치 또는 갱신하고 `enable + restart`까지 한 번에 수행한다.

설치 또는 갱신:

```bash
bash runtime/install_orangepi_rknn_web_service.sh
```

운영 중 확인 명령:

```bash
sudo systemctl status insightface_gallery_web.service
sudo systemctl restart insightface_gallery_web.service
sudo systemctl stop insightface_gallery_web.service
sudo journalctl -u insightface_gallery_web.service -n 100 -f
```

### 4. SDK를 바로 확인할 때

```python
import cv2
from runtime import FaceSDK

frame = cv2.imread("runtime/results/face_benchmark_input.jpg")

sdk = FaceSDK(
    gallery_dir="runtime/gallery",
    model_pack="buffalo_m",
    backend="rknn",
    model_zoo_root="conversion/results/model_zoo",
)

print(sdk.describe())
print(sdk.list_gallery_people())
print(sdk.infer(frame))
sdk.close()
```

실행 예제:

```bash
source ../envs/ifr_rknn_lite2_cp310/bin/activate
python runtime/examples/sdk_quickstart.py \
  --image-path runtime/results/face_benchmark_input.jpg \
  --gallery-dir runtime/gallery \
  --model-pack buffalo_m \
  --backend rknn \
  --model-zoo-root conversion/results/model_zoo
```

### 5. 커스텀 기능을 직접 호출할 때

외부 사용자가 detection, embedding, cosine similarity, gallery matching을 직접 제어할 수 있도록 public helper를 연다.

```python
import cv2
from runtime import FaceSDK

sdk = FaceSDK(
    gallery_dir="runtime/gallery",
    model_pack="buffalo_m",
    backend="rknn",
    model_zoo_root="conversion/results/model_zoo",
)

frame_a = cv2.imread("frame_a.jpg")
frame_b = cv2.imread("frame_b.jpg")

detections = sdk.detect_faces(frame_a)
embeddings = sdk.extract_face_embeddings(frame_a)
embedding_a = sdk.extract_embedding(frame_a)
embedding_b = sdk.extract_embedding(frame_b)
gallery_matches = sdk.match_embedding(embedding_a, top_k=3)
pair_similarity = FaceSDK.compare_embeddings(embedding_a, embedding_b)

print(detections)
print(embeddings[0]["bbox"] if embeddings else None)
print(gallery_matches)
print(pair_similarity)
sdk.close()
```

실행 예제:

```bash
source ../envs/ifr_rknn_lite2_cp310/bin/activate
python runtime/examples/sdk_custom_usage.py \
  --image-path-a runtime/results/face_benchmark_input.jpg \
  --gallery-dir runtime/gallery \
  --model-pack buffalo_m \
  --backend rknn \
  --top-k 3 \
  --model-zoo-root conversion/results/model_zoo
```

## model pack 메모

- `buffalo_s`는 face-only alias pack이다.
- `conversion/results/model_zoo/rk3588/buffalo_s/` 안에는 `pack.json`만 있고, 실제 `.rknn` 파일은 `buffalo_sc/` 아래 canonical 산출물을 재사용한다.
- `runtime/rknn_model_zoo.py`가 manifest의 `alias_of: buffalo_sc`를 읽어 `buffalo_s -> buffalo_sc`로 해석하므로, `buffalo_s/`에 별도 `.rknn` 파일이 없어도 정상이다.

## 현재 사용 형태

- 앱 코드에서는 `runtime.FaceSDK` 또는 `runtime.face_wrapper.FaceWrapper`를 import해서 쓴다.
- 운영 화면은 `runtime/web_backend/main.py`와 `runtime/web_frontend/dist/`를 함께 띄워 쓴다.
- service 설치는 `runtime/install_orangepi_rknn_web_service.sh`가 맡는다.

## Public SDK Surface

- `FaceSDK.infer(frame)`
- `FaceSDK.detect_faces(frame)`
- `FaceSDK.extract_face_embeddings(frame)`
- `FaceSDK.extract_embedding(frame, face_index=0)`
- `FaceSDK.match_embedding(embedding, top_k=...)`
- `FaceSDK.list_gallery_people()`
- `FaceSDK.compare_embeddings(embedding_a, embedding_b)`
- `FaceSDK.list_model_packs()`

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

## benchmark 결과 파일

- CPU baseline: [results/260401_1530_ort_cpu_benchmark/summary.json](results/260401_1530_ort_cpu_benchmark/summary.json)
- RKNN all-pack benchmark: [results/260403_0942_rknn_all_pack_benchmark/summary.json](results/260403_0942_rknn_all_pack_benchmark/summary.json)

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
- `runtime/examples/sdk_quickstart.py`
  - gallery 자동 로드 + `infer(frame)` 예제
- `runtime/examples/sdk_custom_usage.py`
  - detection, embedding, cosine similarity, gallery top-k 예제
- `runtime/web_backend/main.py`
  - `FastAPI` backend entry
- `runtime/web_backend/app.py`
  - API route와 정적 frontend 연결
- `runtime/web_backend/runtime_manager.py`
  - 카메라, SDK, FPS, 모델 전환, gallery 작업을 묶는 런타임 관리자
- `runtime/benchmark_rknn_face_sdk.py`
  - OrangePI에서 `FP16 / INT8 / all-pack` 비교 benchmark
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
