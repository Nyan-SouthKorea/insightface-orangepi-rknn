#!/usr/bin/env bash

set -euo pipefail

# Smoke:
#   bash runtime/setup_orangepi_rknn_web_env.sh
#
# Full:
#   bash runtime/setup_orangepi_rknn_web_env.sh
#   source ../envs/ifr_rknn_lite2_cp310/bin/activate
#   python runtime/web_backend/main.py --help
#
# Inputs:
#   - runtime/setup_orangepi_rknn_lite2_env.sh
#   - runtime/requirements_rknn_web.txt
# Outputs:
#   - ../envs/ifr_rknn_lite2_cp310 with FastAPI web packages

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORK_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
VENV_ROOT="${WORK_ROOT}/envs/ifr_rknn_lite2_cp310"
REQUIREMENTS_PATH="${REPO_ROOT}/runtime/requirements_rknn_web.txt"

bash "${REPO_ROOT}/runtime/setup_orangepi_rknn_lite2_env.sh"

source "${VENV_ROOT}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "${REQUIREMENTS_PATH}"

python - <<'PY'
import fastapi
import uvicorn
print("fastapi", fastapi.__version__)
print("uvicorn", uvicorn.__version__)
PY
