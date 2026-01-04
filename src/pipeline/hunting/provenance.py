from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Set, Tuple
import networkx as nx
import time

NODE_PROCESS = "process"
NODE_FILE = "file"
NODE_SOCKET = "socket"

def _proc_node(pid: Any) -> str:
    return f"p:{pid}"

def _file_node(path: str) -> str:
    return f"f:{path}"

def _sock_node(saddr: str) -> str:
    return f"s:{saddr}"

@dataclass
class WindowedProvenanceGraph:
    window_seconds: int = 120
    max_nodes: int = 200000

    def __post_init__(self):
        self.g = nx.DiGraph()

    def _prune(self, now_ts: float) -> None:
        cutoff = now_ts - self.window_seconds
        # remove old edges; keep nodes if still connected
        remove_edges = [(u,v) for u,v,dat in self.g.edges(data=True) if dat.get("ts", now_ts) < cutoff]
        self.g.remove_edges_from(remove_edges)
        # optional: trim isolated nodes if too big
        if self.g.number_of_nodes() > self.max_nodes:
            isolates = list(nx.isolates(self.g))
            self.g.remove_nodes_from(isolates[: max(0, len(isolates)//2)])

    def ingest(self, ev: Dict[str, Any]) -> None:
        ts = float(ev.get("ts", time.time()))
        kind = ev.get("kind")
        self._prune(ts)

        if kind == "process_start":
            p = _proc_node(ev["pid"])
            pp = _proc_node(ev.get("ppid", "0"))
            self.g.add_node(p, ntype=NODE_PROCESS, exe=ev.get("exe",""), comm=ev.get("comm",""))
            self.g.add_node(pp, ntype=NODE_PROCESS)
            self.g.add_edge(pp, p, etype="FORK", ts=ts)
            return

        if kind == "file_op":
            p = _proc_node(ev["pid"])
            f = _file_node(ev.get("path",""))
            self.g.add_node(p, ntype=NODE_PROCESS, exe=ev.get("exe",""), comm=ev.get("comm",""))
            self.g.add_node(f, ntype=NODE_FILE, path=ev.get("path",""))
            act = ev.get("action","OTHER")
            etype = "READ" if act == "OTHER" else act  # conservative
            self.g.add_edge(p, f, etype=etype, ts=ts)
            return

        if kind == "net_op":
            p = _proc_node(ev["pid"])
            s = _sock_node(ev.get("saddr",""))
            self.g.add_node(p, ntype=NODE_PROCESS, exe=ev.get("exe",""), comm=ev.get("comm",""))
            self.g.add_node(s, ntype=NODE_SOCKET, saddr=ev.get("saddr",""))
            self.g.add_edge(p, s, etype="CONNECT", ts=ts)
            return
