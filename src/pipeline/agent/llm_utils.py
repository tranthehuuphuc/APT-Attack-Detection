from __future__ import annotations

import os
import random
import time
from typing import Any, Callable, Optional


def _is_retryable_exception(exc: Exception) -> bool:
    """Return True if we should retry the failed API call.

    We avoid importing OpenAI exception classes directly to keep compatibility
    across SDK minor versions.
    """
    name = exc.__class__.__name__.lower()
    msg = str(exc).lower()

    if any(k in name for k in ("ratelimit", "timeout", "apitimeout", "apierror", "serviceunavailable", "internalserver")):
        return True
    if any(k in msg for k in ("rate limit", "timed out", "timeout", "temporarily", "overloaded", "server error", "502", "503", "504")):
        return True
    return False


def call_with_retry(
    fn: Callable[[], Any],
    *,
    max_retries: int = 6,
    base_sleep_s: float = 0.8,
    max_sleep_s: float = 12.0,
    jitter: float = 0.25,
    timeout_s: Optional[float] = None,
) -> Any:
    """Call `fn` with exponential backoff.

    Env overrides:
      - OPENAI_MAX_RETRIES
      - OPENAI_RETRY_BASE_SLEEP
      - OPENAI_RETRY_MAX_SLEEP
    """
    env_max = os.getenv("OPENAI_MAX_RETRIES")
    if env_max:
        try:
            max_retries = int(env_max)
        except Exception:
            pass
    env_base = os.getenv("OPENAI_RETRY_BASE_SLEEP")
    if env_base:
        try:
            base_sleep_s = float(env_base)
        except Exception:
            pass
    env_maxs = os.getenv("OPENAI_RETRY_MAX_SLEEP")
    if env_maxs:
        try:
            max_sleep_s = float(env_maxs)
        except Exception:
            pass

    t0 = time.time()
    last_exc: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            if timeout_s is not None and (time.time() - t0) > timeout_s:
                raise TimeoutError(f"Timed out after {timeout_s}s while retrying OpenAI call")
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt >= max_retries or not _is_retryable_exception(exc):
                raise
            sleep_s = min(max_sleep_s, base_sleep_s * (2 ** attempt))
            sleep_s = max(0.0, sleep_s * (1.0 + random.uniform(-jitter, jitter)))
            time.sleep(sleep_s)

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("OpenAI call failed without exception")
