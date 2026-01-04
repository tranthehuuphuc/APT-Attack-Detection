from __future__ import annotations
from typing import Iterable, List, Set
import networkx as nx

def k_hop_subgraph(g: nx.DiGraph, seeds: List[str], k: int = 2) -> nx.DiGraph:
    if not seeds:
        return g.copy()
    nodes: Set[str] = set(seeds)
    frontier: Set[str] = set(seeds)
    for _ in range(k):
        nxt: Set[str] = set()
        for u in frontier:
            nxt.update(g.predecessors(u))
            nxt.update(g.successors(u))
        nxt -= nodes
        nodes |= nxt
        frontier = nxt
        if not frontier:
            break
    return g.subgraph(nodes).copy()
