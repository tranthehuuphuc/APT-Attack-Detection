from __future__ import annotations

from typing import Any, Dict, Optional

from src.pipeline.agent.llm_client import get_client, get_model

def call_openai(prompt: str, schema: Optional[dict] = None, model: Optional[str] = None) -> Dict[str, Any]:
    """Call OpenAI Responses API. If schema is provided, enforces json_schema."""
    client = get_client()
    model = model or get_model()

    if schema is None:
        resp = client.responses.create(
            model=model,
            input=[{"role": "user", "content": prompt}],
        )
        return {"text": resp.output_text}

    resp = client.responses.create(
        model=model,
        input=[{"role": "user", "content": prompt}],
        response_format={"type": "json_schema", "json_schema": schema},
    )
    return resp.output_parsed
