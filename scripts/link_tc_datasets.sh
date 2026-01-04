#!/usr/bin/env bash
set -euo pipefail
ENGINE_DATASET_DIR="src/engine/graph_matcher/engine_repo/dataset"
TARGET="data/datasets"
mkdir -p "$TARGET"
for ds in darpa_cadets darpa_theia darpa_trace; do
  if [ ! -d "$ENGINE_DATASET_DIR/$ds" ]; then
    echo "[WARN] missing engine dataset folder: $ENGINE_DATASET_DIR/$ds"
    continue
  fi
  if [ -e "$TARGET/$ds" ]; then
    echo "[OK] $TARGET/$ds exists"
  else
    ln -s "../../$ENGINE_DATASET_DIR/$ds" "$TARGET/$ds"
    echo "[OK] linked $ds"
  fi
done
