# logbook

## 읽기 규칙

- 비사소한 작업에서는 항상 `docs/AGENT.md`를 먼저 읽는다.
- 그다음 `README.md`를 읽고 프로젝트 전역 구조와 고정 메모를 맞춘다.
- 그다음 이 문서를 읽고 현재 스냅샷, 전역 결정, 활성 체크리스트, 최근 로그를 확인한다.
- 아직 archive 문서는 없다. archive가 생기면 최신 `docs/logbook_archive/logbook_*.md` 1개를 함께 읽는다.
- 모듈 작업 전에는 관련 모듈 `README.md`와 해당 모듈 `docs/logbook.md`를 함께 읽는다.

## 현재 프로젝트 스냅샷

- 현재 단계는 문서 부트스트랩이다.
- 프로젝트 목표는 `InsightFace -> ONNX -> RKNN -> OrangePI RK3588 실시간 추론` 주경로를 안정적으로 만드는 것이다.
- 현재 canonical 모듈은 `conversion/`과 `runtime/` 두 개다.
- 아직 확정되지 않은 항목은 첫 번째 타깃 모델 조합, 호스트 환경 버전, 실기기 측정 기준값이다.
- 아직 없는 항목은 변환 스크립트, 실기기 실행 스크립트, 인벤토리 스크립트, logbook archive 스크립트, git 동기화 스크립트다.

## 현재 전역 결정

- 운영 규칙은 `docs/AGENT.md`에 유지한다.
- 프로젝트 전역 설명과 안정된 구조는 `README.md`에 유지한다.
- 현재 truth와 최근 로그는 이 문서에 유지한다.
- 모듈 경계는 우선 `conversion/`과 `runtime/`만 둔다.
- 실제 대용량 산출물은 모듈 내부 `results/` 아래에 둔다.
- 장시간 변환과 실기기 benchmark는 smoke를 먼저 통과시킨다.
- `OrangePI` SSH 접속 정보 같은 비공개 장치 자격 정보는 `../secrets/README.local.md`에 유지한다.
- 아직 `tools/directory_inventory.py`가 없으므로, 초기 부트스트랩 단계에서는 `find`와 `rg --files` 기반의 shallow inventory로 대신하고 그 사실을 logbook에 남긴다.
- 아직 `tools/logbook_archive_guard.py`가 없으므로, 초기 단계에서는 줄 수를 수동으로 확인한다.
- 아직 git 저장소가 초기화되지 않았으므로, commit과 push 규칙은 저장소 초기화 뒤에 강제한다.

## 현재 활성 체크리스트

- 이번 실행의 목표
  - 프로젝트 운영 문서 초안을 이번 저장소 구조에 맞게 세운다.
  - `RK3588 + RKNN + 실시간 추론` 기준으로 모듈 경계를 고정한다.
- 이번 실행의 비범위
  - 실제 모델 변환 코드 작성
  - 실기기 배포 스크립트 작성
  - benchmark 수치 확정
- 수정 대상 파일과 역할
  - `README.md`: 프로젝트 전역 소개와 구조
  - `docs/logbook.md`: 현재 스냅샷, 전역 결정, 활성 체크리스트, 최근 로그
  - `conversion/README.md`: 모델 변환 모듈 기준
  - `conversion/docs/logbook.md`: 변환 모듈 현재 상태
  - `runtime/README.md`: 실기기 실행 모듈 기준
  - `runtime/docs/logbook.md`: 실기기 모듈 현재 상태
  - `docs/AGENT.md`: 운영 규칙 보정
- 생성되거나 갱신되는 산출물 경로
  - `conversion/results/`
  - `runtime/results/`
- 다음 단계 연결
  - `conversion/`은 첫 번째 변환 smoke 경로 정의로 이어진다.
  - `runtime/`은 첫 번째 실기기 smoke benchmark 경로 정의로 이어진다.
- 검증 방법과 완료 조건
  - 문서 역할이 서로 겹치지 않는지 확인한다.
  - root 문서와 모듈 문서가 서로 링크로 이어지는지 확인한다.
  - 이번 턴에서 만든 문서를 다시 읽어 무중복과 무누락을 점검한다.
- 체크리스트
  - [x] root canonical 문서 초안 정의
  - [x] 모듈 `README.md` 초안 정의
  - [x] 모듈 `docs/logbook.md` 초안 정의
  - [x] `docs/AGENT.md`를 `RKNN + OrangePI RK3588` 흐름에 맞게 보정
  - [x] 현재 logbook 줄 수 수동 확인
  - [ ] 첫 번째 타깃 `InsightFace` 모델 조합 확정
  - [ ] 호스트 환경과 `OrangePI RK3588` 실기기 환경 표 작성
  - [ ] 변환 smoke 명령과 full 명령 초안 작성
  - [ ] 실기기 benchmark smoke 명령과 full 명령 초안 작성
  - [ ] 인벤토리 스크립트와 archive guard 스크립트 필요 여부 판단
  - [ ] git 저장소 초기화 여부 결정

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
