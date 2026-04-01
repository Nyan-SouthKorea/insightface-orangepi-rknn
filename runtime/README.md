# runtime

## 역할

- 이 모듈은 `OrangePI RK3588`에서 얼굴 인식 런타임을 실기기 기준으로 정리한다.
- 현재 첫 구현 목표는 `face-only` 웹 데모와 `ONNX Runtime CPU` 검증 경로를 먼저 닫는 것이다.
- 이후 `RKNN` 주경로가 준비되면 같은 입력과 같은 gallery 규칙 위에 실행 backend만 교체한다.

## 이 모듈이 맡는 것

- 실기기 실행 진입점
- 이미지, 비디오, 카메라 입력 연결
- gallery 자동 로드와 임베딩 비교
- 전처리와 후처리의 실기기 적용
- 단건 추론 smoke
- 반복 추론과 실시간 루프
- 웹 스트리밍과 서비스 실행
- 지연 시간, 초당 처리 수, 장치 사용량 측정
- 배포 전 benchmark 정리

## 이 모듈이 맡지 않는 것

- 원본 모델 선택과 변환 로직
- `ONNX` 생성과 `RKNN` 빌드
- calibration 입력 묶음 관리

## 기준 입력

- 현재 단계에서는 `InsightFace` 기본 모델팩과 `ONNX Runtime CPU`
- 이후 `conversion/`에서 넘어온 `RKNN` 산출물
- 모델별 입력 크기와 정규화 metadata
- 시험용 이미지 또는 비디오
- 실기기 카메라 입력
- `runtime/gallery/` 아래 로컬 얼굴 이미지

## 기준 산출물

- smoke 실행 로그
- 지연 시간과 초당 처리 수 요약
- 실기기 benchmark 결과
- 배포 전 점검 메모
- `systemd` 서비스 파일

## 기본 작업 흐름

1. `runtime/gallery/` 규칙을 정하고 사용자 얼굴 이미지를 로컬로 준비한다.
2. `../envs/ifr_ort_cpu_probe` 환경에서 `ONNX Runtime CPU` 검증을 먼저 통과시킨다.
3. 웹캠 또는 JSON 입력으로 `face-only` 웹 데모를 띄운다.
4. `systemd` 서비스로 부팅 후 자동 실행 경로를 닫는다.
5. 그다음 `RKNN` backend를 붙여 실기기 지연 시간과 초당 처리 수를 다시 측정한다.
6. 기준을 통과한 경로를 canonical runtime으로 승격한다.

## 새 파일을 둘 위치

- 실기기 entry script와 helper는 `runtime/` 아래에 둔다.
- 모듈 현재 상태와 실행 체크리스트는 `runtime/docs/logbook.md`에 둔다.
- 환경 문서와 외부 공유용 요약 문서는 필요할 때만 `runtime/docs/` 아래 날짜 prefix 문서로 둔다.
- 실제 실행 산출물은 `runtime/results/` 아래에 둔다.
- 실제 사용자 얼굴 이미지 같은 로컬 자산은 `runtime/gallery/` 아래에 두되 git으로 추적하지 않는다.

## 현재 고정 결정

- 현재 웹 데모는 `face-only` 경로만 유지하고 speaker 경로는 넣지 않는다.
- 현재 첫 backend는 `ONNX Runtime CPUExecutionProvider`다.
- gallery 폴더 이름은 기본적으로 `한글이름, EnglishName` 형식을 권장한다.
- 현재 `OrangePI` 서비스 템플릿의 기본 카메라 번호는 실기기 probe 기준 `11`로 둔다.
- 실기기 smoke는 카메라 입력보다 파일 입력 경로를 먼저 닫되, 웹 데모는 동일 entry script에서 `webcam/json` 둘 다 받는다.
- benchmark는 최소 `지연 시간`과 `초당 처리 수`를 함께 기록한다.
- 모델 변환 경계는 `conversion/`이 맡고, 이 모듈은 받은 산출물의 실행 안정성과 실시간성을 확인하는 데 집중한다.

## 현재 entry script

- `runtime/face_gallery_web_demo.py`
  - `Flask` 기반 웹 스트리밍 데모
- `runtime/face_gallery_recognizer.py`
  - `InsightFace FaceAnalysis` 기반 gallery 인식 helper
- `runtime/image_capture.py`
  - 웹캠과 JSON 이미지 polling helper
- `runtime/setup_orangepi_ort_cpu_env.sh`
  - `../envs/ifr_ort_cpu_probe` 생성과 CPU provider 확인
- `runtime/install_orangepi_service.sh`
  - `insightface_gallery_web.service` 설치

## 관련 문서

- [root README](../README.md)
- [project logbook](../docs/logbook.md)
- [module logbook](docs/logbook.md)
