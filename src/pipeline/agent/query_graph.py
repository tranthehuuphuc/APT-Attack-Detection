from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
import networkx as nx
from networkx.readwrite import json_graph

from src.common.io import write_json

@dataclass
class QueryGraph:
    technique_id: str
    graph: nx.DiGraph

def build_simple_query_graph(technique_id: str) -> QueryGraph:
    # deterministic minimal template: process -> file -> socket
    g = nx.DiGraph()
    g.add_node("proc", type="process")
    g.add_node("file", type="file")
    g.add_node("sock", type="socket")
    g.add_edge("proc", "file", type="READ")
    g.add_edge("proc", "sock", type="CONNECT")
    return QueryGraph(technique_id=technique_id, graph=g)

def export_query_graph_json(out_dir: Path, qg: QueryGraph) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{qg.technique_id}.json"
    payload = json_graph.node_link_data(qg.graph)
    payload["technique_id"] = qg.technique_id
    write_json(p, payload)
    return p
