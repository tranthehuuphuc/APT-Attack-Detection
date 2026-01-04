from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import difflib

from src.pipeline.agent.attack_knowledge import Technique, exact_id_hits

@dataclass
class Candidate:
    tid: str
    score: float
    evidence: str

def _fuzzy_match(text: str, techniques: List[Technique], top_k: int = 5) -> List[Candidate]:
    # lightweight string similarity over technique names
    text_l = text.lower()
    cands: List[Candidate] = []
    for tech in techniques:
        name = tech.name.lower()
        ratio = difflib.SequenceMatcher(None, text_l, name).ratio()
        if ratio > 0.25:
            cands.append(Candidate(tid=tech.tid, score=ratio, evidence=name))
    cands.sort(key=lambda x: x.score, reverse=True)
    return cands[:top_k]

def map_chunk(text: str, techniques: List[Technique], top_k: int = 6) -> List[Candidate]:
    # channel 1: exact IDs
    ids = exact_id_hits(text)
    out: List[Candidate] = [Candidate(tid=i, score=1.0, evidence="exact_id") for i in ids]
    # channel 2: fuzzy names
    out.extend(_fuzzy_match(text, techniques, top_k=top_k))
    # de-dup keep best
    best: Dict[str, Candidate] = {}
    for c in out:
        if c.tid not in best or c.score > best[c.tid].score:
            best[c.tid] = c
    return sorted(best.values(), key=lambda x: x.score, reverse=True)[:top_k]
