from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import json
import re

import math
from collections import Counter, defaultdict

@dataclass
class Technique:
    tid: str
    name: str
    description: str

def load_attack_techniques(stix_json_path: Path) -> List[Technique]:
    obj = json.loads(stix_json_path.read_text(encoding="utf-8"))
    techniques: List[Technique] = []
    for it in obj.get("objects", []):
        if it.get("type") != "attack-pattern":
            continue
        tid = ""
        for ref in it.get("external_references", []):
            if ref.get("source_name") == "mitre-attack" and ref.get("external_id","").startswith("T"):
                tid = ref.get("external_id")
                break
        if not tid:
            continue
        techniques.append(Technique(tid=tid, name=it.get("name",""), description=it.get("description","") or ""))
    return techniques


def _tokenize(s: str) -> List[str]:
    return [t for t in re.findall(r"[a-zA-Z0-9_\-]{2,}", (s or "").lower())]


class TechniqueRetriever:
    """Lightweight lexical retriever (no extra deps).

    Purpose: provide a small STIX hint set (top-k techniques) per chunk to reduce LLM hallucinations.
    """

    def __init__(self, techniques: List[Technique]):
        self.techniques = techniques
        self._df = Counter()
        self._doc_tokens: Dict[str, Counter] = {}
        for t in techniques:
            toks = _tokenize(f"{t.tid} {t.name} {t.description}")
            c = Counter(toks)
            self._doc_tokens[t.tid] = c
            for tok in set(toks):
                self._df[tok] += 1
        self._N = max(1, len(techniques))

    def _score(self, q: Counter, doc: Counter) -> float:
        # TF-IDF-ish cosine with idf smoothing
        num = 0.0
        qnorm = 0.0
        dnorm = 0.0
        for tok, qt in q.items():
            idf = math.log((self._N + 1) / (self._df.get(tok, 0) + 1)) + 1.0
            qv = qt * idf
            dv = doc.get(tok, 0) * idf
            num += qv * dv
            qnorm += qv * qv
        for tok, dt in doc.items():
            idf = math.log((self._N + 1) / (self._df.get(tok, 0) + 1)) + 1.0
            dv = dt * idf
            dnorm += dv * dv
        if qnorm <= 0 or dnorm <= 0:
            return 0.0
        return num / math.sqrt(qnorm * dnorm)

    def top_k(self, text: str, k: int = 8) -> List[Technique]:
        q = Counter(_tokenize(text))
        scored: List[Tuple[float, Technique]] = []
        for t in self.techniques:
            s = self._score(q, self._doc_tokens[t.tid])
            if s > 0:
                scored.append((s, t))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:k]]

TID_RE = re.compile(r"\bT\d{4}(?:\.\d{3})?\b")

def exact_id_hits(text: str) -> List[str]:
    return list(set(TID_RE.findall(text)))
