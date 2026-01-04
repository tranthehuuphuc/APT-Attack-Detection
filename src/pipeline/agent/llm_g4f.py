from __future__ import annotations

from typing import Any, Dict, Optional

from src.pipeline.agent.json_repair import parse_json, minimal_validate

def call_g4f(prompt: str, schema: Optional[dict] = None, model: Optional[str] = None) -> Dict[str, Any]:
    """Educational fallback backend using g4f.

    Notes:
    - g4f does NOT support OpenAI structured outputs, so we enforce JSON by prompt and repair/validate client-side.
    - schema is accepted for interface parity, but validation is lightweight.
    - Uses Blackbox provider to avoid authentication requirements
    """
    try:
        import g4f  # type: ignore
        from g4f.Provider import Blackbox, DeepInfra, Pizzagpt
    except Exception as e:
        raise RuntimeError("g4f is not installed or failed to import. Install via: pip install -r requirements/g4f.txt") from e

    chosen_model = model or "gpt-4o"

    if schema is not None:
        # Encourage strict JSON output
        prompt = (
            "Return ONLY valid JSON (no markdown, no commentary).\n"
            "If you cannot find evidence, return empty lists in the JSON.\n\n"
            + prompt
        )

    # Try multiple providers that don't require authentication
    providers = [Blackbox, DeepInfra, Pizzagpt]
    last_error = None
    
    for provider in providers:
        try:
            resp = g4f.ChatCompletion.create(
                model=chosen_model,
                messages=[{"role": "user", "content": prompt}],
                provider=provider,
            )
            break  # Success, exit loop
        except Exception as e:
            last_error = e
            continue  # Try next provider
    else:
        # All providers failed
        raise RuntimeError(f"All g4f providers failed. Last error: {last_error}")

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

