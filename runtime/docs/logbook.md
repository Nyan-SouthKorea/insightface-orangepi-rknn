# runtime logbook

## 읽기 규칙

- 먼저 `../../docs/AGENT.md`를 읽는다.
- 그다음 `../README.md`를 읽고 이 모듈의 역할과 경계를 맞춘다.
- 그다음 `../../docs/logbook.md`를 읽고 프로젝트 전역 결정과 활성 체크리스트를 맞춘다.

## 현재 모듈 스냅샷

- 현재 canonical runtime 방향은 `RKNN face SDK + FastAPI backend + React frontend`다.
- 앱 코드가 import하는 표면은 `runtime.FaceSDK`, `runtime.face_wrapper.FaceWrapper`로 유지한다.
- 현재 venv 이름은 `../envs/ifr_rknn_lite2_cp310`으로 고정했다.
- 현재 OrangePI USB 카메라의 stable path는 `/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0`이다.
- 새 web console backend는 `runtime/web_backend/main.py`, frontend source는 `runtime/web_frontend/`다.
- 새 web console은 모델 전환, gallery 등록, 촬영 저장, 업로드, 삭제, `live-state` 결과 갱신, 실시간 FPS, 메모리 표시를 지원한다.
- 갤러리 UI는 현재 `새 프로필 추가`, `갤러리 목록`, `선택 인물 편집` 세 영역으로 나뉘어 있다.
- `buffalo_m_i8` pack을 포함해 selectable pack 전체 benchmark를 다시 실행했고, 현재 fastest pack은 `buffalo_m_i8 21.57 FPS`, 기본 pack `buffalo_m`은 `10.52 FPS`를 기록했다.
- `FaceSDK`는 현재 `detect_faces`, `extract_face_embeddings`, `extract_embedding`, `match_embedding`, `compare_embeddings`, `list_gallery_people`까지 public helper로 제공한다.
- `runtime/examples/sdk_quickstart.py`, `runtime/examples/sdk_custom_usage.py`를 OrangePI Lite2 env에서 실제로 다시 실행했다.
- frontend build 산출물 `runtime/web_frontend/dist/`는 build로 재생성하고 tracked repo에는 포함하지 않는다.
- CPU baseline은 결과 JSON만 보존하고, ONNX 전용 보조 코드는 canonical runtime 경로에서 제거했다.

## 현재 모듈 결정

- 이 모듈은 실기기 실행과 성능 측정을 맡는다.
- 원본 모델과 변환 로직은 `conversion/`이 맡는다.
- 큰 산출물은 `runtime/results/` 아래에 둔다.
- OrangePI Lite2 smoke env는 `RKNNLite + opencv-python-headless 4.10.0.84` 조합으로 유지한다.
- 현재 `RKNN Lite2` 입력은 `raw RGB uint8 NHWC`로 넣고, 변환 시 넣은 `mean/std`를 runtime에서 다시 적용하지 않는다.
- `runtime/rknn_model_zoo.py`는 `pack.json` manifest와 alias를 읽어 `buffalo_s -> buffalo_sc` 같은 pack 선택을 해석한다.
- `runtime.FaceSDK`는 현재 앱 코드와 backend API가 공용으로 쓰는 SDK-style import 이름이다.
- `runtime.FaceSDK`는 `detect_faces`, `extract_face_embeddings`, `extract_embedding`, `match_embedding`, `compare_embeddings`, `list_gallery_people`, `list_model_packs`를 안정된 public surface로 유지한다.
- gallery 로컬 자산은 `runtime/gallery/<person_id>/meta.json`, `runtime/gallery/<person_id>/images/*` 구조로 두고 git으로 추적하지 않는다.
- service 설치 스크립트는 `camera-source`를 자동 선택해 unit 파일에 박아 넣는다.
- wrapper가 주 제품이고 web demo는 사람 확인용 entry다.
- 현재 web console은 `backend API`와 `frontend UI`를 분리한다.
- 현재 web console overlay와 최근 결과는 `/api/live-state/stream`을 기준으로 갱신한다.
- 현재 backend 기본 추론 상한은 `0`, 즉 제한 없이 최신 프레임 우선 처리다.
- 현재 기본 runtime pack은 `buffalo_m`다.
- `buffalo_m_i8`는 비교용 후보 pack으로 유지한다.
- 현재 canonical service 설치 entry는 `runtime/install_orangepi_rknn_web_service.sh`다.

## 현재 benchmark 상세

### CPU baseline 보존 기록

- 결과 JSON: `runtime/results/260401_1530_ort_cpu_benchmark/summary.json`
- 해석: CPU baseline은 비교 기준선으로만 남긴 기록이다.

| model pack | detection avg ms | recognition avg ms | pipeline avg ms | pipeline FPS |
| --- | ---: | ---: | ---: | ---: |
| buffalo_sc | 49.21 | 23.09 | 139.57 | 7.16 |
| buffalo_s | 50.60 | 27.01 | 160.37 | 6.24 |
| buffalo_m | 152.80 | 318.90 | 635.75 | 1.57 |
| buffalo_l | 573.89 | 429.12 | 1102.10 | 0.91 |

### RKNN all-pack benchmark

- 결과 JSON: `runtime/results/260403_0942_rknn_all_pack_benchmark/summary.json`

| model pack | resolved pack | dtype | load ms | detection avg ms | recognition avg ms | pipeline avg ms | pipeline FPS |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| buffalo_sc | buffalo_sc | fp | 354.14 | 54.02 | 6.28 | 46.96 | 21.29 |
| buffalo_s | buffalo_sc | fp | 270.52 | 46.13 | 6.03 | 65.67 | 15.23 |
| buffalo_m | buffalo_m | fp | 586.53 | 58.82 | 24.73 | 95.01 | 10.52 |
| buffalo_m_i8 | buffalo_m_i8 | i8 | 390.42 | 27.70 | 11.19 | 46.36 | 21.57 |
| buffalo_l | buffalo_l | fp | 618.27 | 110.31 | 25.81 | 116.20 | 8.61 |

## 현재 활성 체크리스트

- [x] RKNN-only SDK 표면으로 정리
- [x] web console 실행 경로 단순화
- [x] README와 runtime README에서 삭제된 경로 참조 제거
- [x] frontend build 산출물은 build 결과로만 유지
- [x] CPU 전용 보조 코드 제거 후 benchmark JSON만 보존

## Recent Logs

- 2026-04-01: `runtime.FaceSDK`와 `list_model_packs()`를 추가해 backend와 앱 코드가 함께 쓸 상위 표면을 만들었다.
- 2026-04-01: `runtime/web_backend/`와 `runtime/web_frontend/`를 추가해 새 web console 구조를 만들었다.
- 2026-04-01: OrangePI `5050` 수동 smoke에서 새 web console이 실제 카메라를 열고 FPS와 최근 결과를 갱신하는 것을 확인했다.
- 2026-04-01: OrangePI `5050` 수동 smoke에서 `buffalo_sc -> buffalo_m -> buffalo_l -> buffalo_m` 모델 전환과 gallery API를 실제로 통과했다.
- 2026-04-01: `buffalo_m_i8` pack을 추가했고, OrangePI benchmark에서 `pipeline 46.36 ms / 21.57 FPS`를 기록했다.
- 2026-04-03: custom SDK helper를 public surface로 정리해 detection, embedding, gallery match, cosine similarity compare를 직접 호출할 수 있게 했다.
- 2026-04-03: `runtime/examples/sdk_quickstart.py`, `runtime/examples/sdk_custom_usage.py`를 OrangePI Lite2 env에서 실제 출력과 gallery match로 다시 확인했다.
- 2026-04-03: repo 슬림화 작업에서 ONNX 전용 보조 코드, build 산출물, local cache, 중간 자산 생성 스크립트를 canonical runtime 경로에서 제거했다.
