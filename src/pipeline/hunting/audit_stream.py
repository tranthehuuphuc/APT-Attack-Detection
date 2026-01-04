from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional

SERIAL_RE = re.compile(r"msg=audit\([^:]+:(\d+)\)")
TYPE_RE = re.compile(r"type=([A-Z_]+)")
KV_RE = re.compile(r"(\w+)=([^\s]+)")

@dataclass
class AuditRecord:
    record_type: str
    serial: str
    kv: Dict[str, str]
    raw: str

def parse_record(line: str) -> Optional[AuditRecord]:
    mtype = TYPE_RE.search(line)
    mserial = SERIAL_RE.search(line)
    if not mtype or not mserial:
        return None
    record_type = mtype.group(1)
    serial = mserial.group(1)
    kv: Dict[str, str] = {}
    for k, v in KV_RE.findall(line):
        kv[k] = v.strip('"')
    return AuditRecord(record_type=record_type, serial=serial, kv=kv, raw=line)

def group_by_serial(lines: Iterable[str]) -> Iterator[List[AuditRecord]]:
    current: Optional[str] = None
    bucket: List[AuditRecord] = []
    for line in lines:
        rec = parse_record(line)
        if rec is None:
            continue
        if current is None:
            current = rec.serial
            bucket = [rec]
            continue
        if rec.serial == current:
            bucket.append(rec)
        else:
            yield bucket
            current = rec.serial
            bucket = [rec]
    if bucket:
        yield bucket
