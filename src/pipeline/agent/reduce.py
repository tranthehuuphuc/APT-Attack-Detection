from __future__ import annotations
from typing import Dict, List, Optional
from src.pipeline.agent.map_step import Candidate

def reduce_candidates(chunks: List[List[Candidate]]) -> List[Candidate]:
    # merge by max score, accumulate evidence count
    best: Dict[str, Candidate] = {}
    counts: Dict[str, int] = {}
    for cs in chunks:
        for c in cs:
            counts[c.tid] = counts.get(c.tid, 0) + 1
            if c.tid not in best or c.score > best[c.tid].score:
                best[c.tid] = c
    out = list(best.values())
    # boost by frequency slightly
    for c in out:
        c.score = float(c.score) + 0.05 * (counts.get(c.tid, 1) - 1)
    out.sort(key=lambda x: x.score, reverse=True)
    return out


def reduce_llm(
    technique_chunks: List[List[dict]],
    indicator_chunks: List[List[dict]],
    stix_name_by_id: Optional[Dict[str, str]] = None,
) -> Dict[str, List[dict]]:
    """Reduce (merge + de-dup) for LLM outputs.

    - Techniques are merged by technique_id if present else by lowercased technique_name.
    - Indicators are merged by (type,value).
    """
    stix_name_by_id = stix_name_by_id or {}

    best_t: Dict[str, dict] = {}
    for cs in technique_chunks:
        for it in cs:
            tid = (it.get("technique_id") or "").strip()
            name = (it.get("technique_name") or "").strip()
            if tid and tid in stix_name_by_id:
                it["technique_name"] = stix_name_by_id[tid]
            key = tid or name.lower()
            if not key:
                continue
            if key not in best_t or float(it.get("confidence", 0)) > float(best_t[key].get("confidence", 0)):
                best_t[key] = it
    techniques = list(best_t.values())
    techniques.sort(key=lambda x: float(x.get("confidence", 0)), reverse=True)

    best_i: Dict[str, dict] = {}
    for cs in indicator_chunks:
        for it in cs:
            typ = (it.get("type") or "").strip()
            val = (it.get("value") or "").strip()
            if not typ or not val:
                continue
            key = f"{typ}::{val.lower()}"
            if key not in best_i or float(it.get("confidence", 0)) > float(best_i[key].get("confidence", 0)):
                best_i[key] = it
    indicators = list(best_i.values())
    indicators.sort(key=lambda x: float(x.get("confidence", 0)), reverse=True)

    return {"techniques": techniques, "indicators": indicators}
