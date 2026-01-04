from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from src.pipeline.agent.attack_knowledge import Technique
from src.pipeline.agent.cache import load_cache, save_cache
from src.pipeline.agent.llm_client import get_client
from src.pipeline.agent.llm_utils import call_with_retry


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    num = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        num += x * y
        na += x * x
        nb += y * y
    if na <= 0 or nb <= 0:
        return 0.0
    return num / math.sqrt(na * nb)


@dataclass
class EmbeddingTechniqueRetriever:
    """Embedding-based retriever for ATT&CK techniques.

    - Uses OpenAI embeddings to index technique texts.
    - Caches both technique embeddings and query embeddings on disk.
    - Falls back gracefully if OPENAI_API_KEY is missing.
    """

    techniques: List[Technique]
    embedding_model: str = "text-embedding-3-small"
    cache_dir: Path = Path("runs/cache/stix_embed")

    def __post_init__(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.cache_dir / f"techniques_{self.embedding_model}.json"
        self._vec_by_tid: Dict[str, List[float]] = {}
        self._load_or_build_index()

    def _load_or_build_index(self) -> None:
        if self._index_path.exists():
            try:
                obj = json.loads(self._index_path.read_text(encoding="utf-8"))
                self._vec_by_tid = {k: v for k, v in obj.get("vec_by_tid", {}).items()}
                return
            except Exception:
                pass

        # Build index (lazy): only if we have a key.
        if not os.getenv("OPENAI_API_KEY"):
            self._vec_by_tid = {}
            return

        client = get_client()
        texts = []
        tids = []
        for t in self.techniques:
            tids.append(t.tid)
            texts.append(f"{t.tid}\n{t.name}\n{t.description}".strip())

        def _do() -> Dict[str, List[float]]:
            resp = client.embeddings.create(model=self.embedding_model, input=texts)
            vecs = [d.embedding for d in resp.data]
            return {tid: vec for tid, vec in zip(tids, vecs)}

        self._vec_by_tid = call_with_retry(_do)
        self._index_path.write_text(
            json.dumps({"embedding_model": self.embedding_model, "vec_by_tid": self._vec_by_tid}),
            encoding="utf-8",
        )

    def _embed_query(self, text: str) -> List[float]:
        text = (text or "").strip()
        if not text or not os.getenv("OPENAI_API_KEY"):
            return []

        q_cache_dir = self.cache_dir / "queries"
        key_parts = ["q", self.embedding_model, text]
        cached = load_cache(q_cache_dir, key_parts)
        if cached is not None:
            return cached

        client = get_client()

        def _do() -> List[float]:
            r = client.embeddings.create(model=self.embedding_model, input=text)
            return r.data[0].embedding

        vec = call_with_retry(_do)
        save_cache(q_cache_dir, key_parts, vec)
        return vec

    def top_k(self, text: str, k: int = 8) -> List[Technique]:
        if not self._vec_by_tid:
            return []
        qv = self._embed_query(text)
        if not qv:
            return []

        scored: List[Tuple[float, Technique]] = []
        for t in self.techniques:
            dv = self._vec_by_tid.get(t.tid)
            if not dv:
                continue
            s = _cosine(qv, dv)
            scored.append((s, t))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:k]]
