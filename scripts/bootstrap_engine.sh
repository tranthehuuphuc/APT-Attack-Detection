#!/usr/bin/env bash
set -euo pipefail
ENGINE_DIR="src/engine/graph_matcher/engine_repo"
if [ -d "$ENGINE_DIR/src" ]; then
  echo "[OK] engine_repo already present at $ENGINE_DIR"
  exit 0
fi
if [ $# -lt 1 ]; then
  echo "Usage: bash scripts/bootstrap_engine.sh <MEGR_APT_GIT_URL>"
  exit 1
fi
URL="$1"
mkdir -p "$ENGINE_DIR"
git clone "$URL" "$ENGINE_DIR"
echo "[OK] cloned engine into $ENGINE_DIR"
