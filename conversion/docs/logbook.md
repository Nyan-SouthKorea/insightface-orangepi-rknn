# conversion logbook

## 읽기 규칙

- 먼저 `../../docs/AGENT.md`를 읽는다.
- 그다음 `../README.md`를 읽고 이 모듈의 역할과 경계를 맞춘다.
- 그다음 `../../docs/logbook.md`를 읽고 프로젝트 전역 결정과 활성 체크리스트를 맞춘다.
- 아직 archive 문서는 없다. archive가 생기면 최신 `logbook_*.md` 1개를 함께 읽는다.

## 현재 모듈 스냅샷

- 아직 실제 변환 스크립트는 없다.
- 현재 목적은 첫 번째 `InsightFace -> ONNX -> RKNN` smoke 경로를 정의하는 것이다.
- 아직 정하지 않은 항목은 타깃 모델 조합, calibration 입력 묶음, host 검증 방식이다.

## 현재 모듈 결정

- 이 모듈은 변환과 입력 출력 일치 확인까지 맡는다.
- 실기기 실시간 루프와 카메라 입력은 `runtime/`이 맡는다.
- 큰 산출물은 `conversion/results/` 아래에 둔다.

## 현재 활성 체크리스트

- [ ] 첫 번째 타깃 모델 조합 확정
- [ ] 입력 크기와 정규화 기준 표 작성
- [ ] smoke 변환 명령 초안 작성
- [ ] canonical 산출물 폴더 이름 규칙 초안 작성
- [ ] `runtime/`으로 넘길 최소 metadata 정의

## Recent Logs

- 2026-04-01: 모듈 문서 초안을 만들고 역할을 `변환 전용`으로 고정했다.
