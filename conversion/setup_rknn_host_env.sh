#!/usr/bin/env bash

set -euo pipefail

# Smoke:
#   bash conversion/setup_rknn_host_env.sh
#   source ../envs/ifr_rknn_host_cp310/bin/activate
#   python -c "from rknn.api import RKNN; print('rknn host env ok')"
#
# Full:
#   bash conversion/setup_rknn_host_env.sh
#   source ../envs/ifr_rknn_host_cp310/bin/activate
#   python conversion/export_insightface_rknn.py \
#     --onnx-path ~/.insightface/models/buffalo_sc/det_500m.onnx \
#     --output-rknn-path conversion/results/model_zoo/rk3588/buffalo_sc/det_500m_fp16.rknn \
#     --model-kind detection \
#     --input-shape 1,3,640,640 \
#     --target-platform rk3588 \
#     --dtype fp
#
# Inputs:
#   - repo/conversion/requirements_rknn_host_cp310.txt
# Outputs:
#   - ../envs/ifr_rknn_host_cp310

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORK_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
VENV_ROOT="${WORK_ROOT}/envs/ifr_rknn_host_cp310"
WHEEL_URL="https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit2/packages/x86_64/rknn_toolkit2-2.3.2-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"

mkdir -p "${WORK_ROOT}/envs"
python3.10 -m venv "${VENV_ROOT}"
source "${VENV_ROOT}/bin/activate"

python -m pip install --upgrade pip wheel
python -m pip install setuptools==75.8.0
python -m pip install -r "${REPO_ROOT}/conversion/requirements_rknn_host_cp310.txt"
python -m pip install "${WHEEL_URL}"

python - <<'PY'
from rknn.api import RKNN
print("rknn host env ok:", RKNN)
PY

echo "venv ready: ${VENV_ROOT}"
