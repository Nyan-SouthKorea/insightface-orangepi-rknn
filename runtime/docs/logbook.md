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
- 현재 목적은 실제 gallery 이미지를 넣고, 선택할 모델팩을 CPU 기준표로 결정한 뒤, 같은 표면으로 RKNN backend를 붙이는 것이다.
- 현재 venv 이름은 `../envs/ifr_ort_cpu_probe`로 고정했다.
- 현재 OrangePI USB 카메라의 stable path는 `/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0`이고, 장치 번호는 현재 `/dev/video21`이다.

## 현재 모듈 결정

- 이 모듈은 실기기 실행과 성능 측정을 맡는다.
- 원본 모델과 변환 로직은 `conversion/`이 맡는다.
- 큰 산출물은 `runtime/results/` 아래에 둔다.
- 현재 `face-only` 웹 데모는 CPU 검증 경로로 먼저 세운다.
- `ONNX Runtime`은 검증용 CPU 경로로 두고, RK3588 NPU 실시간 주경로는 이후 `RKNN`으로 옮긴다.
- gallery 로컬 자산은 `runtime/gallery/` 아래에 두고 git으로 추적하지 않는다.
- service 설치 스크립트는 `camera-source`를 자동 선택해 unit 파일에 박아 넣는다.
- wrapper가 주 제품이고 web demo는 사람 확인용 entry다.

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
- [ ] 실제 gallery 사용자 이미지 입력 후 인식 품질 확인
- [ ] 첫 번째 기본 모델팩 확정
- [ ] wrapper API에 RKNN backend 선택 표면 추가
- [ ] RKNN runtime smoke entry script 초안 작성

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
