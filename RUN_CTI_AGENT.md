# 🤖 CTI Agent Evaluation - Step by Step

## Mục Đích

Đánh giá khả năng của LLM Agent (sử dụng g4f - free backend) trong việc:
1. Trích xuất MITRE ATT&CK techniques từ CTI reports
2. Nhận diện Indicators of Compromise (IOCs)  
3. Tạo query graphs cho hunting
4. Đánh giá confidence scores

---

## ⚡ Quick Start (5-10 phút)

### On VM - Copy & Paste

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Run CTI Agent với 10 reports per source
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --out-cti runs/cti \
  --out-qg data/query_graphs \
  --llm-backend g4f \
  --per-source-limit 10

# Expected time: 5-10 minutes
```

---

## 📋 Detailed Steps

### Step 1: Activate Environment

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Verify
python -c "import g4f; print('✅ g4f ready')"
```

### Step 2: Check Input Data

```bash
# Check MITRE ATT&CK
ls -lh data/mitre/enterprise-attack.json

# Check RSS feeds
cat data/cti_reports/rss_seeds.txt
grep -v '^#' data/cti_reports/rss_seeds.txt | grep -v '^$' | wc -l
# Should show 5-7 feeds
```

### Step 3: Run CTI Agent

**Option A: Quick Test (3 reports per source)**

```bash
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/test_seeds.json \
  --llm-backend g4f \
  --per-source-limit 3

# Time: ~3-5 minutes
```

**Option B: Full Evaluation (10 reports per source)** ⭐

```bash
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --out-cti runs/cti \
  --out-qg data/query_graphs \
  --llm-backend g4f \
  --per-source-limit 10

# Time: ~8-12 minutes
```

**Option C: Comprehensive (20 reports per source)**

```bash
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds_full.json \
  --out-cti runs/cti_full \
  --out-qg data/query_graphs \
  --llm-backend g4f \
  --per-source-limit 20

# Time: ~15-20 minutes
```

### Step 4: Monitor Progress

**In another terminal:**

```bash
# SSH to VM
gcloud compute ssh YOUR_VM --zone=YOUR_ZONE

# Watch log
cd /opt/apt-detection
tail -f runs/cti/*.log

# Or monitor files
watch -n 2 'ls -lrt runs/cti/ | tail -10'
```

---

## 📊 Analyze Results

### Check Output Files

```bash
# Main output - seeds.json
ls -lh runs/cti/seeds.json

# Individual CTI items
ls -1 runs/cti/cti_*.json | wc -l

# Query graphs
ls -1 data/query_graphs/*.json | wc -l
```

### View Seeds Summary

```bash
cat runs/cti/seeds.json | python3 -m json.tool | head -100
```

### Detailed Analysis

```bash
python3 << 'EOF'
import json
from pathlib import Path
from collections import Counter

# Load seeds
seeds_file = Path('runs/cti/seeds.json')
if not seeds_file.exists():
    print("❌ seeds.json not found")
    exit(1)

seeds = json.loads(seeds_file.read_text())

print("=" * 70)
print("CTI AGENT EVALUATION RESULTS")
print("=" * 70)

# 1. Extraction Counts
techniques = seeds.get('techniques', [])
indicators = seeds.get('indicators', [])

print(f"\n📊 Extraction Statistics:")
print(f"  Total Techniques: {len(techniques)}")
print(f"  Total Indicators: {len(indicators)}")

# 2. Top Techniques
print(f"\n🎯 Top 10 Extracted Techniques:")
tech_counter = Counter([t.get('technique_id', 'unknown') for t in techniques])
for i, (tid, count) in enumerate(tech_counter.most_common(10), 1):
    print(f"  {i}. {tid}: {count} occurrences")

# 3. Confidence Distribution
print(f"\n📈 Confidence Distribution:")
confidences = [t.get('confidence', 0) for t in techniques if 'confidence' in t]
if confidences:
    avg_conf = sum(confidences) / len(confidences)
    print(f"  Average: {avg_conf:.3f}")
    print(f"  Min: {min(confidences):.3f}")
    print(f"  Max: {max(confidences):.3f}")
    
    # Bins
    high = sum(1 for c in confidences if c >= 0.7)
    med = sum(1 for c in confidences if 0.4 <= c < 0.7)
    low = sum(1 for c in confidences if c < 0.4)
    
    print(f"\n  Confidence Bins:")
    print(f"    High (≥0.7): {high} ({high/len(confidences)*100:.1f}%)")
    print(f"    Medium (0.4-0.7): {med} ({med/len(confidences)*100:.1f}%)")
    print(f"    Low (<0.4): {low} ({low/len(confidences)*100:.1f}%)")

# 4. Technique Categories (Tactics)
print(f"\n🗂️  MITRE Tactics Coverage:")
tactics_set = set()
for tech in techniques:
    tid = tech.get('technique_id', '')
    # Tactics are typically in the technique object or can be inferred
    if 'tactics' in tech:
        tactics_set.update(tech['tactics'])

if tactics_set:
    print(f"  Covered Tactics: {len(tactics_set)}")
    for tactic in sorted(tactics_set):
        print(f"    - {tactic}")

# 5. Indicator Types
print(f"\n🔍 Indicator Types:")
ind_types = Counter([ind.get('type', 'unknown') for ind in indicators])
for itype, count in ind_types.most_common():
    print(f"  {itype}: {count}")

# 6. Sample Indicators
print(f"\n💡 Sample Indicators (first 5):")
for i, ind in enumerate(indicators[:5], 1):
    itype = ind.get('type', 'N/A')
    value = ind.get('value', 'N/A')
    # Truncate long values
    if len(value) > 60:
        value = value[:60] + "..."
    print(f"  {i}. [{itype}] {value}")

# 7. Query Graphs
qg_dir = Path('data/query_graphs')
if qg_dir.exists():
    qg_files = list(qg_dir.glob('*.json'))
    print(f"\n📊 Query Graphs Generated: {len(qg_files)}")
    for qg in qg_files[:5]:
        print(f"  - {qg.name}")
    if len(qg_files) > 5:
        print(f"  ... and {len(qg_files) - 5} more")

print("\n" + "=" * 70)
EOF
```

---

## 🎯 Expected Results

### Extraction Counts

| Metric | Expected Range |
|--------|----------------|
| Techniques | 50-200 |
| Indicators | 100-500 |
| Query Graphs | 10-50 |
| Avg Confidence | 0.6-0.8 |
| High Confidence (≥0.7) | 40-60% |

### Top Techniques (Examples)

- T1566 (Phishing)
- T1059 (Command and Scripting Interpreter)
- T1105 (Ingress Tool Transfer)
- T1071 (Application Layer Protocol)
- T1055 (Process Injection)

### Indicator Types

- `file_hash` (MD5, SHA256)
- `ip_address`
- `domain`
- `url`
- `file_path`
- `registry_key`

---

## 📈 Evaluation Metrics

### Manual Inspection

```bash
# Pick a random CTI report
ls runs/cti/cti_*.json | shuf | head -1 | xargs cat | python3 -m json.tool

# Check quality:
# - Are techniques relevant?
# - Are IOCs correctly extracted?
# - Is confidence reasonable?
```

### Automated Evaluation (if ground truth available)

```bash
python3 -m src.eval.agent_eval \
  --predicted runs/cti/seeds.json \
  --ground-truth path/to/ground_truth.json \
  --output runs/evaluation/agent_eval.json

# View results
cat runs/evaluation/agent_eval.json | python3 -m json.tool
```

---

## 🔍 Troubleshooting

### Issue 1: g4f Connection Errors

```bash
# Symptom: "Failed to connect to g4f provider"

# Solution: Retry or use different backend
python3 -m src.pipeline.agent.main \
  --llm-backend openai \  # If you have API key
  --per-source-limit 10
```

### Issue 2: No Techniques Extracted

```bash
# Check logs
ls -lrt runs/cti/*.log | tail -1 | awk '{print $NF}' | xargs tail -50

# Verify MITRE data
python3 -c "import json; data=json.load(open('data/mitre/enterprise-attack.json')); print(f'{len([o for o in data[\"objects\"] if o.get(\"type\")==\"attack-pattern\"])} techniques')"
```

### Issue 3: Out of Memory

```bash
# Reduce batch size
python3 -m src.pipeline.agent.main \
  --per-source-limit 5 \  # Reduce from 10 to 5
  --llm-backend g4f
```

---

## 💾 Save Results

### Create Evaluation Report

```bash
# Run analysis and save to file
python3 << 'EOF' > runs/cti/evaluation_report.txt
import json
from pathlib import Path
from collections import Counter
from datetime import datetime

seeds = json.loads(Path('runs/cti/seeds.json').read_text())

print(f"CTI Agent Evaluation Report")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

techniques = seeds.get('techniques', [])
indicators = seeds.get('indicators', [])

print(f"\nExtraction Summary:")
print(f"  Techniques: {len(techniques)}")
print(f"  Indicators: {len(indicators)}")

confidences = [t.get('confidence', 0) for t in techniques]
if confidences:
    print(f"\nConfidence Statistics:")
    print(f"  Average: {sum(confidences)/len(confidences):.3f}")
    print(f"  Min: {min(confidences):.3f}")
    print(f"  Max: {max(confidences):.3f}")

print(f"\nTop 10 Techniques:")
for tid, count in Counter([t['technique_id'] for t in techniques]).most_common(10):
    print(f"  {tid}: {count}")

print(f"\nIndicator Types:")
for itype, count in Counter([i['type'] for i in indicators]).most_common():
    print(f"  {itype}: {count}")
EOF

cat runs/cti/evaluation_report.txt
```

### Archive Results

```bash
# Create timestamped archive
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p runs/archives
tar -czf runs/archives/cti_agent_$TIMESTAMP.tar.gz \
  runs/cti/seeds.json \
  runs/cti/cti_*.json \
  data/query_graphs/*.json

echo "✅ Archived to: runs/archives/cti_agent_$TIMESTAMP.tar.gz"
```

---

## 📥 Download Results to Local

**From macOS:**

```bash
# Download all CTI results
gcloud compute scp --recurse \
  YOUR_VM:/opt/apt-detection/runs/cti/ \
  ~/Desktop/cti-results-$(date +%Y%m%d)/ \
  --zone=YOUR_ZONE

# Download just seeds.json
gcloud compute scp \
  YOUR_VM:/opt/apt-detection/runs/cti/seeds.json \
  ~/Desktop/ \
  --zone=YOUR_ZONE
```

---

## ✅ Success Criteria

CTI Agent evaluation successful if:

- [x] seeds.json generated
- [x] Techniques extracted (>20)
- [x] Indicators extracted (>50)
- [x] Average confidence >0.5
- [x] Multiple MITRE tactics covered
- [x] Query graphs generated
- [x] No critical errors in logs

---

## 🚀 Next Steps

After CTI Agent evaluation:

1. **Review Results**: Analyze extraction quality
2. **Run Scenarios**: Use seeds for hunting
   ```bash
   bash scripts/run_experiments.sh
   ```
3. **Document Findings**: Note interesting patterns

---

## 📚 References

- CTI Agent code: `src/pipeline/agent/`
- Evaluation code: `src/eval/agent_eval.py`
- MITRE ATT&CK: `data/mitre/enterprise-attack.json`

---

**Quick Command**: 
```bash
source .venv/bin/activate && python3 -m src.pipeline.agent.main --rss-file data/cti_reports/rss_seeds.txt --stix data/mitre/enterprise-attack.json --out-seeds runs/cti/seeds.json --llm-backend g4f --per-source-limit 10
```

**Time**: 5-10 minutes ⏱️
