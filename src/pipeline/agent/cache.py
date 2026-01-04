from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional


def _key(parts: list[str]) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update((p or "").encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def load_cache(cache_dir: Path, key_parts: list[str]) -> Optional[Any]:
    p = cache_dir / f"{_key(key_parts)}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_cache(cache_dir: Path, key_parts: list[str], obj: Any) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    p = cache_dir / f"{_key(key_parts)}.json"
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return p
