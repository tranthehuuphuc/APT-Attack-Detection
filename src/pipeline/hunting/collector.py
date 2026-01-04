from __future__ import annotations
import argparse
import time
from pathlib import Path
import logging

from src.common.logging import setup_logging
from src.common.io import append_jsonl
from src.pipeline.hunting.audit_stream import group_by_serial
from src.pipeline.hunting.normalizer import normalize_records

log = logging.getLogger(__name__)

def follow(path: Path, sleep: float = 0.2):
    # tail -F like follow
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(sleep)
                continue
            yield line

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit-log", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--log-level", default="INFO")
    args = ap.parse_args()

    setup_logging(args.log_level)
    audit_path = Path(args.audit_log)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Collector following %s -> %s", audit_path, out_path)
    for recs in group_by_serial(follow(audit_path)):
        ev = normalize_records(recs)
        if ev:
            append_jsonl(out_path, ev)

if __name__ == "__main__":
    main()
