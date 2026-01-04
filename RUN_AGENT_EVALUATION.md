# 🤖 CTI LLM Agent - Evaluation Guide

## Mục Tiêu

Chạy và đánh giá CTI Agent với LLM để extract MITRE techniques và IOCs từ threat reports.

---

## 📋 3 Options Thực Tế

| Option | Input | LLM | Cost | Time | Quality |
|--------|-------|-----|------|------|---------|
| **A. MITRE Direct** | MITRE data | None | Free | 5s | Medium |
| **B. PDF + g4f** | PDF files | g4f (free) | Free | 10-30min | Low-Medium |
| **C. PDF + OpenAI** | PDF files | OpenAI | ~$0.10 | 5-10min | High |

---

## ⭐ OPTION A: MITRE-Based (Recommended - No LLM Issues)

### Quick Run

```bash
cd ~/apt-detection
source .venv/bin/activate

# Extract seeds from MITRE ATT&CK (no LLM needed)
python3 scripts/extract_mitre_seeds.py \
  --mitre-file data/mitre/enterprise-attack.json \
  --output runs/cti/seeds.json \
  --num-techniques 25

# Verify
cat runs/cti/seeds.json | python3 -m json.tool | head -50
```

**Kết quả**:
- ✅ 25 MITRE techniques
- ✅ ~20 synthetic IOCs
- ✅ Query graphs (tự động)
- ⏱️ < 5 seconds

**Pros**: Fast, reliable, no LLM issues  
**Cons**: Không demonstrate LLM workflow

---

## 🔧 OPTION B: PDF + g4f (Free LLM)

### Setup

```bash
cd ~/apt-detection
source .venv/bin/activate

# Install PDF support
pip install PyPDF2

# Create PDF directory
mkdir -p data/cti_reports/pdfs
```

### Add Sample PDFs

**Option B1**: Download CTI reports (recommended)
```bash
# Download from CISA
wget -O data/cti_reports/pdfs/cisa_advisory.pdf \
  "https://www.cisa.gov/sites/default/files/publications/..." 

# Or use curl for specific reports
```

**Option B2**: Create sample PDF
```bash
python3 << 'EOF'
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas("data/cti_reports/pdfs/sample_apt.pdf", pagesize=letter)
c.setFont("Helvetica", 12)
c.drawString(100, 750, "APT Threat Report")
c.drawString(100, 730, "Observed: Spearphishing (T1566.001)")
c.drawString(100, 710, "PowerShell execution (T1059.001)")
c.drawString(100, 690, "MD5: d41d8cd98f00b204e9800998ecf8427e")
c.drawString(100, 670, "IP: 192.0.2.1")
c.showPage()
c.save()
print("✅ Sample PDF created")
EOF
```

### Run Agent with g4f

```bash
python3 -m src.pipeline.agent.main \
  --pdf-dir data/cti_reports/pdfs \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --out-qg data/query_graphs \
  --llm-backend g4f \
  --log-level INFO
```

**Expected**: 
- Warning: g4f may fail some extractions
- Result: Partial data in seeds.json
- Time: 10-30 minutes

### Verify Results

```bash
# Check output
cat runs/cti/seeds.json | python3 -m json.tool

# Statistics
python3 << 'EOF'
import json
seeds = json.load(open('runs/cti/seeds.json'))
print(f"✅ Techniques: {len(seeds.get('techniques', []))}")
print(f"✅ Indicators: {len(seeds.get('indicators', []))}")

if len(seeds.get('techniques', [])) == 0:
    print("⚠️  g4f failed to extract. Use Option A or C instead.")
else:
    for t in seeds['techniques'][:5]:
        print(f"  - {t['technique_id']}: {t.get('confidence', 0):.2f}")
EOF
```

---

## 💰 OPTION C: PDF + OpenAI (Best Quality)

### Setup

```bash
# Get API key from: https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-proj-..."

# Verify
echo $OPENAI_API_KEY
```

### Run Agent

```bash
cd ~/apt-detection
source .venv/bin/activate

python3 -m src.pipeline.agent.main \
  --pdf-dir data/cti_reports/pdfs \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --out-qg data/query_graphs \
  --llm-backend openai \
  --log-level INFO
```

**Cost**: ~$0.05-0.15 for 5 PDF reports  
**Time**: 5-10 minutes  
**Quality**: High accuracy

---

## 📊 Evaluation - Assess Results

### 1. Quantitative Metrics

```bash
python3 << 'EOF'
import json
from collections import Counter
from pathlib import Path

seeds = json.load(Path('runs/cti/seeds.json').open())

print("="*70)
print("CTI AGENT EVALUATION REPORT")
print("="*70)

# Basic counts
techs = seeds.get('techniques', [])
inds = seeds.get('indicators', [])

print(f"\n📊 Extraction Statistics:")
print(f"  Total Techniques: {len(techs)}")
print(f"  Total Indicators: {len(inds)}")

# Confidence distribution
if techs:
    confs = [t.get('confidence', 0) for t in techs]
    print(f"\n📈 Confidence Distribution:")
    print(f"  Average: {sum(confs)/len(confs):.3f}")
    print(f"  Min: {min(confs):.3f}")
    print(f"  Max: {max(confs):.3f}")
    
    high = sum(1 for c in confs if c >= 0.7)
    med = sum(1 for c in confs if 0.4 <= c < 0.7)
    low = sum(1 for c in confs if c < 0.4)
    
    print(f"\n  Bins:")
    print(f"    High (≥0.7): {high} ({high/len(confs)*100:.1f}%)")
    print(f"    Medium: {med} ({med/len(confs)*100:.1f}%)")
    print(f"    Low (<0.4): {low} ({low/len(confs)*100:.1f}%)")

# Top techniques
print(f"\n🎯 Top 10 Techniques:")
for i, t in enumerate(sorted(techs, key=lambda x: x.get('confidence', 0), reverse=True)[:10], 1):
    print(f"  {i}. {t['technique_id']} - {t.get('name', 'Unknown')} ({t.get('confidence', 0):.2f})")

# Tactics coverage
if techs:
    tactics = set()
    for t in techs:
        tactics.update(t.get('tactics', []))
    print(f"\n🗂️  MITRE Tactics Coverage: {len(tactics)} tactics")
    for tactic in sorted(tactics):
        count = sum(1 for t in techs if tactic in t.get('tactics', []))
        print(f"  - {tactic}: {count} techniques")

# Indicator types
if inds:
    print(f"\n🔍 Indicator Types:")
    ind_types = Counter([i.get('type', 'unknown') for i in inds])
    for itype, count in ind_types.most_common():
        print(f"  {itype}: {count}")

# Query graphs
qg_dir = Path('data/query_graphs')
if qg_dir.exists():
    qg_count = len(list(qg_dir.glob('*.json')))
    print(f"\n📊 Query Graphs Generated: {qg_count}")

print("\n" + "="*70)
EOF
```

### 2. Qualitative Review

**Manual inspection**:
```bash
# View specific technique
python3 << 'EOF'
import json
seeds = json.load(open('runs/cti/seeds.json'))

print("Sample Techniques:\n")
for t in seeds['techniques'][:3]:
    print(f"ID: {t['technique_id']}")
    print(f"Name: {t.get('name', 'N/A')}")
    print(f"Confidence: {t.get('confidence', 0):.2f}")
    print(f"Tactics: {', '.join(t.get('tactics', []))}")
    print("-" * 50)
EOF
```

**Check quality**:
- ✅ Technique IDs valid? (Txx.xxx format)
- ✅ Confidence scores reasonable? (0.0-1.0)
- ✅ Names match IDs?
- ✅ Tactics make sense?

### 3. Query Graph Verification

```bash
# List query graphs
ls -lh data/query_graphs/

# View one
cat data/query_graphs/*.json | head -50
```

---

## 📈 Expected Results

### Good Result (OpenAI or MITRE)
```
Techniques: 15-30
Indicators: 10-25
Avg Confidence: 0.65-0.85
Tactics Coverage: 5-8 tactics
Query Graphs: 3+
```

### Acceptable Result (g4f partial success)
```
Techniques: 5-15
Indicators: 5-15
Avg Confidence: 0.50-0.75
Tactics Coverage: 3-5 tactics
Query Graphs: 1-3
```

### Poor Result (g4f failed)
```
Techniques: 0
Indicators: 0
→ Use Option A or C instead
```

---

## 🔍 Troubleshooting

### Issue 1: No Techniques Extracted

```bash
# Check if PDFs were read
ls -lh runs/cti/cti_*.json

# View CTI item
cat runs/cti/cti_000.json | python3 -m json.tool | head -50

# If no text → PDF extraction failed
# Fix: Try different PDF or check PyPDF2 installation
```

### Issue 2: g4f All Fail

```bash
# Fall back to MITRE
python3 scripts/extract_mitre_seeds.py

# Or use OpenAI
export OPENAI_API_KEY="..."
python3 -m src.pipeline.agent.main --llm-backend openai --pdf-dir data/cti_reports/pdfs
```

### Issue 3: Low Quality Results

**Improve**:
- Add more/better PDF reports
- Use OpenAI instead of g4f
- Check input text quality

---

## 📝 Documentation for Research

### Report Template

```
CTI Agent Evaluation Results
=============================

Input:
- Source: [3 PDF reports / MITRE ATT&CK direct]
- Method: [g4f LLM / OpenAI / MITRE extraction]

Output:
- Techniques Extracted: [25]
- Indicators Identified: [18]
- Average Confidence: [0.72]
- Tactics Coverage: [7/14 MITRE tactics]
- Query Graphs: [3 generated]

Quality Assessment:
- Precision: [Manual review - X/Y correct]
- Coverage: [Compared to manual analysis]
- Confidence Distribution: [XX% high confidence]

Conclusion:
[LLM-based CTI extraction successfully identified key techniques...]
```

---

## ✅ Complete Workflow

```bash
# 1. Choose your option
# Option A: MITRE (fastest)
python3 scripts/extract_mitre_seeds.py

# Option B: PDF + g4f (free LLM)
pip install PyPDF2
mkdir -p data/cti_reports/pdfs
# Add PDFs
python3 -m src.pipeline.agent.main --pdf-dir data/cti_reports/pdfs --llm-backend g4f

# Option C: PDF + OpenAI (best quality)
export OPENAI_API_KEY="sk-..."
python3 -m src.pipeline.agent.main --pdf-dir data/cti_reports/pdfs --llm-backend openai

# 2. Evaluate
python3 # Run evaluation script above

# 3. Use for experiments
bash scripts/run_experiments.sh
```

---

## 🎯 Recommendations

**For Research/Thesis**:
- Use **Option C (OpenAI)** - best quality, reproducible
- Document: "LLM-based extraction with GPT-4"
- Cost: ~$0.10-0.15

**For Development/Testing**:
- Use **Option A (MITRE)** - fast, reliable
- Good enough for system testing

**For Demo**:
- Use **Option B (g4f)** with fallback to A
- Shows workflow without cost

---

**Quick Start**: `python3 scripts/extract_mitre_seeds.py` ⚡  
**Best Quality**: Use OpenAI with PDF inputs 🎯  
**For Thesis**: Document LLM extraction process 📄
