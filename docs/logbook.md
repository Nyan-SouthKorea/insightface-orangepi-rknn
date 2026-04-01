# logbook

## 읽기 규칙

- 비사소한 작업에서는 항상 `docs/AGENT.md`를 먼저 읽는다.
- 그다음 `README.md`를 읽고 프로젝트 전역 구조와 고정 메모를 맞춘다.
- 그다음 이 문서를 읽고 현재 스냅샷, 전역 결정, 활성 체크리스트, 최근 로그를 확인한다.
- 아직 archive 문서는 없다. archive가 생기면 최신 `docs/logbook_archive/logbook_*.md` 1개를 함께 읽는다.
- 모듈 작업 전에는 관련 모듈 `README.md`와 해당 모듈 `docs/logbook.md`를 함께 읽는다.

## 현재 프로젝트 스냅샷

- 현재 단계는 reference 아키텍처 분석과 실행 경로 판단 단계다.
- 프로젝트 목표는 `InsightFace -> ONNX -> RKNN -> OrangePI RK3588 실시간 추론` 주경로를 안정적으로 만드는 것이다.
- 현재 canonical 모듈은 `conversion/`과 `runtime/` 두 개다.
- 현재 reference 소스는 `/tmp/jetson-face-speaker-recognition`에 임시 clone해 둔 상태다.
- 아직 확정되지 않은 항목은 첫 번째 타깃 모델 조합, 호스트 환경 버전, 실기기 측정 기준값, ONNX 검증용 venv 이름이다.
- 아직 없는 항목은 변환 스크립트, 실기기 실행 스크립트, 인벤토리 스크립트, logbook archive 스크립트다.

## 현재 전역 결정

- 운영 규칙은 `docs/AGENT.md`에 유지한다.
- 프로젝트 전역 설명과 안정된 구조는 `README.md`에 유지한다.
- 현재 truth와 최근 로그는 이 문서에 유지한다.
- 모듈 경계는 우선 `conversion/`과 `runtime/`만 둔다.
- 실제 대용량 산출물은 모듈 내부 `results/` 아래에 둔다.
- 장시간 변환과 실기기 benchmark는 smoke를 먼저 통과시킨다.
- `OrangePI` SSH 접속 정보 같은 비공개 장치 자격 정보는 `../secrets/README.local.md`에 유지한다.
- 로컬 git 저장소는 초기화되어 있다.
- reference 저장소 `jetson-face-speaker-recognition`에서 가져올 핵심 구조는 `얼굴 갤러리 로드 -> 실시간 입력 -> 얼굴 임베딩 비교 -> 이름 표시` 흐름이다.
- reference 저장소의 화자 인식 경로는 이번 프로젝트 범위에서 제외한다.
- 공식 ONNX Runtime 문서 기준 Python CPU 패키지는 Linux ARM64를 지원한다.
- 공식 ONNX Runtime 문서 기준 Rockchip RKNPU 실행 제공자는 preview이며 지원 플랫폼이 `RK1808 Linux`로 한정되어 있다.
- 공식 Rockchip `rknn-toolkit2`와 `rknpu2` 문서 기준 RK3588 NPU 사용 경로는 `ONNX 등 원본 모델 -> RKNN 변환 -> RKNN Runtime/Lite2 추론`이다.
- 따라서 `OrangePI RK3588`에서 `별도 RKNN 변환 없이 ONNX Runtime만으로 Rockchip NPU 가속`을 쓰는 경로는 현재 기준으로 공식 지원 경로로 보지 않는다.
- 필요하면 ONNX Runtime은 CPU 검증 경로로만 별도 유지하고, 실시간 목표 경로는 RKNN 변환을 기본으로 잡는다.
- 아직 `tools/directory_inventory.py`가 없으므로, 초기 부트스트랩 단계에서는 `find`와 `rg --files` 기반의 shallow inventory로 대신하고 그 사실을 logbook에 남긴다.
- 아직 `tools/logbook_archive_guard.py`가 없으므로, 초기 단계에서는 줄 수를 수동으로 확인한다.

## 현재 활성 체크리스트

- 이번 실행의 목표
  - reference 저장소에서 `face-only`로 가져올 수 있는 최소 아키텍처를 분리한다.
  - `OrangePI RK3588`에서 `ONNX Runtime`을 검증용으로 유지할지, `RKNN`만 주경로로 둘지 판단한다.
- 이번 실행의 비범위
  - 실제 모델 변환 코드 작성
  - 실기기 배포 스크립트 작성
  - benchmark 수치 확정
  - reference 저장소 전체 이식
- 수정 대상 파일과 역할
  - `docs/logbook.md`: 현재 스냅샷, 전역 결정, 활성 체크리스트, 최근 로그
- 생성되거나 갱신되는 산출물 경로
  - 없음
- 다음 단계 연결
  - `conversion/`은 첫 번째 `InsightFace -> ONNX -> RKNN` 변환 smoke 경로 정의로 이어진다.
  - `runtime/`은 `gallery face recognition` runtime 설계와 ONNX CPU 검증 경로 정의로 이어진다.
- 검증 방법과 완료 조건
  - reference 저장소에서 face 경로와 speaker 경로가 어디서 갈리는지 확인한다.
  - RK3588에서 ONNX Runtime CPU 가능 여부와 Rockchip NPU 직결 가능 여부를 공식 자료로 구분한다.
  - 다음 구현 단계가 `face-only runtime`과 `RKNN 주경로`로 자연스럽게 이어지게 정리한다.
- 체크리스트
  - [x] reference 저장소 clone과 구조 확인
  - [x] face 경로와 speaker 경로 분기 지점 확인
  - [x] RK3588 ONNX Runtime 공식 지원 범위 확인
  - [ ] `face-only runtime` 초안 구조를 현재 repo에 반영
  - [ ] ONNX 검증용 venv 이름 확정과 생성
  - [ ] 첫 번째 타깃 `InsightFace` 모델 조합 확정
  - [ ] 호스트 환경과 `OrangePI RK3588` 실기기 환경 표 작성
  - [ ] 변환 smoke 명령과 full 명령 초안 작성
  - [ ] 실기기 benchmark smoke 명령과 full 명령 초안 작성
  - [ ] 인벤토리 스크립트와 archive guard 스크립트 필요 여부 판단
  - [x] git 저장소 초기화 여부 결정

## Recent Logs

- 2026-04-01: `AGENT.md`만 있던 빈 저장소 상태를 확인했다.
- 2026-04-01: 프로젝트의 첫 번째 canonical 문서로 `README.md`, `docs/logbook.md`, 모듈 `README.md`, 모듈 `docs/logbook.md` 초안을 만들기로 결정했다.
- 2026-04-01: 초기 모듈 경계를 `conversion/`과 `runtime/`으로 고정했다.
- 2026-04-01: 도구 스크립트와 git 저장소가 아직 없으므로, 부트스트랩 예외를 `AGENT.md`와 logbook에 반영하기로 결정했다.
- 2026-04-01: `docs/AGENT.md`의 예시를 변환, 양자화 검증, 실기기 benchmark 중심으로 보정했다.
- 2026-04-01: `wc -l` 확인 결과 active logbook들은 archive 기준인 1000줄에 한참 못 미치므로 archive는 만들지 않았다.
- 2026-04-01: `git -C repo rev-parse --is-inside-work-tree` 확인 결과 아직 git 저장소가 초기화되지 않은 상태임을 다시 확인했다.
- 2026-04-01: `../secrets/README.local.md`를 만들고 `OrangePI` SSH 접속 메모를 로컬 전용으로 기록했다.
- 2026-04-01: `ssh orangepi@192.168.20.238 'hostname; whoami; uname -m'` smoke 결과 `orangepicm5`, `orangepi`, `aarch64`를 확인했다.
- 2026-04-01: `assets/prompts`는 이전 LLM 작업 흔적으로 판단해 삭제 대상으로 정리하고, 이를 유도한 `AGENT` 문장도 함께 제거했다.
- 2026-04-01: 로컬 git 저장소 초기화와 첫 push smoke는 완료 상태로 current truth를 갱신했다.
- 2026-04-01: reference 저장소 `jetson-face-speaker-recognition`를 `/tmp/jetson-face-speaker-recognition`에 clone해 구조를 확인했다.
- 2026-04-01: reference 저장소의 핵심 재사용 후보는 `module/face_recognition.py`, `module/image_capture.py`, `01_demo_face-recognition.py`로 판단했다.
- 2026-04-01: reference 저장소의 `main.py`는 `FaceRecognizer + SpeakerRecognizer` 융합 구조이고, 이번 프로젝트에서는 speaker 경로 전체를 제거 대상으로 판단했다.
- 2026-04-01: 공식 ONNX Runtime 문서 기준 Python CPU 패키지는 Linux ARM64를 지원하지만, 공식 Rockchip RKNPU 실행 제공자는 `RK1808 Linux`만 지원한다는 점을 확인했다.
- 2026-04-01: 공식 Rockchip 문서 기준 RK3588 NPU 경로는 RKNN 변환 뒤 `RKNN Runtime/Lite2`를 사용하는 흐름이므로, `ONNX Runtime만으로 RK3588 NPU 가속`은 현재 기준으로 주경로로 채택하지 않기로 잠정 판단했다.
