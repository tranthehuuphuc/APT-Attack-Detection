from __future__ import annotations

import json
import re
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

def extract_first_json_object(text: str) -> str:
    """Extract first {...} JSON object from a text blob.
    
    Returns empty dict string if no JSON found (graceful degradation).
    """
    m = _JSON_RE.search(text)
    if not m:
        logger.warning(f"No JSON object found in LLM output (length={len(text)}). Returning empty structure.")
        # Return empty valid structure instead of raising
        return '{"techniques": [], "indicators": []}'
    return m.group(0)

def parse_json(text: str) -> Dict[str, Any]:
    """Parse JSON from text, with fallback to empty structure."""
    try:
        raw = extract_first_json_object(text)
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error: {e}. Returning empty structure.")
        return {"techniques": [], "indicators": []}
    except Exception as e:
        logger.warning(f"Unexpected error parsing JSON: {e}. Returning empty structure.")
        return {"techniques": [], "indicators": []}

def minimal_validate(parsed: Dict[str, Any], schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Lightweight validation to protect pipeline from malformed outputs.

    We keep it minimal on purpose (no heavy jsonschema dependency).
    Returns empty structure if validation fails instead of crashing.
    """
    if not isinstance(parsed, dict):
        logger.warning(f"Parsed output is not a dict (type={type(parsed)}). Returning empty structure.")
        return {"techniques": [], "indicators": []}

    # Common schemas in this repo:
    # - EXTRACT_SCHEMA expects: {"techniques": [...], "indicators": [...]}
    # - SELF_CORRECT_SCHEMA expects: {"techniques": [...], "indicators": [...]}
    if "techniques" in parsed and "indicators" in parsed:
        # Ensure they are lists
        if not isinstance(parsed["techniques"], list):
            logger.warning("techniques is not a list. Converting/creating empty.")
            parsed["techniques"] = []
        if not isinstance(parsed["indicators"], list):
            logger.warning("indicators is not a list. Converting/creating empty.")
            parsed["indicators"] = []
        return parsed

    # Backwards compat for older shape: {"items":[...]}
    if "items" in parsed and isinstance(parsed["items"], list):
        return parsed

    # If shape doesn't match, try to salvage or return empty
    logger.warning(f"Unexpected JSON shape for schema={schema_name or 'unknown'}; keys={list(parsed.keys())}. Returning empty structure.")
    return {"techniques": [], "indicators": []}

