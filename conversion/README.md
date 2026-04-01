# conversion

## 역할

- 이 모듈은 `InsightFace` 계열 입력 모델을 `RKNN` 산출물로 변환하는 경로를 맡는다.
- 목표는 `OrangePI RK3588`에서 바로 시험할 수 있는 작은 smoke 경로와 반복 가능한 full 변환 경로를 만드는 것이다.
- 현재는 `buffalo_sc`, `buffalo_m`, `buffalo_l`의 face-only 핵심 모델을 `FP16 RKNN`으로 정리했고, `buffalo_s`는 alias pack manifest로 연결했다.

## 이 모듈이 맡는 것

- 원본 모델 파일과 버전 인벤토리
- `ONNX` 또는 중간 표현 변환
- 전처리와 후처리의 입력 출력 약속 정리
- calibration 입력 묶음 준비
- `RKNN` 변환과 양자화 옵션 정리
- 원본 모델, 중간 표현, `RKNN` 산출물 간의 기본 일치 확인
- 변환 결과 metadata와 간단한 비교 요약 정리

## 이 모듈이 맡지 않는 것

- `OrangePI RK3588` 실기기에서 돌아가는 카메라 입력 루프
- 실시간 화면 표시와 사용자 상호작용
- 실기기 장기 benchmark 자동화

## 기준 입력

- 원본 `InsightFace` 모델 가중치
- 변환 확인용 얼굴 이미지 또는 얼굴 crop 묶음
- calibration에 쓰는 작은 실제 입력 묶음
- 모델별 입력 크기와 정규화 기준

## 기준 산출물

- `ONNX` 파일 또는 중간 표현 산출물
- `RKNN` 파일
- 입력 출력 shape와 정규화 metadata
- 양자화 옵션 메모
- 비교 요약과 smoke 검증 결과

## 기본 작업 흐름

1. 원본 모델과 입력 형식을 확인한다.
2. 가장 작은 실제 입력 묶음으로 smoke 변환 계획을 세운다.
3. `det_500m`, `w600k_mbf`처럼 실제 파이프라인에 필요한 최소 모델만 먼저 분리한다.
4. `ONNX` 또는 중간 표현 변환을 수행한다.
5. 전처리와 후처리 기준이 유지되는지 확인한다.
6. `RKNN` 변환과 양자화를 수행한다.
7. host 기준 비교 또는 가능한 작은 device 확인으로 기본 동작을 점검한다.
8. 첫 번째 성공 경로를 문서화한 뒤 같은 방식으로 나머지 모델팩을 확장한다.
9. 기준을 통과한 산출물만 canonical 위치로 승격한다.

## 새 파일을 둘 위치

- 변환 entry script와 helper는 `conversion/` 아래에 둔다.
- 모듈 현재 상태와 실행 체크리스트는 `conversion/docs/logbook.md`에 둔다.
- 환경 문서와 외부 공유용 요약 문서는 필요할 때만 `conversion/docs/` 아래 날짜 prefix 문서로 둔다.
- 실제 실행 산출물은 `conversion/results/` 아래에 둔다.

## 현재 고정 결정

- 변환 경로는 한 번에 크게 벌리지 않고, 첫 번째 smoke 경로를 먼저 닫는다.
- 첫 번째 smoke 경로는 `buffalo_sc -> det_500m + w600k_mbf`다.
- host 변환 환경은 `../envs/ifr_rknn_host_cp310`로 고정하고, 현재 기준 `RKNN Toolkit2 2.3.2 + Python 3.10 + setuptools 75.8.0 + onnx 1.16.1` 조합을 유지한다.
- 실행 가능한 스크립트는 상단 주석이나 docstring에 smoke 명령과 full 명령을 남긴다.
- 실기기 경계는 `runtime/`이 맡고, 이 모듈은 변환 가능한 산출물을 안정적으로 넘겨주는 데 집중한다.
- `conversion/export_insightface_pack_rknn.py`를 pack-level canonical entry로 두고, nested pack 경로도 여기서 정규화한다.
- 성공한 산출물은 `pack.json`과 함께 정리해 `runtime`이 모델 전환 UI와 alias 해석에 읽게 만든다.

## 관련 문서

- [root README](../README.md)
- [project logbook](../docs/logbook.md)
- [module logbook](docs/logbook.md)
