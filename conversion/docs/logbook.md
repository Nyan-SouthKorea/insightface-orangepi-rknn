# conversion logbook

## 읽기 규칙

- 먼저 `../../docs/AGENT.md`를 읽는다.
- 그다음 `../README.md`를 읽고 이 모듈의 역할과 경계를 맞춘다.
- 그다음 `../../docs/logbook.md`를 읽고 프로젝트 전역 결정과 활성 체크리스트를 맞춘다.
- 아직 archive 문서는 없다. archive가 생기면 최신 `logbook_*.md` 1개를 함께 읽는다.

## 현재 모듈 스냅샷

- 현재 목적은 face-only `InsightFace -> RKNN` pack 경로를 반복 가능한 entry와 canonical model zoo로 정리하는 것이다.
- 현재 canonical `FP16 RKNN` face pack은 `buffalo_sc`, `buffalo_m`, `buffalo_l`이고, `buffalo_s`는 alias manifest로 연결했다.
- host 변환 환경은 `../envs/ifr_rknn_host_cp310`로 만들었고, `RKNN Toolkit2 2.3.2 cp310` import를 확인했다.
- 현재 기준 실제 동작에 필요한 host 고정 조합은 `Python 3.10`, `setuptools 75.8.0`, `onnx 1.16.1`이다.
- `conversion/export_insightface_rknn.py`, `conversion/setup_rknn_host_env.sh`, `conversion/requirements_rknn_host_cp310.txt`를 추가했다.
- host에서 `buffalo_sc det_500m`, `buffalo_sc w600k_mbf`의 `FP16 RKNN export`를 각각 성공했다.
- OrangePI로 두 `.rknn` 파일을 넘겨 `RKNN Lite2` smoke까지 실제 연결했다.
- host 기준 `buffalo_s`의 핵심 face ONNX 둘은 `buffalo_sc`와 동일 해시임을 확인했다.
- `buffalo_m` pack은 zip 내부가 `buffalo_m/buffalo_m/*.onnx` 중첩 구조라서 pack 경로 정규화가 필요하다.
- `conversion/export_insightface_pack_rknn.py`로 pack-level export와 `pack.json` manifest 생성까지 묶었다.
- canonical `RKNN model zoo`는 현재 tracked repo의 `conversion/results/model_zoo/rk3588/` 아래에 유지한다.
- `conversion/README.md`에는 다른 사람이 그대로 따라 할 수 있는 host 변환 순서와 OrangePI smoke 절차를 정리했다.
- 아직 정하지 않은 항목은 `INT8` calibration 입력 묶음, canonical model zoo metadata 형식, 나머지 모델팩 확장 순서다.

## 현재 모듈 결정

- 이 모듈은 변환과 입력 출력 일치 확인까지 맡는다.
- 실기기 실시간 루프와 카메라 입력은 `runtime/`이 맡는다.
- 큰 산출물은 `conversion/results/` 아래에 둔다.
- 첫 번째 성공 경로를 문서화한 뒤 같은 스크립트 구조로 나머지 모델팩을 확장한다.
- host 변환은 `setup_rknn_host_env.sh`와 `export_insightface_rknn.py` 두 entry를 기준 경로로 유지한다.
- host pack 변환은 `export_insightface_pack_rknn.py`를 기준 entry로 유지하고, `export_insightface_rknn.py`는 하위 단일 모델 export로 둔다.
- detection 기본 정규화는 `mean 127.5 / std 128.0`, recognition 기본 정규화는 `mean 127.5 / std 127.5`로 현재 고정한다.
- face-only 기준 실제 distinct pack은 `buffalo_sc`, `buffalo_m`, `buffalo_l` 세 개로 본다.
- 변환 순서는 `buffalo_m -> buffalo_l`로 두고, `buffalo_s`는 우선 alias metadata로 정리한다.
- 각 pack 폴더의 `pack.json`은 runtime이 pack 선택과 alias 해석에 읽는 canonical manifest다.

## 현재 활성 체크리스트

- [x] 첫 번째 타깃 모델 조합 확정
- [x] RKNN Toolkit2 공식 경로와 host 환경 제약 확인
- [x] `det_500m` 입력 크기와 정규화 기준 표 작성
- [x] `w600k_mbf` 입력 크기와 정규화 기준 표 작성
- [x] `buffalo_sc det_500m` smoke 변환 명령 작성
- [x] `buffalo_sc w600k_mbf` smoke 변환 명령 작성
- [x] canonical 산출물 폴더 이름 규칙 초안 작성
- [x] `runtime/`으로 넘길 최소 metadata 정의
- [x] 첫 번째 RKNN 성공 경로 문서화
- [x] 나머지 모델팩 확장 순서 확정
- [x] nested pack 경로를 허용하는 pack-level export entry 추가
- [x] `buffalo_m` detector / recognizer RKNN export
- [x] `buffalo_m` OrangePI Lite2 smoke
- [x] `buffalo_l` detector / recognizer RKNN export
- [x] `buffalo_l` OrangePI Lite2 smoke
- [x] OrangePI `RKNN Lite2` smoke 성공
- [ ] `INT8` calibration 경로 초안 작성

## 현재 성공 경로

- host 변환 환경 생성
  - `bash conversion/setup_rknn_host_env.sh`
- pack 변환
  - `source ../envs/ifr_rknn_host_cp310/bin/activate`
  - `python conversion/export_insightface_pack_rknn.py --model-packs buffalo_sc,buffalo_m,buffalo_l,buffalo_s --target-platform rk3588 --dtype fp --skip-existing`
- current canonical 산출물
  - `conversion/results/model_zoo/rk3588/buffalo_sc/*`
  - `conversion/results/model_zoo/rk3588/buffalo_s/pack.json`
  - `conversion/results/model_zoo/rk3588/buffalo_m/*`
  - `conversion/results/model_zoo/rk3588/buffalo_l/*`

## Recent Logs

- 2026-04-01: 모듈 문서 초안을 만들고 역할을 `변환 전용`으로 고정했다.
- 2026-04-01: 에이전트 모드 전환 뒤 첫 번째 RKNN 타깃을 `buffalo_sc`의 `det_500m`, `w600k_mbf`로 고정했다.
- 2026-04-01: host에 `../envs/ifr_rknn_host_cp310`을 만들고 `RKNN Toolkit2 2.3.2 cp310` import를 확인했다.
- 2026-04-01: `setuptools 82.x`에서는 `pkg_resources` 문제로 import가 깨졌고, `setuptools 75.8.0`으로 고정해 해결했다.
- 2026-04-01: `onnx 1.21.x`에서는 `onnx.mapping` 오류로 `load_onnx`가 실패했고, `onnx 1.16.1`로 고정해 해결했다.
- 2026-04-01: `det_500m.onnx`와 `w600k_mbf.onnx`의 입력 이름은 둘 다 `input.1`로 확인했고, 동적 입력 ONNX는 첫 입력 이름을 자동으로 잡도록 export script를 보강했다.
- 2026-04-01: `export_insightface_rknn.py`로 `buffalo_sc det_500m`과 `buffalo_sc w600k_mbf`의 `FP16 RKNN` export를 host에서 성공했고, metadata json도 함께 남기도록 했다.
- 2026-04-01: host 산출물을 OrangePI `conversion/results/model_zoo/rk3588/buffalo_sc/`로 복사해 device smoke 입력 경로까지 닫았다.
- 2026-04-01: `buffalo_s det_500m`, `w600k_mbf`의 SHA256이 `buffalo_sc`와 동일함을 확인했고, current face-only 범위에서는 별도 변환보다 alias pack으로 정리하기로 했다.
- 2026-04-01: `buffalo_m` 다운로드 결과 zip 내부가 `buffalo_m/buffalo_m/*.onnx` 중첩 구조임을 확인했고, pack-level export는 nested model dir 탐색을 지원하도록 보강하기로 했다.
- 2026-04-01: `export_insightface_pack_rknn.py`를 추가해 `buffalo_sc`, `buffalo_m`, `buffalo_l`의 pack-level export와 `buffalo_s` alias manifest 생성을 같은 entry로 묶었다.
- 2026-04-01: canonical `RKNN model zoo`를 tracked repo 아래에 두도록 `conversion/results/.gitignore`를 조정했고, host push 뒤 OrangePI pull 흐름으로 pack 배치를 닫았다.
- 2026-04-01: host에서 `buffalo_m`, `buffalo_l`의 `FP16 RKNN` export를 성공했고, OrangePI wrapper smoke까지 연결해 pack-level 변환 경로를 닫았다.
- 2026-04-01: `conversion/README.md`를 host 환경 준비, pack export, OrangePI probe, SDK smoke까지 따라 할 수 있는 매뉴얼 형태로 다시 정리했다.
