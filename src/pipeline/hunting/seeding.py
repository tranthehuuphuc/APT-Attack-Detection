from __future__ import annotations
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
import json
import networkx as nx

SUSPICIOUS_PATH_PREFIXES = ("/tmp/", "/dev/shm/", "/var/tmp/")


def _load_cti_seeds(path: Optional[str]) -> Tuple[List[dict], List[dict]]:
    if not path:
        return [], []
    p = Path(path)
    if not p.exists():
        return [], []
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        return obj.get("techniques", []) or [], obj.get("indicators", []) or []
    except Exception:
        return [], []


def _match_indicator_to_nodes(g: nx.DiGraph, ind: dict) -> Set[str]:
    typ = (ind.get("type") or "").strip()
    val = (ind.get("value") or "").strip()
    if not typ or not val:
        return set()
    vlow = val.lower()
    out: Set[str] = set()

    for n, dat in g.nodes(data=True):
        ntype = dat.get("ntype")
        if typ == "file_path" and ntype == "file":
            if vlow in (dat.get("path", "").lower()):
                out.add(n)
        elif typ in ("process_name", "command_line") and ntype == "process":
            exe = (dat.get("exe", "").lower())
            comm = (dat.get("comm", "").lower())
            if vlow in exe or vlow in comm:
                out.add(n)
        elif typ in ("ip", "domain") and ntype == "socket":
            saddr = (dat.get("saddr", "").lower())
            if vlow in saddr:
                out.add(n)
    return out

def find_seeds(
    g: nx.DiGraph,
    query_name: Optional[str] = None,
    cti_seeds_path: Optional[str] = None,
) -> List[str]:
    seeds: Set[str] = set()

    # 0) CTI-derived indicators (preferred)
    _techs, inds = _load_cti_seeds(cti_seeds_path)
    for ind in inds:
        seeds |= _match_indicator_to_nodes(g, ind)

    # Heuristic: suspicious file paths
    for n, dat in g.nodes(data=True):
        if dat.get("ntype") == "file":
            path = dat.get("path","")
            if path.startswith(SUSPICIOUS_PATH_PREFIXES):
                seeds.add(n)
    # Heuristic: processes with exe in temp paths
    for n, dat in g.nodes(data=True):
        if dat.get("ntype") == "process":
            exe = dat.get("exe","")
            if exe.startswith(SUSPICIOUS_PATH_PREFIXES):
                seeds.add(n)
    # If query_name is provided, keep as tag (future extension)
    return list(seeds)
