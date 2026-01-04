from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

def extract_first_json_object(text: str) -> str:
    """Extract first {...} JSON object from a text blob."""
    m = _JSON_RE.search(text)
    if not m:
        raise ValueError("No JSON object found in LLM output")
    return m.group(0)

def parse_json(text: str) -> Dict[str, Any]:
    raw = extract_first_json_object(text)
    return json.loads(raw)

def minimal_validate(parsed: Dict[str, Any], schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Lightweight validation to protect pipeline from malformed outputs.

    We keep it minimal on purpose (no heavy jsonschema dependency).
    """
    if not isinstance(parsed, dict):
        raise ValueError("Parsed output is not a JSON object")

    # Common schemas in this repo:
    # - EXTRACT_SCHEMA expects: {"techniques": [...], "indicators": [...]}
    # - SELF_CORRECT_SCHEMA expects: {"techniques": [...], "indicators": [...]}
    if "techniques" in parsed and "indicators" in parsed:
        if not isinstance(parsed["techniques"], list) or not isinstance(parsed["indicators"], list):
            raise ValueError("techniques/indicators must be lists")
        return parsed

    # Backwards compat for older shape: {"items":[...]}
    if "items" in parsed and isinstance(parsed["items"], list):
        return parsed

    raise ValueError(f"Unexpected JSON shape for schema={schema_name or 'unknown'}; keys={list(parsed.keys())}")
