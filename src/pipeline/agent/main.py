from __future__ import annotations
import argparse
from pathlib import Path
import logging
import textwrap
from typing import List

from src.common.logging import setup_logging
from src.common.config import load_yaml
from src.common.io import write_json
from src.pipeline.agent.ingest import ingest_sources, save_items
from src.pipeline.agent.attack_knowledge import load_attack_techniques, TechniqueRetriever
from src.pipeline.agent.embedding_retriever import EmbeddingTechniqueRetriever
from src.pipeline.agent.map_step import map_chunk
from src.pipeline.agent.self_check import self_check
from src.pipeline.agent.reduce import reduce_candidates, reduce_llm
from src.pipeline.agent.chunking import chunk_text
from src.pipeline.agent.map_step_llm import map_chunk_llm
from src.pipeline.agent.self_correct_llm import self_correct_llm
from src.pipeline.agent.query_graph import build_simple_query_graph, export_query_graph_json

log = logging.getLogger(__name__)

def _has_openai_key() -> bool:
    import os
    return bool(os.getenv("OPENAI_API_KEY"))


def _has_g4f() -> bool:
    try:
        import g4f  # type: ignore
        return True
    except Exception:
        return False
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rss", nargs="*", default=[])
    ap.add_argument("--rss-file", default="data/cti_reports/rss_seeds.txt")
    ap.add_argument("--per-source-limit", type=int, default=10, help="Max entries per RSS feed (if source is a feed).")
    ap.add_argument("--timeout", type=int, default=20, help="HTTP timeout for CTI fetch.")
    ap.add_argument("--stix", default="data/mitre/enterprise-attack.json")
    ap.add_argument("--out-cti", default="runs/cti")
    ap.add_argument("--out-qg", default="data/query_graphs")
    ap.add_argument("--out-seeds", default="runs/cti/seeds.json")
    ap.add_argument("--configs", default="configs")
    ap.add_argument("--log-level", default="INFO")
    ap.add_argument("--llm", choices=["auto","on","off","openai","g4f"], default="auto")
    ap.add_argument("--llm-backend", choices=["auto","openai","g4f","off"], default=None, help="Explicit LLM backend override (preferred).")
    ap.add_argument(
        "--retrieval",
        choices=["auto", "lexical", "embed", "none"],
        default="auto",
        help="How to build STIX hints for the LLM (auto=embed if key available else lexical).",
    )
    args = ap.parse_args()

    setup_logging(args.log_level)
    cfg = load_yaml(Path(args.configs)/"agent.yaml")
    chunk_size = int(cfg.get("chunk_size_chars", 2500))
    top_k = int(cfg.get("top_k_retrieval", 6))
    min_conf = float(cfg.get("min_confidence", 0.35))
    # LLM backend selection
    # --llm-backend takes precedence; --llm kept for backward compatibility.
    llm_backend = (args.llm_backend or args.llm).lower() if args.llm_backend else args.llm.lower()
    if llm_backend == "on":
        llm_backend = "openai"
    if llm_backend == "off":
        llm_enabled = False
    elif llm_backend == "openai":
        llm_enabled = _has_openai_key()
        if not llm_enabled and (args.llm_backend or args.llm) in ("openai","on"):
            raise RuntimeError("OPENAI_API_KEY is not set but backend=openai was requested")
    elif llm_backend == "g4f":
        llm_enabled = _has_g4f()
        if not llm_enabled:
            raise RuntimeError("g4f is not installed/importable but backend=g4f was requested. Install: pip install -r requirements/g4f.txt")
    elif llm_backend == "auto":
        if _has_openai_key():
            llm_backend = "openai"; llm_enabled = True
        elif _has_g4f():
            llm_backend = "g4f"; llm_enabled = True
        else:
            llm_backend = "off"; llm_enabled = False
    else:
        raise ValueError(f"Unknown llm backend: {llm_backend}")
    llm_model = str(cfg.get("llm_model", "gpt-4o-mini"))
    llm_max_chars = int(cfg.get("llm_chunk_max_chars", 4000))
    llm_overlap = int(cfg.get("llm_chunk_overlap", 400))
    stix_hint_k = int(cfg.get("llm_stix_hint_k", 10))

    rss_urls = list(args.rss)
    rf = Path(args.rss_file)
    if rf.exists():
        rss_urls += [l.strip() for l in rf.read_text(encoding="utf-8").splitlines() if l.strip() and not l.strip().startswith("#")]
    if not rss_urls:
        raise SystemExit("No RSS sources provided.")

    techniques = load_attack_techniques(Path(args.stix))
    valid_ids = {t.tid for t in techniques}
    stix_name_by_id = {t.tid: t.name for t in techniques}
    # Choose retrieval mode for STIX hints
    retrieval_mode = args.retrieval
    if retrieval_mode == "auto":
        # Embedding retrieval requires OpenAI key (we use OpenAI embeddings).
        retrieval_mode = "embed" if (llm_backend == "openai" and llm_enabled and _has_openai_key()) else "lexical"

    lexical_retriever = TechniqueRetriever(techniques)
    embed_model = str(cfg.get("embedding_model", "text-embedding-3-small"))
    embed_retriever = None
    if retrieval_mode == "embed" and (llm_backend == "openai") and _has_openai_key():
        try:
            embed_retriever = EmbeddingTechniqueRetriever(techniques, embedding_model=embed_model)
        except Exception:
            # Fallback to lexical retrieval if embeddings cannot be initialized.
            embed_retriever = None
            retrieval_mode = "lexical"

    items = ingest_sources(rss_urls, per_source_limit=args.per_source_limit, timeout=args.timeout)
    save_items(Path(args.out_cti), items)

    all_techniques: List[dict] = []
    all_indicators: List[dict] = []

    for it in items:
        if llm_enabled:
            chunks = chunk_text(it.text, max_chars=llm_max_chars, overlap=llm_overlap)
            t_chunks: List[List[dict]] = []
            i_chunks: List[List[dict]] = []
            for ch in chunks:
                if retrieval_mode == "none":
                    top = []
                elif retrieval_mode == "embed" and embed_retriever is not None:
                    top = embed_retriever.top_k(ch, k=stix_hint_k)
                else:
                    top = lexical_retriever.top_k(ch, k=stix_hint_k)
                hint = [{"tid": t.tid, "name": t.name} for t in top]
                out = map_chunk_llm(ch, stix_hint=hint, model=llm_model, backend=llm_backend)
                t_chunks.append(out.get("techniques", []) or [])
                i_chunks.append(out.get("indicators", []) or [])
            red = reduce_llm(t_chunks, i_chunks, stix_name_by_id=stix_name_by_id)
            fixed = self_correct_llm(it.text, red["techniques"], red["indicators"], allowed_ids=sorted(valid_ids), model=llm_model, backend=llm_backend)

            final_t = fixed.get("techniques", [])
            final_i = fixed.get("indicators", [])
            all_techniques.extend(final_t)
            all_indicators.extend(final_i)

            # export query graphs for top techniques
            for c in sorted(final_t, key=lambda x: float(x.get("confidence", 0)), reverse=True)[:3]:
                tid = (c.get("technique_id") or "").strip()
                if tid:
                    qg = build_simple_query_graph(tid)
                    export_query_graph_json(Path(args.out_qg), qg)

            log.info("[LLM] CTI '%s' -> techniques: %s", it.title[:80], [c.get("technique_id") for c in final_t[:10]])
        else:
            chunks = [c for c in textwrap.wrap(it.text, width=chunk_size, break_long_words=False, replace_whitespace=False) if c.strip()]
            mapped = []
            for ch in chunks:
                cands = map_chunk(ch, techniques, top_k=top_k)
                cands = self_check(cands, valid_ids, min_conf=min_conf)
                mapped.append(cands)
            final = reduce_candidates(mapped)
            for c in final[:3]:
                qg = build_simple_query_graph(c.tid)
                export_query_graph_json(Path(args.out_qg), qg)
            log.info("[BASELINE] CTI '%s' -> techniques: %s", it.title[:80], [c.tid for c in final[:10]])

    # write seeds.json for hunting
    out_seeds = Path(args.out_seeds)
    out_seeds.parent.mkdir(parents=True, exist_ok=True)
    write_json(out_seeds, {"techniques": all_techniques, "indicators": all_indicators})
    log.info("Wrote CTI seeds: %s (techniques=%d indicators=%d)", out_seeds, len(all_techniques), len(all_indicators))

if __name__ == "__main__":
    main()