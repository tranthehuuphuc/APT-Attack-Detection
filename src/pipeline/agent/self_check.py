from __future__ import annotations
from typing import List, Set
from src.pipeline.agent.map_step import Candidate

def self_check(cands: List[Candidate], valid_ids: Set[str], min_conf: float = 0.35) -> List[Candidate]:
    # enforce: valid technique ids only, min confidence
    out = [c for c in cands if (c.tid in valid_ids and c.score >= min_conf)]
    # cap
    return out[:10]
