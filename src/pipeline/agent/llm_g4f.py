from __future__ import annotations

from typing import Any, Dict, Optional

from src.pipeline.agent.json_repair import parse_json, minimal_validate

def call_g4f(prompt: str, schema: Optional[dict] = None, model: Optional[str] = None) -> Dict[str, Any]:
    """Educational fallback backend using g4f.

    Notes:
    - g4f does NOT support OpenAI structured outputs, so we enforce JSON by prompt and repair/validate client-side.
    - schema is accepted for interface parity, but validation is lightweight.
    - Uses auto provider selection to avoid authentication issues
    """
    try:
        import g4f  # type: ignore
    except Exception as e:
        raise RuntimeError("g4f is not installed or failed to import. Install via: pip install -r requirements/g4f.txt") from e

    chosen_model = model or "gpt-3.5-turbo"  # Use more compatible model

    if schema is not None:
        # Encourage strict JSON output
        prompt = (
            "Return ONLY valid JSON (no markdown, no commentary).\n"
            "If you cannot find evidence, return empty lists in the JSON.\n\n"
            + prompt
        )

    try:
        # Use simple approach - let g4f auto-select working provider
        resp = g4f.ChatCompletion.create(
            model=chosen_model,
            messages=[{"role": "user", "content": prompt}],
            ignore_working=True,  # Skip provider working checks
            ignore_stream=True,   # Get full response
        )
    except Exception as e:
        # Fallback: try with minimal options
        try:
            resp = g4f.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e2:
            raise RuntimeError(f"g4f failed: {e}. Fallback also failed: {e2}")

    # g4f may return str or dict-like
    if isinstance(resp, str):
        text = resp
    elif isinstance(resp, dict):
        # best effort
        text = resp.get("choices", [{}])[0].get("message", {}).get("content", "") or str(resp)
    else:
        text = str(resp)

    if schema is None:
        return {"text": text}

    parsed = parse_json(text)
    return minimal_validate(parsed, schema_name=(schema.get("name") if isinstance(schema, dict) else None))


