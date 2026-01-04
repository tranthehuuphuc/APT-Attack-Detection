from __future__ import annotations

from typing import Any, Dict, Optional
import logging

from src.pipeline.agent.json_repair import parse_json, minimal_validate

logger = logging.getLogger(__name__)

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
        # More explicit JSON enforcement
        prompt = (
            "You must return ONLY a valid JSON object. No explanations, no markdown, no code blocks.\n"
            "Format: {\"techniques\": [...], \"indicators\": [...]}\n"
            "If you find nothing, return: {\"techniques\": [], \"indicators\": []}\n\n"
            + prompt
        )

    try:
        # Use simple approach - let g4f auto-select working provider
        logger.debug("Calling g4f with model: %s, prompt length: %d", chosen_model, len(prompt))
        
        resp = g4f.ChatCompletion.create(
            model=chosen_model,
            messages=[{"role": "user", "content": prompt}],
            ignore_working=True,  # Skip provider working checks
            ignore_stream=True,   # Get full response
        )
        
        # Log actual response for debugging
        logger.debug("g4f response type: %s, length: %d", type(resp).__name__, len(str(resp)) if resp else 0)
        
    except Exception as e:
        logger.warning("g4f primary call failed: %s. Trying fallback.", e)
        # Fallback: try with minimal options
        try:
            resp = g4f.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as e2:
            logger.error("g4f fallback also failed: %s", e2)
            raise RuntimeError(f"g4f failed: {e}. Fallback also failed: {e2}")

    # g4f may return str or dict-like
    if isinstance(resp, str):
        text = resp
    elif isinstance(resp, dict):
        # best effort
        text = resp.get("choices", [{}])[0].get("message", {}).get("content", "") or str(resp)
    else:
        text = str(resp)

    # Log what we got
    logger.info("g4f returned %d chars: %s", len(text), text[:200] if len(text) > 200 else text)

    if schema is None:
        return {"text": text}

    parsed = parse_json(text)
    return minimal_validate(parsed, schema_name=(schema.get("name") if isinstance(schema, dict) else None))



