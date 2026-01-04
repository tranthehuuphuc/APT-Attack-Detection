# APT Attack Detection (Provenance Graph + TTP + GNN)

This repo provides 3 pipelines:
1) Training (DARPA TC offline)
2) Hunting (Ubuntu auditd -> provenance -> subgraph -> predict)
3) CTI Agent (RSS -> ATT&CK techniques -> query graphs)

Engine code is expected at: `src/engine/graph_matcher/engine_repo/`.
Use `scripts/bootstrap_engine.sh` to clone it.

## Quickstart

### 0) Install deps

```bash
python3.8 -m venv .venv
source .venv/bin/activate
pip install -r requirements/hunting.txt
pip install -r requirements/agent.txt
```

### 1) CTI Agent (LLM mode) → `runs/cti/seeds.json`

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-4o-mini"  # optional

python -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-cti runs/cti \
  --out-qg data/query_graphs \
  --out-seeds runs/cti/seeds.json \
  --llm auto

# Optional: stronger STIX hint retrieval
# - lexical (default): no extra cost
# - embed: uses OpenAI embeddings to retrieve top-k techniques per chunk
#   (cached under runs/cache/stix_embed)
#
# python -m src.pipeline.agent.main ... --retrieval embed

# Optional: tune retry policy for OpenAI calls
# export OPENAI_MAX_RETRIES=6
# export OPENAI_RETRY_BASE_SLEEP=0.8
# export OPENAI_RETRY_MAX_SLEEP=12
```

Outputs:
- `runs/cti/*.jsonl` (saved CTI items)
- `runs/cti/seeds.json` (techniques + indicators)
- `data/query_graphs/<Txxxx>.json` (query graph templates)

### 2) Hunting (use CTI seeds)

```bash
python -m src.pipeline.hunting.main \
  --dataset cadets \
  --events runs/events/events.jsonl \
  --checkpoint runs/checkpoints/cadets_demo.pt \
  --query-name qg \
  --cti-seeds runs/cti/seeds.json
```


## Educational fallback: g4f backend (no API key)

If you do not have an OpenAI API key and your supervisor/instructor allows an educational backend, you can run the LLM Agent with **g4f**.

### Install
```bash
pip install -r requirements/g4f.txt
```

### Run Agent with g4f
```bash
python -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --llm-backend g4f
```

Notes:
- g4f does **not** support OpenAI Structured Outputs. The agent enforces JSON with prompt + client-side JSON repair/validation.
- For reproducible experiments, prefer the official OpenAI backend when possible.
