#!/usr/bin/env bash

set -euo pipefail

# Smoke:
#   bash runtime/setup_orangepi_rknn_lite2_env.sh
#
# Full:
#   bash runtime/setup_orangepi_rknn_lite2_env.sh
#   source ../envs/ifr_rknn_lite2_cp310/bin/activate
#   python runtime/probe_rknn_lite2.py --help
#
# Inputs:
#   - OrangePI Python 3.10
# Outputs:
#   - ../envs/ifr_rknn_lite2_cp310

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORK_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
VENV_ROOT="${WORK_ROOT}/envs/ifr_rknn_lite2_cp310"
WHEEL_URL="https://raw.githubusercontent.com/airockchip/rknn-toolkit2/master/rknn-toolkit-lite2/packages/rknn_toolkit_lite2-2.3.2-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl"

mkdir -p "${WORK_ROOT}/envs"
python3.10 -m venv "${VENV_ROOT}"
source "${VENV_ROOT}/bin/activate"

python -m pip install --upgrade pip setuptools wheel
python -m pip install "${WHEEL_URL}"
python -m pip install opencv-python-headless==4.10.0.84

python - <<'PY'
import cv2
from rknnlite.api import RKNNLite
print("opencv env ok:", cv2.__version__)
print("rknn lite2 env ok:", RKNNLite)
PY

echo "venv ready: ${VENV_ROOT}"
