# logbook

## 읽기 규칙

- 비사소한 작업에서는 항상 `docs/AGENT.md`를 먼저 읽는다.
- 그다음 `README.md`를 읽고 프로젝트 전역 구조와 고정 메모를 맞춘다.
- 그다음 이 문서를 읽고 현재 스냅샷, 전역 결정, 활성 체크리스트, 최근 로그를 확인한다.
- 아직 archive 문서는 없다. archive가 생기면 최신 `docs/logbook_archive/logbook_*.md` 1개를 함께 읽는다.
- 모듈 작업 전에는 관련 모듈 `README.md`와 해당 모듈 `docs/logbook.md`를 함께 읽는다.

## 현재 프로젝트 스냅샷

- 현재 단계는 `문체 기준 정리 + web demo 실행 안내 분리 + 수동 검증 준비` 단계다.
- 프로젝트 목표는 `InsightFace -> ONNX -> RKNN -> OrangePI RK3588 실시간 추론` 주경로를 안정적으로 만드는 것이다.
- 최종 산출물 방향은 `SDK처럼 import하는 RKNN wrapper`와 `front / back이 분리된 별도 web console`을 분리하는 구조로 고정했다.
- 현재 canonical 모듈은 `conversion/`과 `runtime/` 두 개다.
- 현재 reference 소스는 `/tmp/jetson-face-speaker-recognition`에 임시 clone해 둔 상태다.
- ONNX CPU 검증용 venv 이름은 `../envs/ifr_ort_cpu_probe`로 확정했다.
- host RKNN 변환 환경은 `../envs/ifr_rknn_host_cp310`, OrangePI RKNN Lite2 환경은 `../envs/ifr_rknn_lite2_cp310`으로 잡았다.
- face-only 기준 canonical `RKNN model zoo`는 `buffalo_sc`, `buffalo_s(alias)`, `buffalo_m`, `buffalo_l` 네 이름으로 정리했고, 비교용 `buffalo_m_i8`도 추가했다.
- 현재 기본 runtime pack은 `buffalo_m`로 둔다.
- 현재 `OrangePI` 고정 LAN 주소는 `eth0 = 192.168.20.238/24`, gateway `192.168.20.4`, DNS `168.126.63.1`이다.
- 현재 `OrangePI` 서비스와 수동 smoke는 숫자 인덱스보다 `camera-source`를 우선 사용하며, 현재 USB 카메라 기준 대표 경로는 `/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0`이다.
- local SDK 표면으로 `runtime.FaceSDK`와 `FaceSDK.list_model_packs()`를 유지한다.
- `runtime.FaceSDK`는 `detect_faces`, `extract_face_embeddings`, `extract_embedding`, `match_embedding`, `compare_embeddings`, `list_gallery_people`를 함께 여는 상위 import 이름으로 유지한다.
- local 기준 새 web console은 `runtime/web_backend/main.py`와 `runtime/web_frontend/` 조합으로 구현했다.
- 새 web console backend는 `FastAPI`, frontend는 `React + Vite`로 고정했다.
- 새 web console backend는 `모델 전환`, `메모리 정리`, `gallery 등록`, `촬영 저장`, `다중 업로드`, `삭제`, `MJPEG 스트리밍`, `상태 API`, `live-state stream`을 지원한다.
- OrangePI 수동 smoke에서 `5050` 포트로 새 web console을 실제 카메라와 함께 검증했다.
- 수동 smoke 기준 모델 전환은 `buffalo_sc -> buffalo_m -> buffalo_l -> buffalo_m` 순서에서 예외 없이 통과했고, 메모리 사용량도 전환 결과에 맞춰 갱신됐다.
- 수동 smoke 기준 gallery API는 `인물 생성 -> 현재 프레임 저장 -> 업로드 -> 삭제`를 실제로 통과했다.
- old CPU demo source와 old service 설치 스크립트는 더 이상 canonical 경로가 아니므로 삭제 대상으로 정리했고, local repo에서는 이미 제거했다.
- 기존 화면이 `1초에 1~2번만 바뀌는 것처럼 보이던` 원인은 frontend의 `1초 polling`과 backend의 `12 FPS` 인위 제한이 겹친 것이었고, 현재는 `live-state stream + 최신 프레임 우선 추론`으로 정리했다.
- 현재 갤러리 UI는 `새 프로필 추가`, `갤러리 목록`, `선택 인물 편집` 세 영역으로 다시 나눴다.
- OrangePI `5000` service는 현재 사용자의 수동 실행 검증을 위해 중지한 상태다. 마지막 service 확인 시 `runtime/web_backend/main.py`, `buffalo_m`, `capture_fps 9.98`, `inference_fps 10.14`, `last_inference_duration_ms 45.1`, `avg_inference_duration_ms 52.5`, `gallery_count 1`를 기록했다.
- OrangePI all-pack benchmark를 다시 실행했고, `buffalo_sc 21.29 FPS`, `buffalo_m_i8 21.57 FPS`, `buffalo_m 10.52 FPS`, `buffalo_l 8.61 FPS`를 확인했다.
- root README가 직접 참조하는 공용 자산은 현재 `assets/readme/`에 둔다.
- `repo/사용자 추가 폴더/` 입력 자산은 `영상 4개 + 이미지 2개`로 확인했고, README용 GIF와 이미지 산출물은 `assets/readme/build_demo_assets.py`로 재생성 가능하게 정리했다.
- README용 데모 인물은 프레임 샘플, 등록 영상, 현재 OrangePI gallery metadata를 함께 확인한 결과 `라이언 / Ryan`으로 정리했다.
- root README는 현재 프로젝트 작성자 관점의 설명 문장과 `환경 준비`, `매번 수동 실행`, `service 실행`을 분리한 실행 안내를 포함하는 소개 문서로 유지한다.
- `buffalo_s`는 `pack.json`만 가진 face-only alias pack으로 유지하고, 실제 `.rknn`은 `buffalo_sc/` 산출물을 재사용한다. 이 점은 README와 conversion README에 명시한다.
- `service 실행` 문서는 foreground 수동 실행과 `systemd` background 실행의 차이, `systemctl`, `journalctl`, install script의 역할이 바로 읽히게 유지한다.
- `runtime.FaceSDK`는 현재 `infer`, `detect_faces`, `extract_face_embeddings`, `extract_embedding`, `match_embedding`, `compare_embeddings`, `list_gallery_people`, `list_model_packs` 표면을 공개한다.
- OrangePI에서 `runtime/examples/sdk_quickstart.py`, `runtime/examples/sdk_custom_usage.py`를 실제로 다시 실행해 gallery match와 embedding compare 동작을 확인했다.
- custom SDK 추가 뒤 마지막 service smoke에서 OrangePI `5000` service의 `api/status`, root HTML 응답을 다시 확인했다.

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
- 현재 `RKNN Lite2` 입력은 `raw RGB uint8 NHWC`로 넣어야 하고, 변환 시 넣은 `mean/std` 전처리를 runtime에서 다시 하지 않는다.
- `buffalo_s`는 현재 face-only 주경로에서 `buffalo_sc`의 alias pack으로 취급하고, 별도 변환보다 metadata alias와 보조 모델 여부를 나눠 관리한다.
- 나머지 실제 RKNN 변환 순서는 `buffalo_m` 다음 `buffalo_l`로 둔다.
- canonical `RKNN model zoo`는 현재 tracked repo의 `conversion/results/model_zoo/rk3588/` 아래에 두고, OrangePI는 `git pull`로 같은 pack을 받는다.
- `conversion/results/model_zoo/<platform>/<pack>/pack.json`은 runtime이 읽는 canonical pack manifest다.
- `runtime.FaceSDK`는 현재 `FaceWrapper` 위의 안정된 import 이름이고, `list_model_packs()`로 future web demo backend가 pack 목록을 바로 읽게 한다.
- 현재 데모 형태는 `GUI`가 아니라 `LAN에서 볼 수 있는 web console`로 고정한다.
- 현재 canonical service 대상은 `runtime/web_backend/main.py`와 `runtime/install_orangepi_rknn_web_service.sh` 조합이다.
- 현재 런타임 제품 방향은 `wrapper가 주 제품`, `web demo는 검증과 운영 인터페이스`다.
- 현재 web console은 `front / back`을 분리하고, 실시간 FPS와 상태는 웹 화면에서 그린다.
- 현재 web console은 `모델 전환`, `gallery 등록`, `다중 이미지 추가`, `삭제`, `촬영 저장`, `갤러리 목록 관리`, `live-state stream`을 지원한다.
- 현재 overlay와 최근 결과는 `/api/live-state/stream`으로 갱신하고, 느린 `1초 polling`은 더 이상 주경로가 아니다.
- 현재 backend는 `--inference-fps 0`을 기본으로 두고 최신 프레임 우선 추론으로 처리한다.
- 현재 `buffalo_m_i8`는 비교용 `INT8` pack으로 model zoo에 추가했다.
- 현재 `buffalo_sc -> buffalo_m_i8 -> buffalo_l -> buffalo_m` 전환은 모두 warm switch로 통과했고 메모리 에러는 재현되지 않았다.
- gallery 저장 구조는 `runtime/gallery/<person_id>/meta.json`, `runtime/gallery/<person_id>/images/*`를 기본으로 한다.
- old CPU demo source, old service template, old service install 스크립트는 canonical repo에서 제거했다.
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

## 현재 RKNN wrapper smoke 요약

- 실행 위치: `OrangePI RK3588`, `../envs/ifr_rknn_lite2_cp310`
- 입력 이미지: `runtime/results/face_benchmark_input.jpg`
- gallery 입력: `/tmp/rknn_gallery_smoke_stage2/테스트, TestUser/face.jpg`

| model pack | resolved pack | load ms | infer ms | match name | similarity | det score |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| buffalo_s | buffalo_sc | 659.93 | 54.20 | TestUser | 1.00 | 0.6807 |
| buffalo_m | buffalo_m | 575.48 | 156.22 | TestUser | 1.00 | 0.6494 |
| buffalo_l | buffalo_l | 4389.70 | 124.09 | TestUser | 1.00 | 0.6753 |

## 현재 RKNN all-pack benchmark

- 실행 위치: `OrangePI RK3588`, `../envs/ifr_rknn_lite2_cp310`
- 실행 명령:
  - `python runtime/benchmark_rknn_face_sdk.py --image-path runtime/results/face_benchmark_input.jpg --gallery-dir runtime/gallery --model-packs buffalo_sc,buffalo_s,buffalo_m,buffalo_m_i8,buffalo_l --repeat 20 --warmup 5 --output-json runtime/results/260403_0942_rknn_all_pack_benchmark/summary.json`
- 결과 JSON:
  - `runtime/results/260403_0942_rknn_all_pack_benchmark/summary.json`

| model pack | resolved pack | dtype | load ms | detection avg ms | recognition avg ms | pipeline avg ms | pipeline FPS | result count |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| buffalo_sc | buffalo_sc | fp | 354.14 | 54.02 | 6.28 | 46.96 | 21.29 | 1 |
| buffalo_s | buffalo_sc | fp | 270.52 | 46.13 | 6.03 | 65.67 | 15.23 | 1 |
| buffalo_m | buffalo_m | fp | 586.53 | 58.82 | 24.73 | 95.01 | 10.52 | 1 |
| buffalo_m_i8 | buffalo_m_i8 | i8 | 390.42 | 27.70 | 11.19 | 46.36 | 21.57 | 1 |
| buffalo_l | buffalo_l | fp | 618.27 | 110.31 | 25.81 | 116.20 | 8.61 | 1 |

## 현재 활성 체크리스트

- 이번 실행의 목표
  - tracked 문서를 프로젝트 작성자나 운영자가 직접 정리한 기술 문서처럼 읽히게 다듬는다.
  - web demo 실행 안내를 `환경 준비`, `매번 수동 실행`, `service 실행`으로 분리한다.
  - OrangePI service가 현재 수동 검증을 위해 중지된 상태임을 current truth에 반영한다.
- 이번 실행의 비범위
  - runtime 기능 변경
  - 새로운 benchmark 재실행
- 수정 대상 파일과 역할
  - `docs/AGENT.md`: 문서 서술 톤 원칙 추가
  - `README.md`: 데모 소개 문장과 web demo 실행 안내 정리
  - `runtime/README.md`: OrangePI 실행 안내를 단계별로 분리
  - `docs/logbook.md`: 현재 상태와 새 문서 기준 반영
  - `runtime/docs/logbook.md`: 모듈 current truth와 새 문서 기준 반영
- 다음 단계 연결
  - 이후 README와 runtime README는 사용자 검증과 운영 인수인계의 직접 기준 문서로 사용한다.
- 검증 방법과 완료 조건
  - tracked 문서에서 도구가 문서를 대신 쓴 것처럼 보이는 표현이 줄어든다.
  - web demo 실행 안내를 처음 보는 사람도 `환경 준비`와 `실행`을 구분할 수 있다.
  - OrangePI `5000` service가 현재 중지 상태임을 문서에서 바로 확인할 수 있다.
- 체크리스트
  - [x] `AGENT`에 문서 서술 원칙 추가
  - [x] root README 데모 소개 문장 정리
  - [x] root README web demo 실행 안내 분리
  - [x] runtime README 실행 안내 분리
  - [x] project logbook 현재 상태 갱신
  - [x] runtime logbook 현재 상태 갱신

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
- 2026-04-01: `runtime.face_wrapper`의 eager import 때문에 `onnxruntime`가 없는 Lite2 env에서 import 실패가 나는 문제를 lazy import로 수정했다.
- 2026-04-01: RKNN detector 점수가 비정상적으로 낮은 원인이 `float32 NCHW` 이중 전처리였음을 확인했고, `raw RGB uint8 NHWC` 입력으로 고쳤다.
- 2026-04-01: NHWC 전환 뒤 detector grid shape 계산이 깨진 부분을 `self.input_height`, `self.input_width` 기준으로 고쳤다.
- 2026-04-01: OrangePI에서 `FaceWrapper(backend="rknn", model_pack="buffalo_sc")`로 gallery 1명 file-input end-to-end를 다시 검증했고 `gallery_count 1`, `TestUser`, `similarity 1.0`, `det_score 0.6806640625`를 확인했다.
- 2026-04-01: host 기준 `buffalo_s det_500m`, `buffalo_s w600k_mbf`의 SHA256이 `buffalo_sc`와 동일함을 확인했고, face-only 범위에서는 `buffalo_s`를 alias pack으로 취급하기로 했다.
- 2026-04-01: `buffalo_m` 다운로드 중 zip 구조가 `buffalo_m/buffalo_m/*.onnx`로 한 단계 더 중첩되는 것을 확인했고, 이후 변환 스크립트는 nested pack 경로도 허용하도록 보강하기로 했다.
- 2026-04-01: `conversion/export_insightface_pack_rknn.py`를 추가해 pack-level export와 `pack.json` manifest 생성, `buffalo_s` alias manifest 생성을 한 번에 처리하게 했다.
- 2026-04-01: canonical `RKNN model zoo`를 `conversion/results/model_zoo/` 아래 tracked 산출물로 열어, host push 뒤 OrangePI pull로 동일 pack을 받는 흐름을 닫았다.
- 2026-04-01: host에서 `buffalo_m`, `buffalo_l`의 `FP16 RKNN` export를 성공했고, OrangePI에서 `buffalo_s(alias)`, `buffalo_m`, `buffalo_l` 모두 `FaceWrapper(backend="rknn")` 기준 gallery 1명 file-input end-to-end를 통과했다.
- 2026-04-01: `runtime.FaceSDK`와 `FaceSDK.list_model_packs()`를 추가해 SDK-style import 이름과 model pack inventory 표면을 만들었다.
- 2026-04-01: OrangePI에서 `from runtime import FaceSDK` import, `FaceSDK.list_model_packs()`, `FaceSDK(...).describe()`, `infer()`까지 다시 확인했고 `buffalo_s -> buffalo_sc` alias 해석과 `TestUser` 결과를 재검증했다.
- 2026-04-01: `runtime/web_backend/`에 `FastAPI` backend, `runtime/web_frontend/`에 `React + Vite` frontend를 추가해 새 web console 구조를 만들었다.
- 2026-04-01: OrangePI `5050` 수동 smoke에서 새 web console이 실제 카메라를 열고 `capture_fps`, `inference_fps`, `stream_fps`, `latest_results`를 반환하는 것을 확인했다.
- 2026-04-01: OrangePI `5050` 수동 smoke에서 `buffalo_sc -> buffalo_m -> buffalo_l -> buffalo_m` 모델 전환을 다시 수행했고, 메모리 값과 최근 결과가 함께 갱신되는 것을 확인했다.
- 2026-04-01: OrangePI `5050` 수동 smoke에서 `인물 생성 -> 현재 프레임 저장 -> 다중 업로드 -> 삭제` gallery API를 실제로 통과했다.
- 2026-04-01: 새 service 설치 스크립트가 `sudo` 실행 시 `root` 사용자로 service를 생성할 수 있는 문제를 발견했고, `SUDO_USER` 기준으로 보정했다.
- 2026-04-01: old CPU demo 파일 `runtime/face_gallery_web_demo.py`, `runtime/install_orangepi_service.sh`, `runtime/insightface_gallery_web.service.template`는 더 이상 canonical 경로가 아니라고 판단해 삭제 대상으로 전환했다.
- 2026-04-01: 새 service 설치 스크립트가 `/tmp/insightface_gallery_web.service` 고정 파일명 때문에 root 소유 파일과 충돌하는 문제를 확인했고, `mktemp` 기반 임시 파일로 수정했다.
- 2026-04-01: OrangePI가 `00614a0`까지 pull한 뒤 `insightface_gallery_web.service`를 새 `FastAPI + React` web console로 교체했고, `5000`에서 `runtime/web_backend/main.py`가 실제로 기동하는 것을 확인했다.
- 2026-04-01: `http://192.168.20.238:5000/`, `/stream.mjpg`, `/api/status`, `/api/model-pack/select`를 다시 확인했고, 서비스 모드에서도 `buffalo_sc -> buffalo_m` 모델 전환과 `RKNNLite` 상태 표시가 정상 동작함을 확인했다.
- 2026-04-01: `5050` 수동 smoke 프로세스는 내렸고, 최종적으로 `5000`만 listen 중인 상태를 확인했다.
- 2026-04-01: web console이 느리게 보이던 원인이 frontend의 `1초 polling`과 backend의 `12 FPS` 인위 제한임을 확인했고, `live-state stream + 최신 프레임 우선 추론`으로 교체했다.
- 2026-04-01: gallery UI를 `새 프로필 추가`, `갤러리 목록`, `선택 인물 편집` 구조로 다시 나눠 저장된 인물 관리가 화면에서 바로 보이게 정리했다.
- 2026-04-01: local-only `conversion/results/calibration/buffalo_m_i8/` 묶음을 만들고 `buffalo_m_i8` INT8 pack export를 성공했다.
- 2026-04-01: OrangePI benchmark에서 `buffalo_m`은 `80.92 ms / 12.36 FPS`, `buffalo_m_i8`는 `38.63 ms / 25.89 FPS`를 기록했고, 서비스 모델 전환 `buffalo_sc -> buffalo_m_i8 -> buffalo_l -> buffalo_m`도 예외 없이 통과했다.
- 2026-04-03: `repo/사용자 추가 폴더/`의 입력 자산이 실제로는 `영상 4개 + 이미지 2개`임을 확인했다.
- 2026-04-03: 각 영상에서 대표 프레임을 뽑아 보면 데모 인물은 모두 `라이언 / Ryan`으로 보였고, 현재 OrangePI gallery metadata도 같은 이름 1명으로 일치했다.
- 2026-04-03: root README가 직접 쓰는 공용 자산을 `assets/readme/` 아래로 정리하고, `build_demo_assets.py`로 GIF 4개와 이미지 2개를 재생성 가능하게 만들었다.
- 2026-04-03: `demo_assets.json`에 입력 자산 메타데이터, 샘플 프레임 인덱스, `라이언 / Ryan` 추론 근거를 기록했다.
- 2026-04-03: root README를 데모 GIF, CPU/RKNN benchmark, `RKNN Lite2` 설명, `공식 Rockchip toolchain + custom wrapper` 설명 중심으로 전면 개편했다.

- 2026-04-03: `FaceSDK`에 `detect_faces`, `extract_face_embeddings`, `extract_embedding`, `match_embedding`, `compare_embeddings`, `list_gallery_people`를 public helper로 정리했다.
- 2026-04-03: `runtime/examples/sdk_quickstart.py`, `runtime/examples/sdk_custom_usage.py`를 추가하고 OrangePI에서 gallery match, embedding compare smoke를 다시 통과했다.
- 2026-04-03: `buffalo_sc`, `buffalo_s`, `buffalo_m`, `buffalo_m_i8`, `buffalo_l` 전체 pack 기준 RKNN benchmark를 다시 실행했고 canonical 결과를 `runtime/results/260403_0942_rknn_all_pack_benchmark/summary.json`으로 올렸다.
- 2026-04-03: custom SDK 추가 뒤에도 OrangePI `5000` service의 root HTML과 `api/status`를 다시 확인했고 web demo가 그대로 동작함을 재확인했다.
- 2026-04-03: OrangePI working tree에서 구형 subset benchmark 결과 `runtime/results/260401_1828_rknn_face_sdk_benchmark/`를 제거하고 CPU baseline + all-pack 결과만 남겼다.
- 2026-04-03: 사용자의 수동 실행 검증을 위해 OrangePI `5000` service를 중지했고, 현재 `5000` 포트가 비어 있는 상태를 확인했다.
- 2026-04-03: tracked 문서는 프로젝트 작성자나 운영자가 직접 정리한 기술 문서처럼 쓰는 원칙을 `docs/AGENT.md`에 추가했다.
