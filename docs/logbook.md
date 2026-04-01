# logbook

## 읽기 규칙

- 비사소한 작업에서는 항상 `docs/AGENT.md`를 먼저 읽는다.
- 그다음 `README.md`를 읽고 프로젝트 전역 구조와 고정 메모를 맞춘다.
- 그다음 이 문서를 읽고 현재 스냅샷, 전역 결정, 활성 체크리스트, 최근 로그를 확인한다.
- 아직 archive 문서는 없다. archive가 생기면 최신 `docs/logbook_archive/logbook_*.md` 1개를 함께 읽는다.
- 모듈 작업 전에는 관련 모듈 `README.md`와 해당 모듈 `docs/logbook.md`를 함께 읽는다.

## 현재 프로젝트 스냅샷

- 현재 단계는 `face-only` 웹 데모와 CPU 검증용 런타임 smoke 완료 단계다.
- 프로젝트 목표는 `InsightFace -> ONNX -> RKNN -> OrangePI RK3588 실시간 추론` 주경로를 안정적으로 만드는 것이다.
- 현재 canonical 모듈은 `conversion/`과 `runtime/` 두 개다.
- 현재 reference 소스는 `/tmp/jetson-face-speaker-recognition`에 임시 clone해 둔 상태다.
- ONNX CPU 검증용 venv 이름은 `../envs/ifr_ort_cpu_probe`로 확정했다.
- 아직 확정되지 않은 항목은 첫 번째 타깃 모델 조합, 호스트 환경 버전, 실기기 측정 기준값이다.
- 현재 `OrangePI` 서비스 기본 카메라 장치 번호는 실기기 read probe 기준 `20`으로 둔다.
- 아직 없는 항목은 변환 스크립트, 인벤토리 스크립트, logbook archive 스크립트, RKNN 실기기 entry script다.

## 현재 전역 결정

- 운영 규칙은 `docs/AGENT.md`에 유지한다.
- 프로젝트 전역 설명과 안정된 구조는 `README.md`에 유지한다.
- 현재 truth와 최근 로그는 이 문서에 유지한다.
- 모듈 경계는 우선 `conversion/`과 `runtime/`만 둔다.
- 실제 대용량 산출물은 모듈 내부 `results/` 아래에 둔다.
- 장시간 변환과 실기기 benchmark는 smoke를 먼저 통과시킨다.
- `OrangePI` SSH 접속 정보 같은 비공개 장치 자격 정보는 `../secrets/README.local.md`에 유지한다.
- 로컬 git 저장소는 초기화되어 있다.
- reference 저장소 `jetson-face-speaker-recognition`에서 가져올 핵심 구조는 `얼굴 갤러리 로드 -> 실시간 입력 -> 얼굴 임베딩 비교 -> 이름 표시` 흐름이다.
- reference 저장소의 화자 인식 경로는 이번 프로젝트 범위에서 제외한다.
- 공식 ONNX Runtime 문서 기준 Python CPU 패키지는 Linux ARM64를 지원한다.
- 공식 ONNX Runtime 문서 기준 Rockchip RKNPU 실행 제공자는 preview이며 지원 플랫폼이 `RK1808 Linux`로 한정되어 있다.
- 공식 Rockchip `rknn-toolkit2`와 `rknpu2` 문서 기준 RK3588 NPU 사용 경로는 `ONNX 등 원본 모델 -> RKNN 변환 -> RKNN Runtime/Lite2 추론`이다.
- 따라서 `OrangePI RK3588`에서 `별도 RKNN 변환 없이 ONNX Runtime만으로 Rockchip NPU 가속`을 쓰는 경로는 현재 기준으로 공식 지원 경로로 보지 않는다.
- 필요하면 ONNX Runtime은 CPU 검증 경로로만 별도 유지하고, 실시간 목표 경로는 RKNN 변환을 기본으로 잡는다.
- 현재 첫 데모 형태는 `GUI`가 아니라 `LAN에서 볼 수 있는 웹 스트리밍`으로 고정한다.
- 현재 첫 서비스 대상은 `runtime/face_gallery_web_demo.py`와 `insightface_gallery_web.service` 조합이다.
- 로컬 워크스페이스 sibling 구조는 `repo / envs / secrets`로 맞춘다.
- 아직 `tools/directory_inventory.py`가 없으므로, 초기 부트스트랩 단계에서는 `find`와 `rg --files` 기반의 shallow inventory로 대신하고 그 사실을 logbook에 남긴다.
- 아직 `tools/logbook_archive_guard.py`가 없으므로, 초기 단계에서는 줄 수를 수동으로 확인한다.

## 현재 활성 체크리스트

- 이번 실행의 목표
  - `face-only` gallery 인식 웹 데모와 CPU 검증용 환경을 현재 repo에 반영한다.
  - `OrangePI RK3588`에서 pull 뒤 바로 설치 가능한 서비스 경로를 만든다.
- 이번 실행의 비범위
  - 실제 RKNN 변환 코드 작성
  - RK3588 NPU benchmark 수치 확정
  - reference 저장소 전체 이식
- 수정 대상 파일과 역할
  - `docs/AGENT.md`: workspace 구조 규칙 갱신
  - `docs/logbook.md`: 현재 스냅샷, 전역 결정, 활성 체크리스트, 최근 로그
  - `runtime/README.md`: 현재 runtime 주경로와 entry script 설명
  - `runtime/docs/logbook.md`: 모듈 현재 체크리스트와 최근 로그
  - `runtime/face_gallery_recognizer.py`: gallery 기반 얼굴 인식
  - `runtime/face_gallery_web_demo.py`: 웹 스트리밍 entry script
  - `runtime/image_capture.py`: 웹캠과 JSON 입력 helper
  - `runtime/requirements_ort_cpu_probe.txt`: CPU 검증용 패키지 목록
  - `runtime/setup_orangepi_ort_cpu_env.sh`: OrangePI용 venv 생성과 probe
  - `runtime/install_orangepi_service.sh`: systemd 설치 helper
  - `runtime/insightface_gallery_web.service.template`: 서비스 템플릿
  - `.gitignore`: Python cache 제외
- 생성되거나 갱신되는 산출물 경로
  - `../envs/ifr_ort_cpu_probe`
  - `/etc/systemd/system/insightface_gallery_web.service`
- 다음 단계 연결
  - `runtime/`은 OrangePI 설치 smoke와 네트워크 접속 검증으로 이어진다.
  - `conversion/`은 이후 같은 gallery/runtime 구조를 유지한 채 `InsightFace -> ONNX -> RKNN` 변환 smoke 정의로 이어진다.
- 검증 방법과 완료 조건
  - 새 Python 파일이 문법 오류 없이 compile된다.
  - 로컬과 OrangePI에서 venv 생성과 `onnxruntime` provider 확인이 된다.
  - OrangePI에서 서비스가 올라오고 같은 네트워크 PC에서 웹 페이지 접근이 된다.
- 체크리스트
  - [x] reference 저장소 clone과 구조 확인
  - [x] face 경로와 speaker 경로 분기 지점 확인
  - [x] RK3588 ONNX Runtime 공식 지원 범위 확인
  - [x] shallow inventory로 현재 repo 경로 확인
  - [x] `face-only runtime` 초안 구조를 현재 repo에 반영
  - [x] ONNX 검증용 venv 이름 확정
  - [x] ONNX 검증용 venv 생성
  - [x] OrangePI 설치 smoke
  - [x] OrangePI 서비스 smoke
  - [x] 같은 네트워크 PC 접속 확인
  - [ ] 첫 번째 타깃 `InsightFace` 모델 조합 확정
  - [ ] 호스트 환경과 `OrangePI RK3588` 실기기 환경 표 작성
  - [ ] 변환 smoke 명령과 full 명령 초안 작성
  - [ ] 실기기 benchmark smoke 명령과 full 명령 초안 작성
  - [ ] 인벤토리 스크립트와 archive guard 스크립트 필요 여부 판단
  - [x] git 저장소 초기화 여부 결정

## Recent Logs

- 2026-04-01: `AGENT.md`만 있던 빈 저장소 상태를 확인했다.
- 2026-04-01: 프로젝트의 첫 번째 canonical 문서로 `README.md`, `docs/logbook.md`, 모듈 `README.md`, 모듈 `docs/logbook.md` 초안을 만들기로 결정했다.
- 2026-04-01: 초기 모듈 경계를 `conversion/`과 `runtime/`으로 고정했다.
- 2026-04-01: 도구 스크립트와 git 저장소가 아직 없으므로, 부트스트랩 예외를 `AGENT.md`와 logbook에 반영하기로 결정했다.
- 2026-04-01: `docs/AGENT.md`의 예시를 변환, 양자화 검증, 실기기 benchmark 중심으로 보정했다.
- 2026-04-01: `wc -l` 확인 결과 active logbook들은 archive 기준인 1000줄에 한참 못 미치므로 archive는 만들지 않았다.
- 2026-04-01: `git -C repo rev-parse --is-inside-work-tree` 확인 결과 아직 git 저장소가 초기화되지 않은 상태임을 다시 확인했다.
- 2026-04-01: `../secrets/README.local.md`를 만들고 `OrangePI` SSH 접속 메모를 로컬 전용으로 기록했다.
- 2026-04-01: `ssh orangepi@192.168.20.238 'hostname; whoami; uname -m'` smoke 결과 `orangepicm5`, `orangepi`, `aarch64`를 확인했다.
- 2026-04-01: `assets/prompts`는 이전 LLM 작업 흔적으로 판단해 삭제 대상으로 정리하고, 이를 유도한 `AGENT` 문장도 함께 제거했다.
- 2026-04-01: 로컬 git 저장소 초기화와 첫 push smoke는 완료 상태로 current truth를 갱신했다.
- 2026-04-01: reference 저장소 `jetson-face-speaker-recognition`를 `/tmp/jetson-face-speaker-recognition`에 clone해 구조를 확인했다.
- 2026-04-01: reference 저장소의 핵심 재사용 후보는 `module/face_recognition.py`, `module/image_capture.py`, `01_demo_face-recognition.py`로 판단했다.
- 2026-04-01: reference 저장소의 `main.py`는 `FaceRecognizer + SpeakerRecognizer` 융합 구조이고, 이번 프로젝트에서는 speaker 경로 전체를 제거 대상으로 판단했다.
- 2026-04-01: 공식 ONNX Runtime 문서 기준 Python CPU 패키지는 Linux ARM64를 지원하지만, 공식 Rockchip RKNPU 실행 제공자는 `RK1808 Linux`만 지원한다는 점을 확인했다.
- 2026-04-01: 공식 Rockchip 문서 기준 RK3588 NPU 경로는 RKNN 변환 뒤 `RKNN Runtime/Lite2`를 사용하는 흐름이므로, `ONNX Runtime만으로 RK3588 NPU 가속`은 현재 기준으로 주경로로 채택하지 않기로 잠정 판단했다.
- 2026-04-01: `find`와 `rg --files` 기반 shallow inventory로 현재 repo 경로를 다시 확인했고, 현재 작업 범위를 `runtime` 모듈 구현으로 좁혔다.
- 2026-04-01: `face-only` gallery 인식 웹 데모, CPU 검증용 requirements, OrangePI venv 생성 스크립트, systemd 설치 스크립트와 템플릿을 추가했다.
- 2026-04-01: 로컬 워크스페이스 구조 규칙을 현재 사용자 요청에 맞춰 `repo / envs / secrets`로 갱신했다.
- 2026-04-01: 로컬 `../envs/ifr_ort_cpu_probe` 생성 smoke에서 `onnxruntime 1.24.4`, 사용 가능 provider `AzureExecutionProvider`, `CPUExecutionProvider`, `buffalo_s` 초기화를 확인했다.
- 2026-04-01: 로컬 `face_gallery_web_demo.py`를 `json` 입력 경로로 띄워 `http://127.0.0.1:5060/api/status` 응답을 확인했고, 웹 endpoint 기본 동작이 살아 있음을 점검했다.
- 2026-04-01: `wc -l` 재확인 결과 active logbook 줄 수는 `116`, `49`로 archive 기준 `1000`에 한참 못 미쳐 이번 턴 archive는 만들지 않았다.
- 2026-04-01: OrangePI에서 `python3.10-venv`를 설치한 뒤 `../envs/ifr_ort_cpu_probe` 생성과 `onnxruntime 1.23.2` CPU provider 초기화를 확인했다.
- 2026-04-01: OrangePI에서 `insightface_gallery_web.service`를 설치했고, 같은 네트워크에서 `http://192.168.20.238:5000/`, `/api/status`, `/stream.mjpg` 응답을 확인했다.
- 2026-04-01: OrangePI 카메라 probe 결과 서비스 기본값 `0`, `21`은 실패했고 `11`, `20`은 열렸다.
- 2026-04-01: OrangePI read probe 결과 `11`은 프레임 읽기 실패, `20`은 프레임 읽기 성공이어서 서비스 템플릿 기본 카메라 번호를 `20`으로 조정했다.
- 2026-04-01: 기존에 실행 중인 service는 unit 파일 변경 뒤 자동 재시작되지 않는 것을 확인했고, `install_orangepi_service.sh`를 `restart`까지 수행하도록 보강했다.
- 2026-04-01: `camera-id 20` 기준 재설치 뒤 `api/status`에서 `last_error`가 비어 있고 `last_frame_time`이 갱신되는 것을 확인해, OrangePI CPU 웹 스트리밍 경로가 현재 기준으로 살아 있음을 확인했다.
