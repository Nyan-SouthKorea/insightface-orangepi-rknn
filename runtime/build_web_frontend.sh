#!/usr/bin/env bash

set -euo pipefail

# Smoke:
#   bash runtime/build_web_frontend.sh
#
# Full:
#   bash runtime/build_web_frontend.sh
#   ls runtime/web_frontend/dist
#
# Inputs:
#   - runtime/web_frontend/package.json
#   - runtime/web_frontend/src/*
# Outputs:
#   - runtime/web_frontend/dist/*

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_ROOT="${REPO_ROOT}/runtime/web_frontend"

cd "${FRONTEND_ROOT}"
npm install
npm run build
