# logbook

## 읽기 규칙

- 비사소한 작업에서는 항상 `docs/AGENT.md`를 먼저 읽는다.
- 그다음 `README.md`를 읽고 프로젝트 전역 구조와 고정 메모를 맞춘다.
- 그다음 이 문서를 읽고 현재 스냅샷, 전역 결정, 활성 체크리스트, 최근 로그를 확인한다.
- 아직 archive 문서는 없다. archive가 생기면 최신 `docs/logbook_archive/logbook_*.md` 1개를 함께 읽는다.
- 모듈 작업 전에는 관련 모듈 `README.md`와 해당 모듈 `docs/logbook.md`를 함께 읽는다.

## 현재 프로젝트 스냅샷

- 현재 단계는 `1차 RKNN 변환 성공 -> SDK화 -> 새 web demo` 큰 실행의 시작 단계다.
- 프로젝트 목표는 `InsightFace -> ONNX -> RKNN -> OrangePI RK3588 실시간 추론` 주경로를 안정적으로 만드는 것이다.
- 최종 산출물 방향은 `SDK처럼 import하는 RKNN wrapper`와 `front / back이 분리된 별도 web demo`를 분리하는 구조로 고정했다.
- 현재 canonical 모듈은 `conversion/`과 `runtime/` 두 개다.
- 현재 reference 소스는 `/tmp/jetson-face-speaker-recognition`에 임시 clone해 둔 상태다.
- ONNX CPU 검증용 venv 이름은 `../envs/ifr_ort_cpu_probe`로 확정했다.
- 현재 `OrangePI` 고정 LAN 주소는 `eth0 = 192.168.20.238/24`, gateway `192.168.20.4`, DNS `168.126.63.1`이다.
- 현재 `OrangePI` 서비스는 숫자 인덱스보다 `camera-source`를 우선 사용하며, 현재 USB 카메라 기준 대표 경로는 `/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0`이다.
- 현재 OrangePI live status 기준 웹 데모는 `capture_fps 8.33`, `inference_fps 1.05`, `stream_fps 8.95`, `gallery_count 0` 상태로 응답한다.
- 첫 번째 RKNN 타깃은 `buffalo_sc`로 잠정 확정했다.
- host RKNN 변환 환경은 `../envs/ifr_rknn_host_cp310`, OrangePI RKNN Lite2 환경은 `../envs/ifr_rknn_lite2_cp310`으로 잡았다.
- `buffalo_sc det_500m`, `buffalo_sc w600k_mbf`의 host `FP16 RKNN export`는 성공했다.
- OrangePI에서 `buffalo_sc det_500m`, `buffalo_sc w600k_mbf`의 `RKNN Lite2` 파일 입력 smoke도 성공했다.
- 아직 확정되지 않은 항목은 RKNN smoke 기준값, 새 web demo 기술 스택, 최종 model zoo metadata 형식이다.
- 아직 없는 항목은 실제 RKNN 파이프라인 wrapper, 새 web demo front / back 코드다.

## 현재 전역 결정

- 운영 규칙은 `docs/AGENT.md`에 유지한다.
- 프로젝트 전역 설명과 안정된 구조는 `README.md`에 유지한다.
- 현재 truth와 최근 로그는 이 문서에 유지한다.
- 모듈 경계는 우선 `conversion/`과 `runtime/`만 둔다.
- 실제 대용량 산출물은 모듈 내부 `results/` 아래에 둔다.
- 장시간 변환과 실기기 benchmark는 smoke를 먼저 통과시킨다.
- `OrangePI` SSH 접속 정보 같은 비공개 장치 자격 정보는 `../secrets/README.local.md`에 유지한다.
- reference 저장소 `jetson-face-speaker-recognition`에서 가져올 핵심 구조는 `얼굴 갤러리 로드 -> 실시간 입력 -> 얼굴 임베딩 비교 -> 이름 표시` 흐름이다.
- reference 저장소의 화자 인식 경로는 이번 프로젝트 범위에서 제외한다.
- 공식 ONNX Runtime 문서 기준 Python CPU 패키지는 Linux ARM64를 지원한다.
- 공식 ONNX Runtime 문서 기준 Rockchip RKNPU 실행 제공자는 preview이며 지원 플랫폼이 `RK1808 Linux`로 한정되어 있다.
- 공식 Rockchip `rknn-toolkit2`와 `rknpu2` 문서 기준 RK3588 NPU 사용 경로는 `ONNX 등 원본 모델 -> RKNN 변환 -> RKNN Runtime/Lite2 추론`이다.
- 따라서 `OrangePI RK3588`에서 `별도 RKNN 변환 없이 ONNX Runtime만으로 Rockchip NPU 가속`을 쓰는 경로는 현재 기준으로 공식 지원 경로로 보지 않는다.
- 필요하면 ONNX Runtime은 CPU 검증 경로로만 별도 유지하고, 실시간 목표 경로는 RKNN 변환을 기본으로 잡는다.
- host 변환 환경은 `RKNN Toolkit2 2.3.2 + Python 3.10`으로 고정한다.
- host 변환 환경은 `setuptools 75.8.0`, `onnx 1.16.1`까지 함께 고정해야 실제 변환이 된다.
- OrangePI `RKNN Lite2` 환경은 현재 `opencv-python-headless 4.10.0.84`까지 포함해야 smoke script가 바로 돈다.
- 현재 OrangePI의 `librknnrt`는 `2.1.0`, driver는 `0.9.6`으로 보이며, exported model의 toolkit `2.3.2`와 warning은 나지만 smoke 추론은 실제로 성공한다.
- 현재 첫 데모 형태는 `GUI`가 아니라 `LAN에서 볼 수 있는 웹 스트리밍`으로 고정한다.
- 현재 첫 서비스 대상은 `runtime/face_gallery_web_demo.py`와 `insightface_gallery_web.service` 조합이다.
- 현재 런타임 제품 방향은 `wrapper가 주 제품`, `web demo는 검증과 운영 인터페이스`다.
- 현재 웹 데모는 `capture thread`, `inference thread`, `render thread`를 분리해 스트리밍 끊김을 줄이는 구조로 유지한다.
- 최종 web demo는 `front / back`을 분리하고, 실시간 FPS와 상태는 웹 화면에서 그린다.
- 최종 web demo는 `모델 전환`, `gallery 등록`, `다중 이미지 추가`, `삭제`, `촬영 저장`을 지원해야 한다.
- 로컬 워크스페이스 sibling 구조는 `repo / envs / secrets`로 맞춘다.
- 아직 `tools/directory_inventory.py`가 없으므로, 초기 부트스트랩 단계에서는 `find`와 `rg --files` 기반의 shallow inventory로 대신하고 그 사실을 logbook에 남긴다.
- 아직 `tools/logbook_archive_guard.py`가 없으므로, 초기 단계에서는 줄 수를 수동으로 확인한다.

## 현재 CPU benchmark 요약

- 실행 위치: `OrangePI RK3588`
- 실행 환경: `../envs/ifr_ort_cpu_probe`, `onnxruntime 1.23.2`, `CPUExecutionProvider`
- 입력 이미지: `runtime/results/face_benchmark_input.jpg`
- 반복 조건: `warmup 5`, `repeat 20`, `det_size 640`

| model pack | zip size MB | detection model | recognition model | detection avg ms | recognition avg ms | pipeline avg ms | pipeline FPS |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| buffalo_sc | 14.3 | det_500m.onnx | w600k_mbf.onnx | 49.21 | 23.09 | 139.57 | 7.16 |
| buffalo_s | 121.7 | det_500m.onnx | w600k_mbf.onnx | 50.60 | 27.01 | 160.37 | 6.24 |
| buffalo_m | 263.2 | det_2.5g.onnx | w600k_r50.onnx | 152.80 | 318.90 | 635.75 | 1.57 |
| buffalo_l | 275.3 | det_10g.onnx | w600k_r50.onnx | 573.89 | 429.12 | 1102.10 | 0.91 |

## 현재 활성 체크리스트

- 이번 실행의 목표
  - `buffalo_sc`의 detection과 recognition을 `RKNN`으로 실제 성공시킨다.
  - 성공 경로를 문서와 스크립트에 재현 가능하게 고정한다.
  - 같은 구조를 나머지 모델팩 확장과 SDK화, 새 web demo까지 이어지게 만든다.
- 이번 실행의 비범위
  - speaker 경로 재도입
  - 기존 CPU-only demo를 최종 demo로 유지하는 일
- 수정 대상 파일과 역할
  - `README.md`: 최종 제품 방향과 고정 메모
  - `docs/logbook.md`: 전역 truth와 큰 실행 체크리스트
  - `conversion/README.md`: RKNN 변환 경로와 산출물 기준
  - `conversion/docs/logbook.md`: 1차 변환 체크리스트와 recent logs
  - `runtime/README.md`: SDK 표면과 새 web demo 방향
  - `runtime/docs/logbook.md`: runtime 측 준비와 새 demo 체크리스트
  - `conversion/*.py`, `conversion/*.sh`: 변환 smoke와 full entry
  - `runtime/*.py`, `runtime/*`: RKNN 추론, SDK, web demo, service
- 생성되거나 갱신되는 산출물 경로
  - `conversion/results/model_zoo/rk3588/buffalo_sc/*`
  - `conversion/results/model_zoo/*`
  - `runtime/results/<timestamp>_rknn_*`
  - `/etc/systemd/system/insightface_gallery_web.service`
- 다음 단계 연결
  - `conversion/`에서 나온 `RKNN` 산출물은 `runtime/` SDK와 web demo가 직접 사용한다.
  - 새 web demo의 모델 전환 UI는 `conversion/results/model_zoo` metadata를 읽는다.
  - gallery 관리 UI는 `runtime/gallery/` 구조와 직접 연결된다.
- 검증 방법과 완료 조건
  - 첫 번째 `buffalo_sc` RKNN 변환이 재현 가능한 스크립트로 성공한다.
  - OrangePI에서 detection과 recognition이 실제로 동작한다.
  - 성공 경로가 문서에 절차와 입력, 출력, 제약까지 함께 기록된다.
  - 새 SDK 표면과 새 web demo 구조가 서로 분리된 채 연결된다.
- 체크리스트
  - [x] reference 저장소 clone과 구조 확인
  - [x] face 경로와 speaker 경로 분기 지점 확인
  - [x] RK3588 ONNX Runtime 공식 지원 범위 확인
  - [x] shallow inventory로 현재 repo 경로 확인
  - [x] ONNX 검증용 venv 이름 확정
  - [x] ONNX 검증용 venv 생성
  - [x] buffalo 모델팩 CPU benchmark 기록
  - [x] OrangePI 고정 IP 설정
  - [x] 기존 CPU demo 안정화
  - [x] 첫 번째 RKNN 타깃을 `buffalo_sc`로 잠정 확정
  - [x] RKNN Toolkit2 공식 경로와 host 환경 제약 확인
  - [x] `buffalo_sc` 입력 구조와 변환 대상 파일 확정
  - [x] `buffalo_sc det_500m` RKNN smoke 변환
  - [x] `buffalo_sc w600k_mbf` RKNN smoke 변환
  - [x] OrangePI RKNN Runtime smoke 구성
  - [x] `buffalo_sc` 실기기 추론 성공
  - [x] 성공 절차 문서화
  - [ ] 나머지 모델팩 full 변환 계획 확정
  - [ ] RKNN model zoo wrapper 표면 구현
  - [ ] 새 web demo front / back 구조 설계
  - [ ] 새 web demo의 모델 전환 UI 구현
  - [ ] 새 web demo의 gallery 등록 / 삭제 / 촬영 UI 구현
  - [ ] 최종 service 정리와 전체 문서 마감

## Recent Logs

- 2026-04-01: `AGENT.md`만 있던 빈 저장소 상태를 확인했다.
- 2026-04-01: 프로젝트의 첫 번째 canonical 문서로 `README.md`, `docs/logbook.md`, 모듈 `README.md`, 모듈 `docs/logbook.md` 초안을 만들기로 결정했다.
- 2026-04-01: 초기 모듈 경계를 `conversion/`과 `runtime/`으로 고정했다.
- 2026-04-01: 도구 스크립트와 git 저장소가 아직 없으므로, 부트스트랩 예외를 `AGENT.md`와 logbook에 반영하기로 결정했다.
- 2026-04-01: `docs/AGENT.md`의 예시를 변환, 양자화 검증, 실기기 benchmark 중심으로 보정했다.
- 2026-04-01: `../secrets/README.local.md`를 만들고 `OrangePI` SSH 접속 메모를 로컬 전용으로 기록했다.
- 2026-04-01: `ssh orangepi@192.168.20.238 'hostname; whoami; uname -m'` smoke 결과 `orangepicm5`, `orangepi`, `aarch64`를 확인했다.
- 2026-04-01: `assets/prompts`는 이전 LLM 작업 흔적으로 판단해 삭제 대상으로 정리하고, 이를 유도한 `AGENT` 문장도 함께 제거했다.
- 2026-04-01: 로컬 git 저장소 초기화와 첫 push smoke는 완료 상태로 current truth를 갱신했다.
- 2026-04-01: reference 저장소 `jetson-face-speaker-recognition`를 `/tmp/jetson-face-speaker-recognition`에 clone해 구조를 확인했다.
- 2026-04-01: reference 저장소의 `main.py`는 `FaceRecognizer + SpeakerRecognizer` 융합 구조이고, 이번 프로젝트에서는 speaker 경로 전체를 제거 대상으로 판단했다.
- 2026-04-01: 공식 ONNX Runtime 문서와 Rockchip 문서를 함께 확인한 뒤 `ONNX Runtime CPU 검증`, `RKNN 실시간 주경로`로 역할을 분리하기로 결정했다.
- 2026-04-01: `face-only` gallery 인식 웹 데모, CPU 검증용 requirements, OrangePI venv 생성 스크립트, systemd 설치 스크립트와 템플릿을 추가했다.
- 2026-04-01: 로컬 `../envs/ifr_ort_cpu_probe` 생성 smoke에서 `onnxruntime 1.24.4`, 사용 가능 provider `AzureExecutionProvider`, `CPUExecutionProvider`, `buffalo_s` 초기화를 확인했다.
- 2026-04-01: OrangePI에서 `python3.10-venv`를 설치한 뒤 `../envs/ifr_ort_cpu_probe` 생성과 `onnxruntime 1.23.2` CPU provider 초기화를 확인했다.
- 2026-04-01: OrangePI에서 `insightface_gallery_web.service`를 설치했고, 같은 네트워크에서 `http://192.168.20.238:5000/`, `/api/status`, `/stream.mjpg` 응답을 확인했다.
- 2026-04-01: OrangePI 카메라 probe 결과 초기에는 `20`에서 읽기 성공을 확인했지만, 이후 USB 장치 번호 재배치로 서비스가 다시 실패하는 상황을 확인했다.
- 2026-04-01: OrangePI 장치 재점검 결과 USB 카메라는 `/dev/video21`, stable path는 `/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0`로 확인했다.
- 2026-04-01: 웹 데모를 `capture`, `inference`, `render` 세 thread로 분리하고, overlay에 `capture_fps`, `infer_fps`, `stream_fps`를 표시하도록 바꿨다.
- 2026-04-01: OrangePI LAN 연결을 `nmcli`로 manual 고정 IP로 전환해 재부팅 뒤에도 `192.168.20.238`을 유지하게 설정했다.
- 2026-04-01: OrangePI CPU benchmark를 `buffalo_sc`, `buffalo_s`, `buffalo_m`, `buffalo_l` 네 pack으로 측정했고, 현재 기준 균형점은 `buffalo_s`, 최대 경량 후보는 `buffalo_sc`로 우선 판단했다.
- 2026-04-01: 최신 commit pull 뒤 `insightface_gallery_web.service`를 다시 설치했고, `camera-source=/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0`, `capture_fps 8.33`, `inference_fps 1.05`, `stream_fps 8.95`, `last_error=""` 상태를 확인했다.
- 2026-04-01: 사용자가 `에이전트 모드`를 선언했고, 큰 실행 순서를 `1차 RKNN 변환 성공 -> 전체 모델 확장 -> SDK화 -> 새 web demo`로 고정했다.
- 2026-04-01: 1차 RKNN 타깃은 가장 작은 `buffalo_sc`로 잡고 `det_500m`, `w600k_mbf`부터 성공시키기로 했다.
- 2026-04-01: host에 `RKNN Toolkit2 2.3.2 cp310` 환경을 만들었고, 실제 동작을 위해 `setuptools 75.8.0`, `onnx 1.16.1` 고정이 필요함을 확인했다.
- 2026-04-01: OrangePI에 `RKNN Lite2 2.3.2 cp310` 환경을 만들었고 `rknnlite.api.RKNNLite` import를 확인했다.
- 2026-04-01: `export_insightface_rknn.py`로 `buffalo_sc det_500m`, `buffalo_sc w600k_mbf`의 `FP16 RKNN` export를 host에서 성공했다.
- 2026-04-01: OrangePI `RKNN Lite2` smoke에서 `cv2` 누락을 확인했고, `setup_orangepi_rknn_lite2_env.sh`에 `opencv-python-headless 4.10.0.84` 설치를 추가했다.
- 2026-04-01: OrangePI에서 `buffalo_sc det_500m_fp16.rknn` probe 결과 `9`개 출력 tensor와 비영값 범위를 확인했고 detection smoke를 통과했다.
- 2026-04-01: OrangePI에서 `buffalo_sc w600k_mbf_fp16.rknn` probe 결과 `1 x 512` 출력 tensor와 비영값 범위를 확인했고 recognition smoke를 통과했다.
- 2026-04-01: OrangePI runtime은 `librknnrt 2.1.0`, driver `0.9.6`으로 보이며 model toolkit `2.3.2`와 버전 warning은 남지만 현재 smoke 추론 자체는 성공했다.
