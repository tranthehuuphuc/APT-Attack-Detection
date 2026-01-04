# 🔍 CTI Agent Pipeline Review - COMPLETE

## ✅ Review Results

### **Pipeline Đúng Chưa?** → ✅ **ĐÚNG**

Pipeline hiện tại hoàn chỉnh với cả 6 bước Map-Reduce.

---

## 📥 INPUT (Đã Bổ Sung PDF)

### **Trước** (Old):
- ❌ Chỉ RSS feeds

### **Sau** (New - Updated):
- ✅ **RSS Feeds**: `--rss-file` hoặc `--rss`
- ✅ **PDF Files**: `--pdf-dir` (MỚI!)

**Sử dụng**:
```bash
# RSS only
python3 -m src.pipeline.agent.main --rss-file data/cti_reports/rss_seeds.txt --llm-backend g4f

# PDF only  
python3 -m src.pipeline.agent.main --pdf-dir data/cti_reports/pdfs --llm-backend g4f

# Both RSS + PDF
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --pdf-dir data/cti_reports/pdfs \
  --llm-backend g4f
```

---

## 📤 OUTPUT (Confirmed)

### ✅ **1. Seeds JSON**
**File**: `runs/cti/seeds.json`

**Structure**:
```json
{
  "techniques": [
    {
      "technique_id": "T1566.001",
      "name": "Spearphishing Attachment", 
      "confidence": 0.85,
      "tactics": ["initial-access"]
    },
    ...
  ],
  "indicators": [
    {
      "type": "file_hash",
      "value": "d41d8cd98f00b204e9800998ecf8427e"
    },
    ...
  ]
}
```

**Location**: Line 172 trong main.py
```python
write_json(out_seeds, {
    "techniques": all_techniques, 
    "indicators": all_indicators
})
```

### ✅ **2. Query Graphs**
**Directory**: `data/query_graphs/`

**Files**: Multiple JSON files (1 per top technique)
- `T1566_001.json`
- `T1059_001.json`
- `T1105.json`
- ...

**Location**: Lines 149-153 trong main.py
```python
for c in sorted(final_t, key=lambda x: float(x.get("confidence", 0)), reverse=True)[:3]:
    tid = (c.get("technique_id") or "").strip()
    if tid:
        qg = build_simple_query_graph(tid)
        export_query_graph_json(Path(args.out_qg), qg)
```

**Purpose**: Used by hunting phase để match against provenance graphs

---

## 🔄 Complete Pipeline Flow (Updated)

```
┌─────────────────────────────────────────────────┐
│ INPUT                                            │
│ - RSS Feeds (--rss-file)                        │
│ - PDF Files (--pdf-dir)         [NEW!]          │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ STEP 1: INGEST                                   │
│ - Fetch RSS → Parse → Extract text              │
│ - Read PDFs → Extract text       [NEW!]         │
│ → List[CTIItem(title, text, link)]              │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ STEP 2: CHUNK                                    │
│ - Split text → chunks (~4K chars)                │
│ → List[str]                                      │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ STEP 3: MAP (LLM per chunk)                     │
│ - Retrieve MITRE hints (RAG)                     │
│ - LLM extract techniques + IOCs                  │
│ → techniques[], indicators[] per chunk           │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ STEP 4: REDUCE                                   │
│ - Merge chunk results                            │
│ - Deduplicate techniques                         │
│ → merged techniques[], indicators[]              │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ STEP 5: SELF-CORRECT (LLM)                      │
│ - Review with full text                          │
│ - Remove false positives                         │
│ → validated results                              │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ STEP 6: QUERY GRAPH GENERATION                  │
│ - Build query graphs for top-3 techniques        │
│ → save to data/query_graphs/*.json              │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│ OUTPUT                                           │
│ ✅ runs/cti/seeds.json                          │
│    {techniques[], indicators[]}                  │
│ ✅ data/query_graphs/*.json                     │
│    Query graphs for hunting                      │
└──────────────────────────────────────────────────┘
```

---

## 📊 Files Changed

### **1. src/pipeline/agent/ingest.py**
**Added**:
- `extract_pdf_text()` - Extract text from PDF
- `ingest_pdfs()` - Process PDF directory

### **2. src/pipeline/agent/main.py**  
**Added**:
- `--pdf-dir` argument
- PDF ingestion logic
- Combines RSS + PDF items

---

## ✅ Summary

| Feature | Status |
|---------|--------|
| **RSS Input** | ✅ Working |
| **PDF Input** | ✅ Added (NEW) |
| **LLM Processing** | ✅ Working (g4f/OpenAI) |
| **Map-Reduce Pattern** | ✅ Implemented |
| **RAG (Retrieval)** | ✅ Lexical + Embedding |
| **Self-Correction** | ✅ Implemented |
| **Output: seeds.json** | ✅ Generated |
| **Output: query graphs** | ✅ Generated (top-3) |

---

## 🎯 Usage Example

```bash
# Complete workflow with PDF
cd ~/apt-detection
source .venv/bin/activate

# 1. Add PDFs
mkdir -p data/cti_reports/pdfs
# Copy your PDF files there

# 2. Run agent
python3 -m src.pipeline.agent.main \
  --pdf-dir data/cti_reports/pdfs \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --out-qg data/query_graphs \
  --llm-backend g4f

# 3. Check outputs
ls runs/cti/seeds.json
ls data/query_graphs/
```

---

**Pipeline**: ✅ **COMPLETE & CORRECT**  
**Inputs**: RSS + PDF ✅  
**Outputs**: seeds.json + query_graphs ✅  
**Ready**: For experiments 🚀
