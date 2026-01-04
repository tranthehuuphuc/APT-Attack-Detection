from __future__ import annotations
from typing import Any, Dict, List, Optional
from src.pipeline.hunting.audit_stream import AuditRecord
import datetime
import re

def _first(records: List[AuditRecord], rtype: str) -> Optional[AuditRecord]:
    for r in records:
        if r.record_type == rtype:
            return r
    return None

def _get(rec: Optional[AuditRecord], key: str, default: str = "") -> str:
    if rec is None:
        return default
    return rec.kv.get(key, default)

TS_RE = re.compile(r"audit\((\d+)\.(\d+):\d+\)")

def _extract_ts(raw: str) -> float:
    m = TS_RE.search(raw)
    if not m:
        return 0.0
    sec = int(m.group(1))
    usec = int(m.group(2))
    return float(sec) + float(usec)/1000000.0

def _syscall_name(syscall: str) -> str:
    # some audit logs provide syscall name in 'syscall=' already (numeric). Keep numeric string.
    return syscall

def normalize_records(records: List[AuditRecord]) -> Optional[Dict[str, Any]]:
    if not records:
        return None
    raw0 = records[0].raw
    ts = _extract_ts(raw0)

    syscall = _first(records, "SYSCALL")
    if syscall is None:
        return None

    pid = _get(syscall, "pid")
    ppid = _get(syscall, "ppid")
    uid = _get(syscall, "uid") or _get(syscall, "auid")
    exe = _get(syscall, "exe").strip('"')
    comm = _get(syscall, "comm").strip('"')
    sc = _get(syscall, "syscall")

    cwd_rec = _first(records, "CWD")
    cwd = _get(cwd_rec, "cwd").strip('"')

    # Process start / exec
    execve = _first(records, "EXECVE")
    if execve is not None:
        argv = [v.strip('"') for k, v in sorted(execve.kv.items()) if k.startswith("a")]
        return {
            "ts": ts,
            "kind": "process_start",
            "pid": int(pid) if pid.isdigit() else pid,
            "ppid": int(ppid) if ppid.isdigit() else ppid,
            "uid": uid,
            "exe": exe,
            "comm": comm,
            "cwd": cwd,
            "syscall": sc,
            "argv": argv,
            "serial": records[0].serial,
        }

    # File ops: PATH record exists
    path_rec = _first(records, "PATH")
    if path_rec is not None:
        name = _get(path_rec, "name").strip('"')
        nametype = _get(path_rec, "nametype")
        # crude action inference: use syscall number bucket + nametype
        action = "OTHER"
        if nametype in ("CREATE", "CREATE-TRUNCATE"):
            action = "CREATE"
        elif nametype == "DELETE":
            action = "DELETE"
        # if open/read/write not directly known, tag by comm/syscall
        return {
            "ts": ts,
            "kind": "file_op",
            "pid": int(pid) if pid.isdigit() else pid,
            "uid": uid,
            "exe": exe,
            "comm": comm,
            "cwd": cwd,
            "path": name,
            "nametype": nametype,
            "action": action,
            "syscall": sc,
            "serial": records[0].serial,
        }

    # Network connect: SOCKADDR
    sock = _first(records, "SOCKADDR")
    if sock is not None:
        saddr = _get(sock, "saddr")
        return {
            "ts": ts,
            "kind": "net_op",
            "pid": int(pid) if pid.isdigit() else pid,
            "uid": uid,
            "exe": exe,
            "comm": comm,
            "cwd": cwd,
            "saddr": saddr,
            "syscall": sc,
            "serial": records[0].serial,
        }

    return None
