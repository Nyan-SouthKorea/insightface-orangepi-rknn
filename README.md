# InsightFace OrangePi RKNN

> `InsightFace` model zoo를 `Rockchip RK3588`용 `RKNN` model zoo로 정리하고, 이를 `SDK + web console` 형태로 묶어 `OrangePI`에서 바로 쓰기 쉽게 만든 프로젝트다.

<p align="center">
  <img src="assets/readme/orangepi-5-ultra-overview.png" alt="Orange Pi 5 Ultra overview" width="74%" />
</p>

<p align="center">
  <img src="assets/readme/rk3588-family-badge.png" alt="Rockchip RK3588 family badge" width="180" />
</p>

## 한눈에 보기

- 최종 산출물은 두 축이다.
- 첫째는 앱 코드가 바로 import해서 쓰는 `RKNN FaceSDK`다.
- 둘째는 모델 전환, 갤러리 관리, 실시간 상태 확인을 맡는 `front / back` 분리형 web console이다.
- 실시간 주경로는 `InsightFace -> ONNX -> RKNN -> RKNN Lite2 -> OrangePI RK3588`다.
- CPU 경로는 benchmark와 비교 검증용이고, 제품 경로는 `RKNN`이다.
- 현재 canonical pack은 `buffalo_sc`, `buffalo_s(alias)`, `buffalo_m`, `buffalo_l`, 비교용 `buffalo_m_i8`다.
- 현재 안정된 기본 runtime pack은 `buffalo_m`으로 둔다.

## Demo

아래 GIF는 `repo/사용자 추가 폴더`에 놓인 demo 영상 4개와 이미지 2개를 기준으로 다시 정리한 README 자산이다.  
프레임 샘플과 현재 gallery metadata를 함께 확인한 결과, 데모 인물은 모두 `라이언 / Ryan`으로 정리했다.  
생성 스크립트와 분석 근거는 [assets/readme/build_demo_assets.py](assets/readme/build_demo_assets.py), [assets/readme/demo_assets.json](assets/readme/demo_assets.json)에 남긴다.

| Live Recognition | Model Switching |
| --- | --- |
| <img src="assets/readme/demo_live-recognition_ryan.gif" alt="Live recognition demo" width="100%" /> | <img src="assets/readme/demo_model-switching_ryan.gif" alt="Model switching demo" width="100%" /> |
| `라이언 / Ryan`을 실시간으로 인식하는 화면 | `buffalo_l`, `buffalo_m_i8`, `buffalo_sc`를 바꿔 가며 같은 인물을 유지 |

| Gallery Registration | NPU Monitoring |
| --- | --- |
| <img src="assets/readme/demo_gallery-registration_ryan.gif" alt="Gallery registration demo" width="100%" /> | <img src="assets/readme/demo_npu-monitoring_ryan.gif" alt="NPU monitoring demo" width="100%" /> |
| 갤러리에 새 인물을 등록하고 즉시 인식에 반영 | `rknpu/load`와 web console을 같이 보며 NPU load 확인 |

## 이 저장소가 제공하는 것

- `conversion/`
  - InsightFace pack을 `RKNN`으로 변환하는 host-side toolchain
  - `pack.json` 기반 canonical model zoo
  - `INT8 calibration` 준비와 변환 매뉴얼
- `runtime/`
  - `FaceSDK`, `FaceWrapper` 기반 import-friendly SDK
  - gallery 로딩, 임베딩 비교, alias pack 해석
  - `FastAPI` backend + `React` frontend web console
  - OrangePI `systemd` service 설치 스크립트
- `assets/readme/`
  - root README가 직접 참조하는 데모 GIF와 하드웨어 이미지

## SDK 형태

이 프로젝트의 주 제품은 web demo 자체가 아니라, 앱 코드에서 바로 가져다 쓸 수 있는 `FaceSDK`다.

```python
from runtime import FaceSDK

sdk = FaceSDK(
    gallery_dir="runtime/gallery",
    model_pack="buffalo_m",
    backend="rknn",
)

result = sdk.infer(frame)
print(result)
sdk.close()
```

web console은 이 SDK를 감싼 운영 인터페이스다.  
즉 `FaceSDK`는 재사용 가능한 제품 표면이고, web console은 모델 관리와 현장 검증을 위한 유지보수형 entry다.

## Benchmark

### CPU baseline

- 실행 위치: `OrangePI RK3588`
- 실행 환경: `onnxruntime 1.23.2`, `CPUExecutionProvider`
- 입력: `runtime/results/face_benchmark_input.jpg`
- 해석: CPU 경로는 비교 기준선이다. 제품 실시간 경로로 보지 않는다.

| model pack | detection model | recognition model | detection avg ms | recognition avg ms | pipeline avg ms | pipeline FPS |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `buffalo_sc` | `det_500m.onnx` | `w600k_mbf.onnx` | 49.21 | 23.09 | 139.57 | 7.16 |
| `buffalo_s` | `det_500m.onnx` | `w600k_mbf.onnx` | 50.60 | 27.01 | 160.37 | 6.24 |
| `buffalo_m` | `det_2.5g.onnx` | `w600k_r50.onnx` | 152.80 | 318.90 | 635.75 | 1.57 |
| `buffalo_l` | `det_10g.onnx` | `w600k_r50.onnx` | 573.89 | 429.12 | 1102.10 | 0.91 |

### RKNN NPU benchmark

- 실행 위치: `OrangePI RK3588`
- 실행 환경: `RKNN Lite2`
- 해석: 아래 표는 device-side steady-state benchmark다.
- `buffalo_m_i8`는 비교용 candidate pack이고, 기본 pack은 아직 `buffalo_m`이다.

| model pack | dtype | load ms | detection avg ms | recognition avg ms | pipeline avg ms | pipeline FPS | top result | similarity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| `buffalo_m` | `FP16` | 458.73 | 47.36 | 25.31 | 80.92 | 12.36 | `DongHoon` | 0.6306 |
| `buffalo_m_i8` | `INT8` | 295.71 | 25.39 | 11.55 | 38.63 | 25.89 | `DongHoon` | 0.6300 |

### 해석 요약

- CPU에서는 `buffalo_sc`와 `buffalo_s`가 그나마 실시간에 가까웠지만, `buffalo_m`, `buffalo_l`는 실시간 운영용으로는 무겁다.
- RKNN으로 옮기면 `buffalo_m`이 `80.92 ms / 12.36 FPS`, `buffalo_m_i8`가 `38.63 ms / 25.89 FPS`까지 내려온다.
- 즉 이 프로젝트는 `CPU로 버티는 구조`가 아니라 `NPU 주경로로 재배치하는 구조`다.

## `RKNN Lite2`는 무엇인가

`Lite`라는 이름 때문에 종종 `가벼운 대신 성능이나 정확도가 떨어지는 열화판`처럼 보이지만, 여기서는 그런 의미가 아니다.

- `RKNN-Toolkit2`
  - host PC에서 `ONNX -> RKNN` 변환, build, quantization, calibration을 수행하는 개발 도구
- `RKNN Lite2`
  - OrangePI 같은 target device에서 `.rknn` 모델을 실제로 실행하는 runtime API

즉 이 프로젝트에서 `Lite2`를 쓴 이유는 `대충 경량화해서`가 아니라, `RK3588 배포 장치에서 공식 runtime 경로가 그것이기 때문`이다.  
모델 품질과 정확도는 `원본 InsightFace pack`, `FP16/INT8 선택`, `calibration dataset`, `runtime 설정`이 결정하고, `Lite2`라는 이름 자체가 정확도 열화를 뜻하지는 않는다.

또한 여기서 말하는 `Lite2`에 대응되는 어떤 `무거운 고급판 runtime`을 일부러 버린 것이 아니다.  
host에서는 `Toolkit2`, device에서는 `Lite2`를 쓰는 조합이 정상적인 분업이다.

## 이 프로젝트가 실제로 한 일

이 저장소는 `공식 Rockchip 경로`를 쓰되, 그 위에 `InsightFace용 제품 레이어`를 직접 얹었다.

- 공식으로 사용한 것
  - `rknn-toolkit2`
  - `rknnlite.api`
  - device-side `librknnrt`
- 이 repo에서 직접 만든 것
  - InsightFace pack 선별과 alias 정책
  - pack 구조 정규화
  - detector / recognizer별 RKNN export
  - `pack.json` manifest와 `model zoo` 구조
  - `FaceSDK`, `FaceWrapper`, gallery manager
  - OrangePI benchmark, model switching, web console, service 운영

즉 `이미 인터넷에 떠도는 완성된 RKNN InsightFace 모델을 그대로 받아서 포장한 프로젝트`가 아니다.  
반대로 `RKNN 자체를 역공학해서 비공식 포맷으로 억지 변환한 프로젝트`도 아니다.  
정확한 위치는 `공식 Rockchip toolchain을 사용해, InsightFace pack을 이 repo에서 직접 변환·검증·포장한 프로젝트`다.

## 현재 주경로

1. host에서 `InsightFace` 원본 pack을 준비한다.
2. `conversion/export_insightface_pack_rknn.py`로 detector와 recognizer를 `RKNN`으로 변환한다.
3. `conversion/results/model_zoo/rk3588/<pack>/pack.json`으로 canonical manifest를 만든다.
4. OrangePI에서 `RKNN Lite2` 환경을 준비한다.
5. 앱 코드는 `runtime.FaceSDK`를 import해서 detection, embedding, gallery match를 한 번에 쓴다.
6. 운영은 `runtime/web_backend/main.py`와 `runtime/web_frontend/` 기반 web console에서 관리한다.

## 저장소 구조

- `docs/`
  - 운영 규칙과 현재 truth
- `conversion/`
  - host-side RKNN 변환, calibration, model zoo
- `runtime/`
  - SDK, gallery, backend, frontend, service
- `assets/`
  - root README가 직접 참조하는 공용 자산

## 문서 지도

- 운영 규칙: [docs/AGENT.md](docs/AGENT.md)
- 현재 상태와 최근 로그: [docs/logbook.md](docs/logbook.md)
- RKNN 변환 매뉴얼: [conversion/README.md](conversion/README.md)
- OrangePI runtime / service 기준: [runtime/README.md](runtime/README.md)
- README 자산 생성 기준: [assets/readme/build_demo_assets.py](assets/readme/build_demo_assets.py)

## 현재 고정 메모

- wrapper가 주 제품이고 web console은 운영 인터페이스다.
- 현재 기본 runtime pack은 `buffalo_m`이다.
- `buffalo_m_i8`는 비교용 candidate pack으로 유지한다.
- `buffalo_s`는 `buffalo_sc` alias pack이다.
- gallery 저장 구조는 `runtime/gallery/<person_id>/meta.json`, `runtime/gallery/<person_id>/images/*`다.
- 현재 개발 보드 고정 LAN 주소는 `192.168.20.238`이다.
