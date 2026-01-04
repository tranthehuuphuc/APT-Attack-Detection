from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.pipeline.agent.schemas_llm import EXTRACT_SCHEMA
from src.pipeline.agent.cache import load_cache, save_cache
from src.pipeline.agent.llm_router import call_llm


SYSTEM = """You extract MITRE ATT&CK techniques (TTPs) and concrete indicators from CTI text.

Constraints:
1) Only output items that have explicit evidence in the given chunk.
2) evidence.span_text MUST be an exact substring of the chunk.
3) start_char/end_char are character offsets for span_text within the chunk (0-indexed, end exclusive).
4) If you mention technique_id, it must match ^T\\d{4}(?:\\.\\d{3})?$.
5) Prefer technique_id from the hint list when applicable; otherwise leave technique_id as an empty string.
6) Keep outputs concise. Return JSON only.

Output JSON schema name: extract_cti_ttps_indicators
"""


def _hint_text(stix_hint: List[Dict[str, str]]) -> str:
    if not stix_hint:
        return ""
    lines = [f"- {it.get('tid')}: {it.get('name')}" for it in stix_hint if it.get("tid")]
    return "Possible techniques (STIX hint):\n" + "\n".join(lines)


def map_chunk_llm(
    chunk_text: str,
    stix_hint: Optional[List[Dict[str, str]]] = None,
    cache_dir: Optional[Path] = None,
    model: Optional[str] = None,
    backend: str = "auto",
) -> Dict[str, Any]:
    """Map step (LLM): extract techniques + indicators from one chunk.

    backend:
      - openai (preferred, structured outputs)
      - g4f (educational fallback, uses JSON repair/validate)
      - auto (try openai else g4f)
    """
    cache_dir = cache_dir or Path("runs/cache/agent_llm")
    cache_dir.mkdir(parents=True, exist_ok=True)

    chunk_text = (chunk_text or "").strip()
    if not chunk_text:
        return {"techniques": [], "indicators": []}

    key_parts = ["map", backend, model or "", str(hash(chunk_text))]
    cached = load_cache(cache_dir, key_parts)
    if cached is not None:
        return cached

    hint = _hint_text(stix_hint or [])
    user = "\n\n".join([hint, "CTI CHUNK:\n<<<" + chunk_text + ">>>"]).strip()
    prompt = SYSTEM + "\n\n" + user

    parsed = call_llm(prompt, schema=EXTRACT_SCHEMA, backend=backend, model=model)

    save_cache(cache_dir, key_parts, parsed)
    return parsed
