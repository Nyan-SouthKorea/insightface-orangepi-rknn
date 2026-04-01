#!/usr/bin/env bash

set -euo pipefail

# Smoke:
#   bash runtime/install_orangepi_service.sh
#
# Full:
#   bash runtime/install_orangepi_service.sh
#   sudo systemctl restart insightface_gallery_web.service
#
# Inputs:
#   - repo/runtime/insightface_gallery_web.service.template
#   - ../envs/ifr_ort_cpu_probe
# Outputs:
#   - /etc/systemd/system/insightface_gallery_web.service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORK_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
VENV_ROOT="${WORK_ROOT}/envs/ifr_ort_cpu_probe"
SERVICE_TEMPLATE="${REPO_ROOT}/runtime/insightface_gallery_web.service.template"
SERVICE_OUTPUT="/tmp/insightface_gallery_web.service"
SYSTEMD_TARGET="/etc/systemd/system/insightface_gallery_web.service"

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
  echo "먼저 bash runtime/setup_orangepi_ort_cpu_env.sh 를 실행하세요."
  exit 1
fi

sed \
  -e "s|__USER__|${USER}|g" \
  -e "s|__REPO_ROOT__|${REPO_ROOT}|g" \
  -e "s|__VENV_ROOT__|${VENV_ROOT}|g" \
  "${SERVICE_TEMPLATE}" > "${SERVICE_OUTPUT}"

"${SUDO[@]}" cp "${SERVICE_OUTPUT}" "${SYSTEMD_TARGET}"
"${SUDO[@]}" systemctl daemon-reload
"${SUDO[@]}" systemctl enable insightface_gallery_web.service
"${SUDO[@]}" systemctl restart insightface_gallery_web.service
"${SUDO[@]}" systemctl --no-pager --full status insightface_gallery_web.service
