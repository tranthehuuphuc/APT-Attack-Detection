from __future__ import annotations

import os
from typing import Any


def get_client() -> Any:
    """Return an OpenAI client.

    The SDK will read OPENAI_API_KEY from env; we pass explicitly for clarity.
    """
    # Import lazily so non-agent flows can run without installing openai.
    from openai import OpenAI  # type: ignore

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def get_model(default: str = "gpt-4o-mini") -> str:
    return os.getenv("OPENAI_MODEL", default)
