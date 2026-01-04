# 🤖 CTI Agent Pipeline - Architecture & Data Flow

## Tổng Quan Pipeline

Pipeline CTI Agent xử lý threat intelligence reports qua **4 bước chính** (Map-Reduce pattern với LLM).

---

## 📊 Pipeline Flow Diagram

```
Input → Ingest → Chunk → Map (LLM) → Reduce → Self-Correct → Output
```

---

## 🔄 Chi Tiết Từng Bước

### **Step 1: INGEST - Thu Thập CTI Reports**

**Module**: `src/pipeline/agent/ingest.py`

**Input**:
- RSS feed URLs (từ `--rss-file`)
- Per-source limit (số reports mỗi feed)
- Timeout settings

**Process**:
1. Fetch RSS feeds
2. Parse XML/Atom feeds
3. Download report content (HTML/text)
4. Clean & extract main text
5. Create CTI items với metadata

**Output**: `List[CTIItem]`
```python
CTIItem {
    title: str        # "APT29 Threat Analysis"
    text: str         # Full report text content
    url: str          # Source URL
    published: str    # Publish date
}
```

**Saved to**: `runs/cti/cti_*.json`

---

### **Step 2: CHUNK - Chia Nhỏ Text**

**Module**: `src/pipeline/agent/chunking.py`

**Input**: CTI text (~10,000+ chars)

**Parameters**:
- `max_chars`: 4000 (LLM context limit)
- `overlap`: 400 (maintain context between chunks)

**Process**:
1. Split text by paragraphs
2. Combine into chunks ≤ max_chars
3. Add overlap between chunks

**Output**: `List[str]` - các chunks
```python
[
    "Chunk 1: APT29 has been observed...",
    "Chunk 2: The malware uses PowerShell...",
    "Chunk 3: Indicators include file hash..."
]
```

**Why chunk?**: LLM có giới hạn context window (vài nghìn tokens)

---

### **Step 3: MAP - Extract Per Chunk (LLM)**

**Module**: `src/pipeline/agent/map_step_llm.py`

**Input per chunk**:
```python
{
    "text": "Chunk content...",
    "stix_hint": [
        {"tid": "T1566.001", "name": "Spearphishing Attachment"},
        {"tid": "T1059.001", "name": "PowerShell"}
    ]
}
```

**STIX Hint** (Retrieval-Augmented Generation):
- **Lexical retrieval**: TF-IDF matching
- **Embedding retrieval** (if OpenAI): Semantic similarity
- Top-K techniques liên quan được gợi ý cho LLM

**LLM Prompt**:
```
You are a cybersecurity threat analyst.
Extract MITRE ATT&CK techniques and IOCs from this CTI report.

Use these MITRE techniques as reference:
- T1566.001: Spearphishing Attachment
- T1059.001: PowerShell
...

Report text:
[chunk content]

Return JSON:
{
  "techniques": [{"technique_id": "T1566.001", "confidence": 0.85}],
  "indicators": [{"type": "file_hash", "value": "abc123..."}]
}
```

**LLM Call**: `call_g4f()` hoặc `call_openai()`

**Output per chunk**:
```json
{
  "techniques": [
    {"technique_id": "T1566.001", "name": "Spearphishing", "confidence": 0.85},
    {"technique_id": "T1059.001", "name": "PowerShell", "confidence": 0.90}
  ],
  "indicators": [
    {"type": "file_hash", "value": "d41d8cd98f00b204e9800998ecf8427e"},
    {"type": "ip_address", "value": "192.0.2.1"}
  ]
}
```

**Lưu ý**: Mỗi chunk xử lý độc lập → có thể duplicate

---

### **Step 4: REDUCE - Gộp Kết Quả**

**Module**: `src/pipeline/agent/reduce.py` → `reduce_llm()`

**Input**: Results từ tất cả chunks
```python
[
    {"techniques": [T1, T2], "indicators": [I1, I2]},  # Chunk 1
    {"techniques": [T2, T3], "indicators": [I2, I3]},  # Chunk 2
    {"techniques": [T1, T4], "indicators": [I4]},      # Chunk 3
]
```

**Process**:
1. Collect all techniques from all chunks
2. Detect duplicates (same technique_id)
3. Merge duplicate techniques:
   - Keep highest confidence
   - Or average confidences
4. Deduplicate indicators

**Output**: Merged result
```json
{
  "techniques": [
    {"technique_id": "T1566.001", "confidence": 0.85},
    {"technique_id": "T1059.001", "confidence": 0.90},
    {"technique_id": "T1105", "confidence": 0.75}
  ],
  "indicators": [
    {"type": "file_hash", "value": "d41d8cd98f00b204e9800998ecf8427e"},
    {"type": "ip_address", "value": "192.0.2.1"},
    ...
  ]
}
```

---

### **Step 5: SELF-CORRECT - Validation (LLM)**

**Module**: `src/pipeline/agent/self_correct_llm.py`

**Input**:
- Original full text
- Extracted techniques
- Extracted indicators
- Valid MITRE technique IDs

**Purpose**: Quality control - LLM kiểm tra lại kết quả

**LLM Prompt**:
```
Review these extracted MITRE techniques from the report.
Remove false positives and add any missed techniques.

Original report: [full text]

Current extractions: [techniques list]

Valid MITRE IDs: [T1xxx, T2yyy, ...]

Return corrected JSON.
```

**Output**: Cleaned/corrected results

---

### **Step 6: QUERY GRAPH Generation**

**Module**: `src/pipeline/agent/query_graph.py`

**Input**: Top techniques (highest confidence)

**Process**:
1. For each top-3 technique
2. Build query graph structure:
   ```json
   {
     "technique_id": "T1566.001",
     "nodes": [...],
     "edges": [...]
   }
   ```
3. Save to `data/query_graphs/`

**Purpose**: Query graphs dùng cho hunting phase

---

## 📤 Final Output

### **seeds.json**
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
    {"type": "file_hash", "value": "abc123..."},
    {"type": "ip_address", "value": "192.0.2.1"},
    ...
  ]
}
```

**Location**: `runs/cti/seeds.json`

### **Query Graphs**
- Multiple JSON files in `data/query_graphs/`
- One per top technique
- Used by hunting engine

---

## 🔀 Pipeline Variants

### **With LLM** (llm_enabled=True)
```
Ingest → Chunk → [Retrieval + Map(LLM)] → Reduce(LLM) → Self-Correct(LLM) → Output
```
- Uses: g4f, OpenAI, or other LLM
- Better accuracy
- Extracts indicators

### **Baseline** (llm_enabled=False)
```
Ingest → Chunk → Map(TF-IDF) → Reduce → Self-Check → Output
```
- No LLM
- Lexical matching only
- Faster but less accurate

---

## 📥 Input/Output Summary

| Step | Input | Output | Size |
|------|-------|--------|------|
| **Ingest** | RSS URLs | CTIItem[] | ~50 items |
| **Chunk** | CTIItem.text | str[] | 3-5 chunks/item |
| **Map** | chunk + hints | techniques+indicators | per chunk |
| **Reduce** | chunk_results[] | merged results | per CTI item |
| **Self-Correct** | full_text + results | cleaned results | final |
| **Final** | all_items | seeds.json | 1 file |

---

## 🔧 Key Parameters

```python
# From configs/agent.yaml
chunk_size_chars: 2500          # Text chunk size
llm_chunk_max_chars: 4000       # LLM context limit
llm_chunk_overlap: 400          # Overlap between chunks
llm_stix_hint_k: 10            # Top-K MITRE hints
top_k_retrieval: 6             # Retrieval top-K
min_confidence: 0.35           # Minimum confidence threshold
```

---

## 🎯 Example Full Flow

**Input**: RSS feed → 1 threat report về APT29

```
1. INGEST
   → CTIItem{title: "APT29 Analysis", text: "...10,000 chars...", ...}

2. CHUNK
   → [chunk1(4000 chars), chunk2(4000 chars), chunk3(2000 chars)]

3. MAP (per chunk)
   Chunk1 + hints[T1566, T1059, ...] → LLM → {T1566.001, T1059.001}
   Chunk2 + hints[T1105, T1071, ...] → LLM → {T1105, T1071.001}
   Chunk3 + hints[T1003, T1082, ...] → LLM → {T1003.001, T1082}

4. REDUCE
   Merge chunks → {T1566.001, T1059.001, T1105, T1071.001, T1003.001, T1082}

5. SELF-CORRECT
   Review with full text → Keep 5, remove 1 false positive
   → Final: {T1566.001, T1059.001, T1105, T1071.001, T1003.001}

6. OUTPUT
   seeds.json: {"techniques": [...5], "indicators": [...8]}
   query_graphs: [T1566.json, T1059.json, T1105.json]
```

---

## 💡 Design Rationale

**Why Map-Reduce?**
- CTI reports too long for single LLM call
- Parallel processing possible
- Reduces hallucinations (smaller context)

**Why Retrieval hints?**
- 1000+ MITRE techniques → overwhelming
- Top-K matching → focused extraction
- Better accuracy with context

**Why Self-Correct?**
- LLM can make mistakes
- Second pass catches false positives
- Validates against MITRE ATT&CK

---

**Status**: ✅ **Complete pipeline documentation**  
**Next**: Use this for research/thesis documentation 📝
