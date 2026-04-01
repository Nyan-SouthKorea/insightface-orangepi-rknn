# runtime logbook

## 읽기 규칙

- 먼저 `../../docs/AGENT.md`를 읽는다.
- 그다음 `../README.md`를 읽고 이 모듈의 역할과 경계를 맞춘다.
- 그다음 `../../docs/logbook.md`를 읽고 프로젝트 전역 결정과 활성 체크리스트를 맞춘다.
- 아직 archive 문서는 없다. archive가 생기면 최신 `logbook_*.md` 1개를 함께 읽는다.

## 현재 모듈 스냅샷

- `face-only` 웹 데모와 CPU 검증용 `ONNX Runtime` 환경은 1차 smoke를 통과했다.
- OrangePI에서 `insightface_gallery_web.service` 기동과 LAN 접속은 확인했다.
- 웹 데모는 현재 `capture`, `inference`, `render` 루프를 분리한 구조로 갱신했다.
- overlay에는 `capture_fps`, `infer_fps`, `stream_fps`를 함께 표시한다.
- 앱 코드가 import하는 표면은 `runtime.face_wrapper.FaceWrapper`로 유지한다.
- 현재 목적은 첫 번째 RKNN 경로를 붙인 뒤, 같은 표면을 `RKNN face SDK`로 승격하고, 새 `front / back` 분리형 web demo를 만드는 것이다.
- 현재 venv 이름은 `../envs/ifr_ort_cpu_probe`로 고정했다.
- RKNN Lite2 실기기 venv 이름은 `../envs/ifr_rknn_lite2_cp310`로 고정했다.
- 현재 OrangePI USB 카메라의 stable path는 `/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0`이고, 장치 번호는 현재 `/dev/video21`이다.
- 현재 live status 기준 `capture_fps 8.33`, `inference_fps 1.05`, `stream_fps 8.95`, `gallery_count 0`, `last_error=""`를 확인했다.
- `runtime/probe_rknn_lite2.py`를 추가했고, 다음 단계는 host에서 만든 `buffalo_sc` RKNN 산출물을 OrangePI에서 smoke하는 것이다.
- OrangePI에서 `buffalo_sc det_500m_fp16.rknn`, `buffalo_sc w600k_mbf_fp16.rknn` 파일 입력 smoke는 실제로 성공했다.
- OrangePI에서 `FaceWrapper(backend="rknn", model_pack="buffalo_sc")` 기준 gallery 1명 file-input end-to-end도 성공했다.
- OrangePI에서 `FaceWrapper(backend="rknn")` 기준 `buffalo_s(alias)`, `buffalo_m`, `buffalo_l`도 gallery 1명 file-input end-to-end를 통과했다.

## 현재 모듈 결정

- 이 모듈은 실기기 실행과 성능 측정을 맡는다.
- 원본 모델과 변환 로직은 `conversion/`이 맡는다.
- 큰 산출물은 `runtime/results/` 아래에 둔다.
- 현재 `face-only` 웹 데모는 CPU 검증 경로로 먼저 세운다.
- `ONNX Runtime`은 검증용 CPU 경로로 두고, RK3588 NPU 실시간 주경로는 이후 `RKNN`으로 옮긴다.
- OrangePI 단건 RKNN smoke는 우선 `probe_rknn_lite2.py`와 파일 입력으로 닫는다.
- 현재 OrangePI Lite2 smoke env는 `RKNNLite + opencv-python-headless 4.10.0.84` 조합으로 유지한다.
- 현재 OrangePI runtime은 `librknnrt 2.1.0`, driver `0.9.6`으로 보이며 toolkit `2.3.2` exported model과 warning은 남지만 smoke 추론은 통과한다.
- 현재 `RKNN Lite2` 입력은 `raw RGB uint8 NHWC`로 넣고, 변환 시 넣은 `mean/std`를 runtime에서 다시 적용하지 않는다.
- `runtime/rknn_model_zoo.py`는 현재 `pack.json` manifest와 alias를 읽어 `buffalo_s -> buffalo_sc` 같은 pack 선택을 해석한다.
- `runtime.FaceSDK`는 현재 앱 코드와 future backend API가 공용으로 쓰는 SDK-style import 이름이다.
- gallery 로컬 자산은 `runtime/gallery/` 아래에 두고 git으로 추적하지 않는다.
- service 설치 스크립트는 `camera-source`를 자동 선택해 unit 파일에 박아 넣는다.
- wrapper가 주 제품이고 web demo는 사람 확인용 entry다.
- 최종 web demo는 `backend API`와 `frontend UI`를 분리한다.

## 현재 CPU benchmark 상세

- 실행 위치: `OrangePI RK3588`
- 실행 명령:
  - `../envs/ifr_ort_cpu_probe/bin/python runtime/benchmark_insightface_cpu.py --image-path runtime/results/face_benchmark_input.jpg --model-packs buffalo_sc,buffalo_s,buffalo_m,buffalo_l --repeat 20 --warmup 5 --provider CPUExecutionProvider --output-json runtime/results/260401_1530_ort_cpu_benchmark/summary.json`
- 입력 이미지: `runtime/results/face_benchmark_input.jpg`
- 결과 JSON: `runtime/results/260401_1530_ort_cpu_benchmark/summary.json`

| model pack | zip size MB | detection model | recognition model | detection avg ms | recognition avg ms | pipeline avg ms | pipeline FPS |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| buffalo_sc | 14.3 | det_500m.onnx | w600k_mbf.onnx | 49.21 | 23.09 | 139.57 | 7.16 |
| buffalo_s | 121.7 | det_500m.onnx | w600k_mbf.onnx | 50.60 | 27.01 | 160.37 | 6.24 |
| buffalo_m | 263.2 | det_2.5g.onnx | w600k_r50.onnx | 152.80 | 318.90 | 635.75 | 1.57 |
| buffalo_l | 275.3 | det_10g.onnx | w600k_r50.onnx | 573.89 | 429.12 | 1102.10 | 0.91 |

## 현재 RKNN smoke 상세

- OrangePI 환경 준비
  - `bash runtime/setup_orangepi_rknn_lite2_env.sh`
- detection smoke
  - `source ../envs/ifr_rknn_lite2_cp310/bin/activate`
  - `python runtime/probe_rknn_lite2.py --rknn-path conversion/results/model_zoo/rk3588/buffalo_sc/det_500m_fp16.rknn --input-image runtime/results/face_benchmark_input.jpg --model-kind detection --input-size 640,640`
  - 결과 요약: `9`개 출력 tensor, 첫 세 출력 shape `12800x1`, `3200x1`, `800x1`
- recognition smoke
  - `source ../envs/ifr_rknn_lite2_cp310/bin/activate`
  - `python runtime/probe_rknn_lite2.py --rknn-path conversion/results/model_zoo/rk3588/buffalo_sc/w600k_mbf_fp16.rknn --input-image runtime/results/face_benchmark_input.jpg --model-kind recognition --input-size 112,112`
  - 결과 요약: `1 x 512` 출력 tensor, 값 범위 `-0.6206 ~ 0.5732`
- 현재 warning 메모
  - static shape 모델이라 `query dynamic range` warning이 보이지만 현재 smoke 기준에서는 무시 가능했다.
  - exported model toolkit `2.3.2`와 OrangePI runtime `2.1.0` 사이 version warning이 남아 있다.

## 현재 RKNN wrapper smoke 상세

- 실행 위치: `OrangePI RK3588`
- 실행 환경: `../envs/ifr_rknn_lite2_cp310`
- 입력 이미지: `runtime/results/face_benchmark_input.jpg`
- gallery 입력: `/tmp/rknn_gallery_smoke_stage2/테스트, TestUser/face.jpg`

| model pack | resolved pack | load ms | infer ms | top result | similarity | det score |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| buffalo_s | buffalo_sc | 659.93 | 54.20 | TestUser | 1.00 | 0.6807 |
| buffalo_m | buffalo_m | 575.48 | 156.22 | TestUser | 1.00 | 0.6494 |
| buffalo_l | buffalo_l | 4389.70 | 124.09 | TestUser | 1.00 | 0.6753 |

## 현재 활성 체크리스트

- [x] `face-only` 얼굴 인식 모듈 초안 작성
- [x] 웹 스트리밍 데모 entry script 작성
- [x] gallery 로컬 폴더 규칙 정의
- [x] CPU 검증용 requirements 파일 작성
- [x] OrangePI용 venv 생성 스크립트 작성
- [x] systemd 서비스 파일 작성
- [x] OrangePI에서 venv 생성과 패키지 설치 smoke 수행
- [x] OrangePI에서 서비스 기동과 네트워크 접속 smoke 수행
- [x] buffalo model pack CPU benchmark 기록
- [x] 웹 데모 스트리밍과 추론 루프 분리
- [x] FPS 표시 추가
- [x] 빨간색 상단 글씨 반영
- [x] stable camera source 기반 service 설치 구조 반영
- [x] OrangePI `RKNN Lite2` venv 생성 스크립트 작성
- [x] RKNN runtime smoke entry script 초안 작성
- [x] `buffalo_sc` RKNN backend 연결
- [x] RKNN SDK 공용 표면 초안 작성
- [ ] 새 web demo back 구조 설계
- [ ] 새 web demo front 구조 설계
- [ ] 모델 전환 UI 구현
- [ ] gallery 등록 / 삭제 / 촬영 API 구현
- [ ] gallery 등록 / 삭제 / 촬영 UI 구현
- [x] wrapper API에 RKNN backend 선택 표면 추가
- [x] 나머지 model pack을 wrapper 표면에 연결
- [x] SDK 상위 package 구조 정리
- [x] OrangePI `RKNN Lite2` smoke 성공

## Recent Logs

- 2026-04-01: 모듈 문서 초안을 만들고 역할을 `실기기 실행 전용`으로 고정했다.
- 2026-04-01: reference 저장소를 기준으로 speaker 경로를 제거하고 `face-only` 웹 데모를 현재 모듈의 첫 구현 대상으로 정했다.
- 2026-04-01: `face_gallery_recognizer.py`, `face_gallery_web_demo.py`, `image_capture.py`를 추가해 gallery 자동 로드와 웹 스트리밍 초안을 만들었다.
- 2026-04-01: `requirements_ort_cpu_probe.txt`, `setup_orangepi_ort_cpu_env.sh`, `install_orangepi_service.sh`, `insightface_gallery_web.service.template`를 추가했다.
- 2026-04-01: `runtime/gallery/README.local.md`와 `.gitignore`를 추가해 로컬 gallery 규칙을 고정했다.
- 2026-04-01: 로컬 `../envs/ifr_ort_cpu_probe` 생성, `onnxruntime 1.24.4`, `CPUExecutionProvider` 확인, `buffalo_s` 초기화까지 통과했다.
- 2026-04-01: `face_gallery_web_demo.py`를 `json` 입력, 빈 gallery 상태로 띄워 `http://127.0.0.1:5060/api/status` 응답을 확인했다.
- 2026-04-01: OrangePI에서 `python3.10-venv` 설치 뒤 `../envs/ifr_ort_cpu_probe` 생성, `onnxruntime 1.23.2`, `CPUExecutionProvider` 확인, `buffalo_s` 초기화까지 통과했다.
- 2026-04-01: OrangePI에서 `insightface_gallery_web.service`를 올리고 LAN `api/status`, `stream.mjpg` 응답을 확인했다.
- 2026-04-01: OrangePI 카메라 probe 결과 초기에는 `20`이 열렸지만, 이후 USB 카메라가 `21`로 다시 잡히는 상황을 확인했다.
- 2026-04-01: OrangePI 재점검 결과 `V4L2 + /dev/video21`과 `/dev/v4l/by-id/...video-index0` 경로에서 읽기 성공을 확인했다.
- 2026-04-01: 웹 데모를 `capture`, `inference`, `render` 세 루프로 분리하고, overlay에 `capture_fps`, `infer_fps`, `stream_fps`를 표시하도록 수정했다.
- 2026-04-01: `buffalo_sc`, `buffalo_s`, `buffalo_m`, `buffalo_l` CPU benchmark를 기록했고 현재 기준으로 `buffalo_s`와 `buffalo_sc`를 우선 비교 대상으로 본다.
- 2026-04-01: 최신 commit을 OrangePI에 pull한 뒤 service를 다시 설치했고, `camera-source=/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0` 기준으로 `api/status`의 FPS 필드가 실제 값으로 갱신되는 것을 확인했다.
- 2026-04-01: 에이전트 모드 전환 뒤 runtime의 다음 목표를 `RKNN face SDK`와 `front / back 분리형 새 web demo`로 확장했다.
- 2026-04-01: OrangePI에 `../envs/ifr_rknn_lite2_cp310`을 만들었고 `rknnlite.api.RKNNLite` import를 확인했다.
- 2026-04-01: `probe_rknn_lite2.py`를 추가해 `.rknn` 단건 파일 입력 smoke 경로를 만들었다.
- 2026-04-01: OrangePI 첫 RKNN smoke에서 `cv2` 누락을 확인했고, Lite2 환경에 `opencv-python-headless 4.10.0.84`를 추가해 해결했다.
- 2026-04-01: OrangePI에서 `det_500m_fp16.rknn` probe가 성공했고 `9`개 출력 tensor와 비영값 범위를 확인했다.
- 2026-04-01: OrangePI에서 `w600k_mbf_fp16.rknn` probe가 성공했고 `1 x 512` 출력 tensor와 비영값 범위를 확인했다.
- 2026-04-01: `runtime.face_wrapper`가 Lite2 env에서 `onnxruntime` 때문에 import 실패하던 문제를 lazy import로 수정했다.
- 2026-04-01: RKNN detector 점수가 비정상적으로 낮은 원인이 `float32 NCHW` 이중 전처리였음을 확인했고, `raw RGB uint8 NHWC` 입력으로 고쳤다.
- 2026-04-01: NHWC 전환 뒤 detector grid shape 계산이 깨지던 문제를 `self.input_height`, `self.input_width` 기준으로 수정했다.
- 2026-04-01: OrangePI에서 `FaceWrapper(backend="rknn", model_pack="buffalo_sc")`로 gallery 1명 file-input end-to-end를 검증했고 `TestUser`, `similarity 1.0`, `det_score 0.6806640625`를 확인했다.
- 2026-04-01: `rknn_model_zoo.py`가 `pack.json`과 alias를 읽도록 보강했고, `buffalo_s`를 `buffalo_sc` alias로 해석하는 경로를 확인했다.
- 2026-04-01: OrangePI에서 `buffalo_s(alias)`, `buffalo_m`, `buffalo_l`를 `FaceWrapper(backend="rknn")`로 다시 검증했고 모두 `TestUser`, `similarity 1.0`을 확인했다.
- 2026-04-01: `FaceSDK`와 `list_model_packs()`를 추가해 future web demo backend가 runtime model zoo를 직접 읽을 수 있는 상위 표면을 만들었다.
- 2026-04-01: OrangePI Lite2 env에서 `from runtime import FaceSDK`, `FaceSDK.list_model_packs()`, `describe()`, `infer()`까지 실제로 다시 확인했고 alias pack `buffalo_s -> buffalo_sc`와 `gallery_count 1` 상태가 기대대로 나왔다.
