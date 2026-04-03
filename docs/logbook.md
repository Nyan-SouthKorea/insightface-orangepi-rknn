# logbook

## 읽기 규칙

- 비사소한 작업에서는 항상 `docs/AGENT.md`를 먼저 읽는다.
- 그다음 `README.md`를 읽고 프로젝트 전역 구조와 고정 메모를 맞춘다.
- 그다음 이 문서를 읽고 현재 스냅샷, 전역 결정, 활성 체크리스트, 최근 로그를 확인한다.
- 모듈 작업 전에는 관련 모듈 `README.md`와 해당 모듈 `docs/logbook.md`를 함께 읽는다.

## 현재 프로젝트 스냅샷

- 현재 단계는 `RKNN 주경로 기준 repo 정리 + 배포용 문서 리팩토링` 단계다.
- 프로젝트 목표는 `InsightFace -> ONNX -> RKNN -> OrangePI RK3588 실시간 추론` 주경로를 안정적으로 만드는 것이다.
- 최종 산출물 방향은 `SDK처럼 import하는 RKNN wrapper`와 `front / back이 분리된 별도 web console`을 분리하는 구조로 고정했다.
- 현재 canonical 모듈은 `conversion/`과 `runtime/` 두 개다.
- 현재 reference 소스는 `/tmp/jetson-face-speaker-recognition`에 임시 clone해 둔 상태다.
- host RKNN 변환 환경은 `../envs/ifr_rknn_host_cp310`, OrangePI RKNN Lite2 환경은 `../envs/ifr_rknn_lite2_cp310`으로 잡았다.
- face-only 기준 canonical `RKNN model zoo`는 `buffalo_sc`, `buffalo_s(alias)`, `buffalo_m`, `buffalo_l` 네 이름으로 정리했고, 비교용 `buffalo_m_i8`도 추가했다.
- 현재 기본 runtime pack은 `buffalo_m`로 둔다.
- `OrangePI`는 고정 LAN 주소 정책으로 운영하고, 실제 네트워크 세부는 로컬 전용 문서에만 둔다.
- local SDK 표면으로 `runtime.FaceSDK`와 `FaceSDK.list_model_packs()`를 유지한다.
- `runtime.FaceSDK`는 `infer`, `detect_faces`, `extract_face_embeddings`, `extract_embedding`, `match_embedding`, `compare_embeddings`, `list_gallery_people`를 함께 여는 상위 import 이름으로 유지한다.
- 새 web console backend는 `FastAPI`, frontend는 `React + Vite`로 고정했다.
- 현재 web console은 `모델 전환`, `메모리 정리`, `gallery 등록`, `촬영 저장`, `다중 업로드`, `삭제`, `MJPEG 스트리밍`, `상태 API`, `live-state stream`을 지원한다.
- root README가 직접 참조하는 공용 자산은 현재 `assets/readme/`에 둔다.
- README에는 최종 표시용 GIF/PNG만 남기고, 중간 생성 스크립트와 입력 메모는 canonical tracked 자산에서 제거했다.
- frontend build 산출물 `runtime/web_frontend/dist/`는 로컬에서 생성하고 tracked repo에는 두지 않는다.
- CPU baseline은 결과 JSON만 보존하고, ONNX 전용 보조 코드와 재생성 가능한 build 캐시는 canonical repo에서 제거했다.
- 같은 `RKNN model zoo`를 `Android 기반 RK3588`에서도 재사용 가능한 방향으로 보고, 현재 repo는 Linux runtime 기준 문서와 자산을 유지한다.
- Android bring-up과 디버깅은 기본적으로 `ssh`보다 `adb` 기준으로 보는 것이 맞다.

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
- 공식 Rockchip `rknn-toolkit2`와 `rknpu2` 문서 기준 RK3588 NPU 사용 경로는 `ONNX 등 원본 모델 -> RKNN 변환 -> RKNN Runtime/Lite2 추론`이다.
- 현재 canonical `RKNN model zoo`는 tracked repo의 `conversion/results/model_zoo/rk3588/` 아래에 둔다.
- `conversion/results/model_zoo/<platform>/<pack>/pack.json`은 runtime이 읽는 canonical pack manifest다.
- 현재 런타임 제품 방향은 `wrapper가 주 제품`, `web demo는 검증과 운영 인터페이스`다.
- 현재 web console은 `front / back`을 분리하고, 실시간 FPS와 상태는 웹 화면에서 그린다.
- 현재 backend는 `--inference-fps 0`을 기본으로 두고 최신 프레임 우선 추론으로 처리한다.
- `buffalo_s`는 현재 face-only 주경로에서 `buffalo_sc`의 alias pack으로 취급하고, 별도 변환보다 metadata alias와 보조 모델 여부를 나눠 관리한다.
- `buffalo_m_i8`는 비교용 `INT8` pack으로 model zoo에 추가했다.
- Android 확장에서는 `model zoo`, 전처리/후처리 기준, gallery 구조를 공용 자산으로 두고, camera/UI/device adapter는 Android 구조에 맞춰 별도 구현한다.
- gallery 저장 구조는 `runtime/gallery/<person_id>/meta.json`, `runtime/gallery/<person_id>/images/*`를 기본으로 한다.
- 로컬 워크스페이스 sibling 구조는 `repo / envs / secrets`로 맞춘다.

## 현재 benchmark 요약

### CPU baseline 보존 기록

- 실행 위치: `OrangePI RK3588`
- 실행 환경: `onnxruntime 1.23.2`, `CPUExecutionProvider`
- 결과 JSON: `runtime/results/260401_1530_ort_cpu_benchmark/summary.json`
- 해석: CPU baseline은 비교 기준선으로만 유지한다.

| model pack | detection model | recognition model | detection avg ms | recognition avg ms | pipeline avg ms | pipeline FPS |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| buffalo_sc | det_500m.onnx | w600k_mbf.onnx | 49.21 | 23.09 | 139.57 | 7.16 |
| buffalo_s | det_500m.onnx | w600k_mbf.onnx | 50.60 | 27.01 | 160.37 | 6.24 |
| buffalo_m | det_2.5g.onnx | w600k_r50.onnx | 152.80 | 318.90 | 635.75 | 1.57 |
| buffalo_l | det_10g.onnx | w600k_r50.onnx | 573.89 | 429.12 | 1102.10 | 0.91 |

### RKNN all-pack benchmark

- 실행 위치: `OrangePI RK3588`
- 실행 환경: `../envs/ifr_rknn_lite2_cp310`
- 결과 JSON: `runtime/results/260403_0942_rknn_all_pack_benchmark/summary.json`

| model pack | resolved pack | dtype | load ms | detection avg ms | recognition avg ms | pipeline avg ms | pipeline FPS | result count |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| buffalo_sc | buffalo_sc | fp | 354.14 | 54.02 | 6.28 | 46.96 | 21.29 | 1 |
| buffalo_s | buffalo_sc | fp | 270.52 | 46.13 | 6.03 | 65.67 | 15.23 | 1 |
| buffalo_m | buffalo_m | fp | 586.53 | 58.82 | 24.73 | 95.01 | 10.52 | 1 |
| buffalo_m_i8 | buffalo_m_i8 | i8 | 390.42 | 27.70 | 11.19 | 46.36 | 21.57 | 1 |
| buffalo_l | buffalo_l | fp | 618.27 | 110.31 | 25.81 | 116.20 | 8.61 | 1 |

## 현재 활성 체크리스트

- [x] RKNN-only SDK 표면으로 정리
- [x] web console 실행 경로를 `runtime/web_backend/main.py` 기준으로 단순화
- [x] README와 모듈 README에서 삭제된 경로 참조 제거
- [x] README 자산은 최종 표시용 GIF/PNG만 남기고 중간 생성 스크립트 제거
- [x] frontend build 산출물과 local cache를 tracked repo에서 제거
- [x] CPU 전용 보조 코드 제거 후 benchmark JSON만 보존
- [x] model zoo, benchmark JSON, SDK 예제, web backend/frontend source는 유지

## Recent Logs

- 2026-04-01: 프로젝트의 첫 번째 canonical 문서로 `README.md`, `docs/logbook.md`, 모듈 `README.md`, 모듈 `docs/logbook.md` 초안을 만들었다.
- 2026-04-01: 초기 모듈 경계를 `conversion/`과 `runtime/`으로 고정했다.
- 2026-04-01: reference 저장소 `jetson-face-speaker-recognition`를 `/tmp/jetson-face-speaker-recognition`에 clone해 구조를 확인했다.
- 2026-04-01: 공식 Rockchip 경로를 따라 `ONNX -> RKNN -> RKNN Lite2` 주경로를 확정했다.
- 2026-04-01: canonical `RKNN model zoo`를 `conversion/results/model_zoo/` 아래 tracked 산출물로 열었다.
- 2026-04-01: `runtime.FaceSDK`, `FaceSDK.list_model_packs()`, `FastAPI + React` web console 구조를 추가했다.
- 2026-04-01: OrangePI에서 `buffalo_sc -> buffalo_m -> buffalo_l -> buffalo_m` 전환과 gallery API를 실제로 통과했다.
- 2026-04-01: `buffalo_m_i8` INT8 pack을 export했고 OrangePI benchmark에서 `46.36 ms / 21.57 FPS`를 확인했다.
- 2026-04-03: README를 제품 소개 문서 형태로 재정리하고 CPU/RKNN benchmark, Lite2 배경, SDK 사용 예제를 함께 정리했다.
- 2026-04-03: tracked 문서는 프로젝트 작성자나 운영자가 직접 정리한 기술 문서처럼 쓰는 기준을 `docs/AGENT.md`에 반영했다.
- 2026-04-03: repo 슬림화 작업에서 CPU 전용 보조 코드, README 자산 생성 스크립트, frontend build 산출물, local calibration bundle, cache 디렉터리를 canonical 경로에서 제거했다.
- 2026-04-03: Android 기반 RK3588 확장 가능성과 `adb` 중심 bring-up 메모를 README와 runtime README, project logbook에 반영했다.
