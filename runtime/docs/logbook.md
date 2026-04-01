# runtime logbook

## 읽기 규칙

- 먼저 `../../docs/AGENT.md`를 읽는다.
- 그다음 `../README.md`를 읽고 이 모듈의 역할과 경계를 맞춘다.
- 그다음 `../../docs/logbook.md`를 읽고 프로젝트 전역 결정과 활성 체크리스트를 맞춘다.
- 아직 archive 문서는 없다. archive가 생기면 최신 `logbook_*.md` 1개를 함께 읽는다.

## 현재 모듈 스냅샷

- `face-only` 웹 데모와 CPU 검증용 `ONNX Runtime` 환경 초안을 만들었다.
- 로컬 `../envs/ifr_ort_cpu_probe` 생성과 `InsightFace` CPU 초기화 smoke는 통과했다.
- 로컬 `http://127.0.0.1:5060/api/status` 응답 smoke는 통과했다.
- 현재 목적은 이 초안을 `OrangePI RK3588`에서 실제로 설치하고 서비스로 띄우는 것이다.
- reference 저장소에서 가져올 최소 흐름은 `gallery 자동 로드 -> 웹캠 또는 JSON 입력 -> 실시간 얼굴 인식 -> 웹 스트리밍`이다.
- 현재 venv 이름은 `../envs/ifr_ort_cpu_probe`로 고정했다.
- 아직 정하지 않은 항목은 첫 번째 타깃 모델팩 고정 여부와 기본 카메라 입력 장치 번호다.

## 현재 모듈 결정

- 이 모듈은 실기기 실행과 성능 측정을 맡는다.
- 원본 모델과 변환 로직은 `conversion/`이 맡는다.
- 큰 산출물은 `runtime/results/` 아래에 둔다.
- 현재 `face-only` 웹 데모는 CPU 검증 경로로 먼저 세운다.
- `ONNX Runtime`은 검증용 CPU 경로로 두고, RK3588 NPU 실시간 주경로는 이후 `RKNN`으로 옮긴다.
- gallery 로컬 자산은 `runtime/gallery/` 아래에 두고 git으로 추적하지 않는다.
- 서비스 실행은 `insightface_gallery_web.service` 한 개로 통일한다.

## 현재 활성 체크리스트

- [x] `face-only` 얼굴 인식 모듈 초안 작성
- [x] 웹 스트리밍 데모 entry script 작성
- [x] gallery 로컬 폴더 규칙 정의
- [x] CPU 검증용 requirements 파일 작성
- [x] OrangePI용 venv 생성 스크립트 작성
- [x] systemd 서비스 파일 작성
- [ ] OrangePI에서 venv 생성과 패키지 설치 smoke 수행
- [ ] OrangePI에서 서비스 기동과 네트워크 접속 smoke 수행

## Recent Logs

- 2026-04-01: 모듈 문서 초안을 만들고 역할을 `실기기 실행 전용`으로 고정했다.
- 2026-04-01: reference 저장소를 기준으로 speaker 경로를 제거하고 `face-only` 웹 데모를 현재 모듈의 첫 구현 대상으로 정했다.
- 2026-04-01: `face_gallery_recognizer.py`, `face_gallery_web_demo.py`, `image_capture.py`를 추가해 gallery 자동 로드와 웹 스트리밍 초안을 만들었다.
- 2026-04-01: `requirements_ort_cpu_probe.txt`, `setup_orangepi_ort_cpu_env.sh`, `install_orangepi_service.sh`, `insightface_gallery_web.service.template`를 추가했다.
- 2026-04-01: `runtime/gallery/README.local.md`와 `.gitignore`를 추가해 로컬 gallery 규칙을 고정했다.
- 2026-04-01: 로컬 `../envs/ifr_ort_cpu_probe` 생성, `onnxruntime 1.24.4`, `CPUExecutionProvider` 확인, `buffalo_s` 초기화까지 통과했다.
- 2026-04-01: `face_gallery_web_demo.py`를 `json` 입력, 빈 gallery 상태로 띄워 `http://127.0.0.1:5060/api/status` 응답을 확인했다.
