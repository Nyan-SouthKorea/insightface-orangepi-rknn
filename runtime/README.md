# runtime

## 역할

- 이 모듈은 `OrangePI RK3588`에서 `RKNN` 모델을 실시간으로 실행하는 경로를 맡는다.
- 목표는 파일 입력 smoke와 카메라 입력 실시간 경로를 같은 기준 안에서 관리하는 것이다.

## 이 모듈이 맡는 것

- 실기기 실행 진입점
- 이미지, 비디오, 카메라 입력 연결
- 전처리와 후처리의 실기기 적용
- 단건 추론 smoke
- 반복 추론과 실시간 루프
- 지연 시간, 초당 처리 수, 장치 사용량 측정
- 배포 전 benchmark 정리

## 이 모듈이 맡지 않는 것

- 원본 모델 선택과 변환 로직
- `ONNX` 생성과 `RKNN` 빌드
- calibration 입력 묶음 관리

## 기준 입력

- `conversion/`에서 넘어온 `RKNN` 산출물
- 모델별 입력 크기와 정규화 metadata
- 시험용 이미지 또는 비디오
- 실기기 카메라 입력

## 기준 산출물

- smoke 실행 로그
- 지연 시간과 초당 처리 수 요약
- 실기기 benchmark 결과
- 배포 전 점검 메모

## 기본 작업 흐름

1. `conversion/`에서 승격된 산출물을 받는다.
2. 파일 입력 기반 smoke 추론을 먼저 통과시킨다.
3. 반복 실행과 장치 안정성을 확인한다.
4. 카메라 입력 실시간 경로를 붙인다.
5. benchmark를 수행하고 기준 미달 구간을 기록한다.
6. 기준을 통과한 경로를 canonical runtime으로 승격한다.

## 새 파일을 둘 위치

- 실기기 entry script와 helper는 `runtime/` 아래에 둔다.
- 모듈 현재 상태와 실행 체크리스트는 `runtime/docs/logbook.md`에 둔다.
- 환경 문서와 외부 공유용 요약 문서는 필요할 때만 `runtime/docs/` 아래 날짜 prefix 문서로 둔다.
- 실제 실행 산출물은 `runtime/results/` 아래에 둔다.

## 현재 고정 결정

- 실기기 smoke는 카메라 입력보다 파일 입력 경로를 먼저 닫는다.
- benchmark는 최소 `지연 시간`과 `초당 처리 수`를 함께 기록한다.
- 모델 변환 경계는 `conversion/`이 맡고, 이 모듈은 받은 산출물의 실행 안정성과 실시간성을 확인하는 데 집중한다.

## 관련 문서

- [root README](../README.md)
- [project logbook](../docs/logbook.md)
- [module logbook](docs/logbook.md)
