from __future__ import annotations

from typing import Any, Dict, Optional

from src.pipeline.agent.llm_utils import call_with_retry

def call_llm(prompt: str, schema: Optional[dict] = None, backend: str = "auto", model: Optional[str] = None) -> Dict[str, Any]:
    """Unified LLM caller.

    backends:
      - openai: OpenAI Responses API with json_schema (preferred)
      - g4f: educational fallback (no structured outputs; requires JSON repair)
      - off: raises
      - auto: try openai, else g4f

    Returns: parsed Python dict matching the provided schema (when schema is not None).
    """
    backend = (backend or "auto").lower()

    if backend == "off":
        raise RuntimeError("LLM backend is disabled")

    def _openai():
        from src.pipeline.agent.llm_openai import call_openai
        return call_openai(prompt, schema=schema, model=model)

    def _g4f():
        from src.pipeline.agent.llm_g4f import call_g4f
        return call_g4f(prompt, schema=schema, model=model)

    if backend == "openai":
        return call_with_retry(_openai)

    if backend == "g4f":
        return call_with_retry(_g4f)

    if backend == "auto":
        try:
            return call_with_retry(_openai)
        except Exception:
            return call_with_retry(_g4f)

    raise ValueError(f"Unknown LLM backend: {backend}")
