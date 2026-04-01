# InsightFace-RKNN

## 프로젝트 개요

- 이 프로젝트는 `InsightFace` 계열 얼굴 관련 모델을 `RKNN`으로 변환하고, `OrangePI RK3588`에서 실시간으로 실행하는 것을 목표로 한다.
- 최종 산출물은 `여러 InsightFace model zoo를 RKNN으로 정리한 wrapper`와 `별도 web demo` 두 축으로 나눈다.
- 즉 앱 코드에서는 SDK처럼 import하는 wrapper를 쓰고, web demo는 시연과 운영 확인 전용 entry로 분리한다.
- 운영 규칙은 `docs/AGENT.md`가 맡는다.
- 현재 상태, 전역 결정, 활성 체크리스트, 최근 로그는 `docs/logbook.md`가 맡는다.
- 모듈별 상세 기준은 각 모듈 `README.md`가 맡는다.

## 최종 산출물 형태

- `conversion/`은 `InsightFace -> ONNX -> RKNN` 변환 경로와 여러 모델팩 산출물을 정리한다.
- `runtime/face_wrapper.py`는 앱 코드가 import해서 쓰는 얇은 표면이 아니라, 최종적으로 `RKNN face SDK`의 공용 import 표면으로 승격한다.
- `runtime/face_gallery_web_demo.py`는 현재 1차 CPU 검증용 demo이고, 이후에는 `front / back`이 분리된 새 web demo로 교체한다.
- 새 web demo는 모델 전환, 실시간 상태 표시, gallery 등록과 삭제, 사용자 촬영과 다중 이미지 관리까지 포함한 운영 인터페이스를 목표로 한다.
- 현재 첫 `RKNN wrapper` 성공 경로는 `FaceWrapper(backend="rknn", model_pack="buffalo_sc")` 기준으로 닫았다.
- 따라서 개발 중에도 `wrapper를 제품`, `web demo를 검증 도구이자 운영 인터페이스`로 보고 분리 상태를 유지한다.

## 현재 주경로

1. 원본 `InsightFace` 모델과 입력 형식을 정리한다.
2. `OrangePI RK3588` CPU 경로에서 buffalo model pack별 속도를 먼저 측정한다.
3. 호스트 환경에서 `ONNX` 또는 중간 표현으로 변환한다.
4. 작은 실제 입력 묶음으로 smoke 변환과 양자화 검증을 통과시킨다.
5. `RKNN` 산출물을 만든다.
6. `OrangePI RK3588`에 배치한다.
7. 실기기에서 단건 추론, 반복 추론, 카메라 입력, 지연 시간과 초당 처리 수를 확인한다.
8. 첫 번째 성공 경로를 정확히 문서화한다.
9. 나머지 `InsightFace` 모델팩을 같은 방식으로 `RKNN`으로 확장한다.
10. `RKNN face SDK`와 분리형 web demo를 완성한다.

## 저장소 구조

- `docs/`
  - 프로젝트 운영 문서와 프로젝트 레벨 logbook
- `conversion/`
  - 모델 변환, 입력 출력 일치 확인, 양자화, `RKNN` 산출물 관리
- `runtime/`
  - `OrangePI RK3588` 실기기 실행, wrapper, 카메라 입력, 성능 측정, 배포용 진입점
- `assets/`
  - 프로젝트 전역 공용 자산과 문서 자산

## 모듈 역할

### `conversion/`

- 원본 모델 인벤토리
- `ONNX` 변환 경로
- 전처리와 후처리 기준 정리
- calibration 입력 묶음 관리
- `RKNN` 변환과 양자화 검증
- 변환 산출물 metadata 정리

### `runtime/`

- `OrangePI RK3588` 실기기 실행 경로
- import해서 쓰는 wrapper 표면
- 카메라 또는 파일 입력 진입점
- 실시간 추론 루프
- 지연 시간, 초당 처리 수, 장치 사용량 측정
- 배포 직전 smoke와 full benchmark

## 새 기능을 어디에 둘까

- 모델을 내보내거나, 입력 출력 형식을 맞추거나, 양자화와 변환을 다루면 `conversion/`에 둔다.
- 기기에서 돌리는 코드, 카메라 입력, 실시간 루프, 성능 측정, wrapper 표면, web demo는 `runtime/`에 둔다.
- 프로젝트 전역 설명, 전역 구조 메모, 처음 읽는 안내는 `README.md`에 둔다.
- 현재 상태, 전역 결정, 진행 체크리스트, 시행착오는 `docs/logbook.md`에 둔다.
- 반복해서 지켜야 하는 운영 규칙은 `docs/AGENT.md`에 둔다.
- 특정 모듈 하나에만 해당하는 안정된 설명은 해당 모듈 `README.md`에 둔다.

## 실행 산출물 기준

- 실제 실행 산출물은 root가 아니라 각 모듈 `results/` 아래에 둔다.
- `conversion/results/`에는 `ONNX`, `RKNN`, 변환 metadata, 비교 요약을 둔다.
- `runtime/results/`에는 benchmark 요약, 실기기 로그, 성능 측정 결과를 둔다.
- smoke, debug, failed run 산출물은 문서화가 끝나면 삭제 가능한 임시 자산으로 본다.

## 공용 고정 메모

- 장시간 변환, 양자화 검증, 실기기 benchmark는 smoke를 먼저 통과시킨 뒤 full run으로 넘어간다.
- 새 실행 파일은 상단 주석이나 docstring에 smoke 명령, full 명령, 주요 인자, 입력 경로, 출력 경로를 남긴다.
- 이 프로젝트의 첫 번째 모듈 경계는 `conversion`과 `runtime` 두 개를 기준으로 유지한다.
- wrapper가 주 제품이고 web demo는 검증과 운영 인터페이스라는 구조를 유지한다.
- CPU 경로에서는 `buffalo_sc`, `buffalo_s`, `buffalo_m`, `buffalo_l` 네 pack의 detection, feature extraction, pipeline 시간을 먼저 기록한다.
- 1차 RKNN 타깃은 `buffalo_sc`로 두고, `det_500m`과 `w600k_mbf`를 먼저 성공시킨다.
- 최종 web demo는 `front / back`을 분리하고, 이미지 위에 직접 글자를 그리는 방식 대신 웹 UI로 상태를 표시한다.
- 최종 web demo는 모델 전환, gallery 등록, 다중 이미지 추가, 삭제, 촬영 저장까지 지원해야 한다.
- 현재 개발 보드 `OrangePI RK3588`의 고정 LAN 주소는 `eth0 = 192.168.20.238/24`, gateway `192.168.20.4`, DNS `168.126.63.1`다.
- 현재 OrangePI service 설치 스크립트는 USB 카메라를 `camera-source`로 자동 선택하며, 현재 보드 기준 주 카메라 경로는 `/dev/v4l/by-id/usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-video-index0`다.
- 더 자세한 현재 작업 상태는 `docs/logbook.md`를 먼저 읽는다.
