from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.pipeline.agent.schemas_llm import SELF_CORRECT_SCHEMA
from src.pipeline.agent.cache import load_cache, save_cache
from src.pipeline.agent.llm_router import call_llm


SYSTEM = """You validate and correct extracted techniques/indicators.

You receive:
- full CTI text
- candidate techniques
- candidate indicators
- list of allowed technique IDs from STIX

Tasks:
1) Remove any item whose evidence.span_text is NOT an exact substring of the CTI text.
2) Fix start_char/end_char offsets if incorrect.
3) If technique_id is not in allowed IDs, set technique_id to empty string (keep technique_name only if evidence is strong).
4) Keep only items with explicit evidence.
Return JSON only.

Output JSON schema name: self_correct_cti_items
"""


def self_correct_llm(
    full_text: str,
    techniques: List[Dict[str, Any]],
    indicators: List[Dict[str, Any]],
    allowed_ids: List[str],
    cache_dir: Optional[Path] = None,
    model: Optional[str] = None,
    backend: str = "auto",
) -> Dict[str, Any]:
    cache_dir = cache_dir or Path("runs/cache/agent_llm")
    cache_dir.mkdir(parents=True, exist_ok=True)

    full_text = (full_text or "").strip()
    if not full_text:
        return {"techniques": [], "indicators": []}

    key_parts = ["self_correct", backend, model or "", str(hash(full_text)), str(len(techniques)), str(len(indicators))]
    cached = load_cache(cache_dir, key_parts)
    if cached is not None:
        return cached

    payload = {
        "cti_text": full_text[:60000],  # keep bounded
        "techniques": techniques,
        "indicators": indicators,
        "allowed_ids": allowed_ids[:8000],
    }

    prompt = SYSTEM + "\n\nINPUT:\n" + str(payload)

    parsed = call_llm(prompt, schema=SELF_CORRECT_SCHEMA, backend=backend, model=model)

    save_cache(cache_dir, key_parts, parsed)
    return parsed
