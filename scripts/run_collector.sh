#!/usr/bin/env bash
set -euo pipefail
AUDIT_LOG="${1:-/var/log/audit/audit.log}"
OUT="${2:-runs/events/events.jsonl}"
python -m src.pipeline.hunting.collector --audit-log "$AUDIT_LOG" --out "$OUT"
