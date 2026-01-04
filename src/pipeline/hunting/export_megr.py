from __future__ import annotations
from typing import Dict, List, Tuple
import networkx as nx
import torch
from torch_geometric.data import Data

NODE_TYPES = ["process", "file", "socket", "other"]
EDGE_TYPES = ["FORK", "READ", "WRITE", "CREATE", "DELETE", "CONNECT", "OTHER"]

def _one_hot(idx: int, size: int) -> torch.Tensor:
    x = torch.zeros(size, dtype=torch.float)
    x[idx] = 1.0
    return x

def to_megr_data_list(g: nx.DiGraph, g_name: str) -> List[Data]:
    # single-graph list (engine expects list[Data])
    nodes = list(g.nodes())
    idx = {n:i for i,n in enumerate(nodes)}
    # edge index
    edges = list(g.edges(data=True))
    if edges:
        edge_index = torch.tensor([[idx[u] for u,v,_ in edges],[idx[v] for u,v,_ in edges]], dtype=torch.long)
        elabel = torch.tensor([EDGE_TYPES.index((dat.get("etype","OTHER") if dat.get("etype","OTHER") in EDGE_TYPES else "OTHER")) for _,_,dat in edges], dtype=torch.long)
    else:
        edge_index = torch.empty((2,0), dtype=torch.long)
        elabel = torch.empty((0,), dtype=torch.long)

    nlabel = torch.stack([
        _one_hot(NODE_TYPES.index((g.nodes[n].get("ntype") if g.nodes[n].get("ntype") in NODE_TYPES else "other")), len(NODE_TYPES))
        for n in nodes
    ], dim=0)

    data = Data(edge_index=edge_index, g_name=g_name)
    data.num_nodes = len(nodes)
    data.nlabel = nlabel
    data.elabel = elabel
    return [data]

def save_prediction_pt(out_path, data_list: List[Data]) -> None:
    import os
    os.makedirs(os.path.dirname(str(out_path)), exist_ok=True)
    torch.save(data_list, out_path)
