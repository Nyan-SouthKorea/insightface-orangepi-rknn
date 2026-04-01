#!/usr/bin/env bash

set -euo pipefail

# Smoke:
#   PORT=5050 bash runtime/install_orangepi_rknn_web_service.sh
#
# Full:
#   bash runtime/install_orangepi_rknn_web_service.sh
#   sudo systemctl restart insightface_gallery_web.service
#
# Inputs:
#   - runtime/insightface_rknn_web.service.template
#   - ../envs/ifr_rknn_lite2_cp310
# Outputs:
#   - /etc/systemd/system/insightface_gallery_web.service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORK_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
VENV_ROOT="${WORK_ROOT}/envs/ifr_rknn_lite2_cp310"
SERVICE_TEMPLATE="${REPO_ROOT}/runtime/insightface_rknn_web.service.template"
SERVICE_OUTPUT="/tmp/insightface_gallery_web.service"
SYSTEMD_TARGET="/etc/systemd/system/insightface_gallery_web.service"
DEFAULT_CAMERA_SOURCE=""

if [[ -d /dev/v4l/by-id ]]; then
  DEFAULT_CAMERA_SOURCE="$(find /dev/v4l/by-id -maxdepth 1 -type l -name '*video-index0' | sort | head -n 1)"
fi

CAMERA_SOURCE="${CAMERA_SOURCE:-${DEFAULT_CAMERA_SOURCE:-21}}"
MODEL_PACK="${MODEL_PACK:-buffalo_m}"
PORT="${PORT:-5000}"

if [[ "${EUID}" -eq 0 ]]; then
  SUDO=()
else
  if [[ -t 0 ]]; then
    sudo -v
  else
    sudo -S -v
  fi
  SUDO=(sudo -n)
fi

if [[ ! -x "${VENV_ROOT}/bin/python" ]]; then
  echo "venv를 찾지 못했습니다: ${VENV_ROOT}"
  echo "먼저 bash runtime/setup_orangepi_rknn_web_env.sh 를 실행하세요."
  exit 1
fi

sed \
  -e "s|__USER__|${USER}|g" \
  -e "s|__REPO_ROOT__|${REPO_ROOT}|g" \
  -e "s|__VENV_ROOT__|${VENV_ROOT}|g" \
  -e "s|__CAMERA_SOURCE__|${CAMERA_SOURCE}|g" \
  -e "s|__MODEL_PACK__|${MODEL_PACK}|g" \
  -e "s|__PORT__|${PORT}|g" \
  "${SERVICE_TEMPLATE}" > "${SERVICE_OUTPUT}"

"${SUDO[@]}" cp "${SERVICE_OUTPUT}" "${SYSTEMD_TARGET}"
"${SUDO[@]}" systemctl daemon-reload
"${SUDO[@]}" systemctl enable insightface_gallery_web.service
"${SUDO[@]}" systemctl restart insightface_gallery_web.service
"${SUDO[@]}" systemctl --no-pager --full status insightface_gallery_web.service

echo "service camera source: ${CAMERA_SOURCE}"
echo "service model pack: ${MODEL_PACK}"
echo "service port: ${PORT}"
