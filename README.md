# InsightFace-RKNN

## 프로젝트 개요

- 이 프로젝트는 `InsightFace` 계열 얼굴 모델을 `RKNN`으로 변환하고, `OrangePI RK3588`에서 실시간으로 실행하는 것을 목표로 한다.
- 최종 산출물은 두 축으로 나눈다.
- 첫째는 어디서든 import해서 쓰는 `RKNN face SDK`다.
- 둘째는 운영 확인과 갤러리 관리를 맡는 `front / back` 분리형 web console이다.
- 운영 규칙은 `docs/AGENT.md`가 맡는다.
- 현재 상태, 전역 결정, 활성 체크리스트, 최근 로그는 `docs/logbook.md`가 맡는다.
- 모듈별 상세 기준은 각 모듈 `README.md`가 맡는다.

## 최종 산출물 형태

- `conversion/results/model_zoo/rk3588/`에는 `buffalo_sc`, `buffalo_s(alias)`, `buffalo_m`, `buffalo_l`의 canonical `RKNN model zoo`를 둔다.
- `runtime/face_sdk.py`와 `runtime/face_wrapper.py`는 앱 코드가 import해서 쓰는 `RKNN face SDK` 표면을 맡는다.
- `runtime/web_backend/main.py`는 `FastAPI` 기반 backend entry다.
- `runtime/web_frontend/`는 `React + Vite` 기반 운영용 web UI다.
- `runtime/install_orangepi_rknn_web_service.sh`는 OrangePI에서 같은 페이지 주소로 web console을 올리는 canonical service 설치 entry다.
- web console은 `모델 전환`, `실시간 FPS`, `갤러리 등록`, `촬영 저장`, `다중 이미지 업로드`, `삭제`, `상태 표시`를 지원한다.

## 현재 주경로

1. host에서 `InsightFace -> RKNN` 변환을 수행한다.
2. canonical `pack.json`과 `.rknn` 산출물을 `conversion/results/model_zoo/`에 정리한다.
3. OrangePI에서 `RKNN Lite2` 환경을 준비한다.
4. `runtime.FaceSDK`로 detection, feature extraction, gallery 비교를 묶어 쓴다.
5. `runtime/web_backend/main.py`와 `runtime/web_frontend/dist/`를 같은 service로 올린다.
6. web console에서 모델을 바꾸고 갤러리를 관리하며 실기기 상태를 확인한다.

## 저장소 구조

- `docs/`
  - 프로젝트 운영 문서와 프로젝트 레벨 logbook
- `conversion/`
  - 모델 변환, metadata, `RKNN model zoo`
- `runtime/`
  - SDK, OrangePI 실기기 실행, web backend, web frontend, service
- `assets/`
  - 프로젝트 전역 공용 자산

## 모듈 역할

### `conversion/`

- 원본 `InsightFace` pack 인벤토리
- host 변환 환경
- `ONNX -> RKNN` export entry
- `pack.json` manifest와 alias 관리
- 다른 사람이 그대로 따라 할 수 있는 변환 절차 문서

### `runtime/`

- `RKNN face SDK` 표면
- gallery 로드와 임베딩 비교
- OrangePI 실기기 카메라 입력
- `FastAPI` backend
- `React` frontend
- `systemd` service
- 실시간 FPS, 메모리, 최근 결과 표시

## 새 기능을 어디에 둘까

- 원본 모델, 변환, 양자화, `RKNN` 산출물은 `conversion/`에 둔다.
- SDK, 카메라 입력, 실시간 루프, web API, web UI, service는 `runtime/`에 둔다.
- 프로젝트 전역 설명과 고정 방향은 `README.md`에 둔다.
- 현재 상태, 시행착오, 활성 체크리스트는 `docs/logbook.md`에 둔다.
- 운영 규칙은 `docs/AGENT.md`에 둔다.

## 따라 하기 문서

- host 변환 절차: [conversion/README.md](conversion/README.md)
- OrangePI 실행 절차: [runtime/README.md](runtime/README.md)
- 현재 살아 있는 truth: [docs/logbook.md](docs/logbook.md)

## 실행 산출물 기준

- `conversion/results/model_zoo/<platform>/<pack>/pack.json`은 runtime이 직접 읽는 canonical manifest다.
- `runtime/results/`에는 benchmark와 운영 smoke 결과만 둔다.
- `runtime/gallery/`는 tracked sample 대신 local gallery 저장소로 쓴다.
- gallery 저장 구조는 `runtime/gallery/<person_id>/meta.json`, `runtime/gallery/<person_id>/images/*`를 기본으로 한다.
- smoke, debug, failed run 산출물은 문서화가 끝나면 삭제 가능한 임시 자산으로 본다.

## 공용 고정 메모

- wrapper가 주 제품이고 web console은 운영 인터페이스다.
- 현재 기본 runtime pack은 `buffalo_m`이다.
- `buffalo_s`는 `buffalo_sc` alias pack으로 유지한다.
- 모델 전환은 web backend에서 메모리 정리와 예외 처리를 포함해 수행한다.
- 최종 web console은 이미지 위에 직접 글자를 그리지 않고, 웹 UI 레이어에서 상태를 표시한다.
- CPU 경로는 benchmark와 비교 검증용으로만 유지하고, 실시간 주경로는 `RKNN`으로 본다.
- 현재 개발 보드 `OrangePI RK3588`의 고정 LAN 주소는 `eth0 = 192.168.20.238/24`, gateway `192.168.20.4`, DNS `168.126.63.1`다.
- 현재 주 카메라 경로는 `/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0`다.
