#!/usr/bin/env bash
set -euo pipefail
DATASET="${1:-cadets}"
CHECKPOINT="${2:-runs/checkpoints/cadets_demo.pt}"
EVENTS="${3:-runs/events/events.jsonl}"
CTI_SEEDS="${4:-runs/cti/seeds.json}"

python -m src.pipeline.hunting.main \
  --dataset "$DATASET" \
  --events "$EVENTS" \
  --checkpoint "$CHECKPOINT" \
  --cti-seeds "$CTI_SEEDS"
