#!/usr/bin/env bash

set -euo pipefail

# Smoke:
#   bash runtime/setup_orangepi_ort_cpu_env.sh
#
# Full:
#   bash runtime/setup_orangepi_ort_cpu_env.sh
#   python runtime/face_gallery_web_demo.py --host 0.0.0.0 --port 5000 --capture-mode webcam
#
# Inputs:
#   - repo/runtime/requirements_ort_cpu_probe.txt
# Outputs:
#   - ../envs/ifr_ort_cpu_probe

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORK_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
VENV_ROOT="${WORK_ROOT}/envs/ifr_ort_cpu_probe"

mkdir -p "${WORK_ROOT}/envs"

python3 -m venv "${VENV_ROOT}"
source "${VENV_ROOT}/bin/activate"

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r "${REPO_ROOT}/runtime/requirements_ort_cpu_probe.txt"

python - <<'PY'
import onnxruntime as ort
print("onnxruntime version:", ort.__version__)
print("available providers:", ort.get_available_providers())
PY

python - <<'PY'
from insightface.app import FaceAnalysis

app = FaceAnalysis(name="buffalo_s", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=-1, det_size=(640, 640))
print("insightface cpu probe: ok")
PY

echo "venv ready: ${VENV_ROOT}"
