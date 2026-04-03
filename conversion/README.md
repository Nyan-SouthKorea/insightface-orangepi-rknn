# conversion

## 역할

- 이 모듈은 `InsightFace` 계열 얼굴 모델을 `RKNN`으로 변환하는 경로를 맡는다.
- 목표는 다른 사람도 그대로 따라 해서 같은 `RKNN model zoo`를 다시 만들 수 있는 재현 가능한 절차를 남기는 것이다.
- 현재 canonical face-only pack은 `buffalo_sc`, `buffalo_m`, `buffalo_l`이고, `buffalo_s`는 alias manifest로 연결한다.
- 현재 `INT8` 비교 pack은 `buffalo_m_i8`까지 만들었다.

## 이 모듈이 맡는 것

- host 변환 환경
- `ONNX -> RKNN` export entry
- `INT8 calibration` 입력 묶음 준비
- pack-level manifest 생성
- alias pack 정리
- 변환 절차 문서화

## 이 모듈이 맡지 않는 것

- OrangePI 카메라 루프
- web UI
- 실시간 서비스 운영

## host 변환 환경

- venv 이름: `../envs/ifr_rknn_host_cp310`
- 고정 조합:
- `Python 3.10`
- `RKNN Toolkit2 2.3.2`
- `setuptools 75.8.0`
- `onnx 1.16.1`

환경 생성:

```bash
bash conversion/setup_rknn_host_env.sh
source ../envs/ifr_rknn_host_cp310/bin/activate
python -c "from rknn.api import RKNN; print('rknn host env ok')"
```

## 그대로 따라 하는 RKNN 변환 순서

1. host 환경 준비

```bash
bash conversion/setup_rknn_host_env.sh
source ../envs/ifr_rknn_host_cp310/bin/activate
```

2. InsightFace 원본 pack 준비

- 기본 입력 경로는 `~/.insightface/models/<pack>/`이다.
- `buffalo_m`처럼 zip 내부가 한 단계 더 중첩된 pack도 `export_insightface_pack_rknn.py`가 정규화한다.

3. 첫 smoke pack 변환

```bash
python conversion/export_insightface_pack_rknn.py \
  --model-packs buffalo_sc \
  --target-platform rk3588 \
  --dtype fp \
  --skip-existing
```

4. 전체 face-only pack 변환

```bash
python conversion/export_insightface_pack_rknn.py \
  --model-packs buffalo_sc,buffalo_m,buffalo_l,buffalo_s \
  --target-platform rk3588 \
  --dtype fp \
  --skip-existing
```

5. `INT8 calibration` 입력 준비

- calibration 이미지는 private local 자산으로 보고 `conversion/results/calibration/` 아래에만 둔다.
- 현재 canonical 준비 script는 `conversion/prepare_rknn_calibration_dataset.py`다.

```bash
python conversion/prepare_rknn_calibration_dataset.py \
  --output-dir conversion/results/calibration/buffalo_m_i8 \
  --source-glob runtime/results/face_benchmark_input.jpg \
  --snapshot-url http://<orangepi-host>:5000/api/snapshot.jpg \
  --snapshot-count 24 \
  --snapshot-interval 0.25
```

6. `buffalo_m_i8` 변환

```bash
python conversion/export_insightface_pack_rknn.py \
  --model-packs buffalo_m_i8 \
  --target-platform rk3588 \
  --dtype i8 \
  --detector-dataset conversion/results/calibration/buffalo_m_i8/detector_dataset.txt \
  --recognizer-dataset conversion/results/calibration/buffalo_m_i8/recognizer_dataset.txt
```

7. OrangePI에서 단건 smoke

```bash
source ../envs/ifr_rknn_lite2_cp310/bin/activate
python runtime/probe_rknn_lite2.py \
  --rknn-path conversion/results/model_zoo/rk3588/buffalo_sc/det_500m_fp16.rknn \
  --input-image runtime/results/face_benchmark_input.jpg \
  --model-kind detection \
  --input-size 640,640

python runtime/probe_rknn_lite2.py \
  --rknn-path conversion/results/model_zoo/rk3588/buffalo_sc/w600k_mbf_fp16.rknn \
  --input-image runtime/results/face_benchmark_input.jpg \
  --model-kind recognition \
  --input-size 112,112
```

8. SDK smoke

```bash
source ../envs/ifr_rknn_lite2_cp310/bin/activate
python - <<'PY'
import cv2
from runtime import FaceSDK

sdk = FaceSDK(
    gallery_dir="runtime/gallery",
    model_pack="buffalo_m",
    backend="rknn",
)
frame = cv2.imread("runtime/results/face_benchmark_input.jpg")
print(sdk.describe())
print(sdk.infer(frame))
sdk.close()
PY
```

9. OrangePI 성능 비교

```bash
source ../envs/ifr_rknn_lite2_cp310/bin/activate
python runtime/benchmark_rknn_face_sdk.py \
  --image-path runtime/results/face_benchmark_input.jpg \
  --gallery-dir runtime/gallery \
  --model-packs buffalo_m,buffalo_m_i8 \
  --repeat 20 \
  --warmup 5 \
  --output-json runtime/results/260401_1828_rknn_face_sdk_benchmark/summary.json
```

## 현재 canonical 산출물

- `conversion/results/model_zoo/rk3588/buffalo_sc/*`
- `conversion/results/model_zoo/rk3588/buffalo_s/pack.json`
- `conversion/results/model_zoo/rk3588/buffalo_m/*`
- `conversion/results/model_zoo/rk3588/buffalo_m_i8/*`
- `conversion/results/model_zoo/rk3588/buffalo_l/*`
- `conversion/results/calibration/README.local.md`

## manifest 규칙

- `conversion/results/model_zoo/<platform>/<pack>/pack.json`은 runtime이 직접 읽는다.
- alias pack은 `alias_of`, `face_only_alias`, `note`를 포함한다.
- 실제 pack은 detector와 recognizer의 `onnx_filename`, `output_filename`, `output_rknn_path`, `metadata`를 함께 둔다.

## `buffalo_s` alias 구조

- 이 저장소의 현재 범위는 `face-only`이므로, `buffalo_s`에서 실제로 쓰는 detector와 recognizer는 `buffalo_sc`와 같은 바이너리를 재사용한다.
- 그래서 `conversion/results/model_zoo/rk3588/buffalo_s/`에는 `.rknn` 파일을 중복 저장하지 않고 `pack.json`만 둔다.
- `pack.json`의 `alias_of: "buffalo_sc"`와 `face_only_alias: true`를 runtime이 읽어 실제 `.rknn` 파일을 `buffalo_sc/`에서 연다.
- `buffalo_s` zip 안에 있는 `1k3d68`, `2d106det`, `genderage` 같은 보조 모델 정보는 metadata로만 남기고, 현재 canonical runtime 경로에는 포함하지 않는다.
- 따라서 `buffalo_s` 폴더에 `.rknn` 파일이 보이지 않아도 누락이 아니라 현재 canonical layout의 의도된 구조다.

## 현재 고정 결정

- 기본 dtype은 `FP16`이다.
- 현재 `INT8` 비교 candidate는 `buffalo_m_i8`이다.
- `buffalo_s`는 별도 변환 대신 `buffalo_sc` alias로 유지한다.
- detection 정규화는 `mean 127.5 / std 128.0`, recognition 정규화는 `mean 127.5 / std 127.5`다.
- `INT8 calibration` 입력은 local-only `conversion/results/calibration/` 아래에 둔다.
- detector와 recognizer는 필요하면 각기 다른 dataset txt를 받게 유지한다.

## 관련 문서

- [root README](../README.md)
- [project logbook](../docs/logbook.md)
- [module logbook](docs/logbook.md)
