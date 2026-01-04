from __future__ import annotations

from typing import List


def chunk_text(text: str, max_chars: int = 4000, overlap: int = 400) -> List[str]:
    """Simple character-based chunking with overlap.

    We keep this dependency-free and deterministic.
    """
    s = (text or "").strip()
    if not s:
        return []
    max_chars = max(256, int(max_chars))
    overlap = max(0, min(int(overlap), max_chars // 2))

    chunks: List[str] = []
    i = 0
    n = len(s)
    while i < n:
        j = min(n, i + max_chars)
        chunks.append(s[i:j])
        if j >= n:
            break
        i = max(0, j - overlap)
    return chunks
