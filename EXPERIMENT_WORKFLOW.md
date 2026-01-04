# 🧪 Experiment Workflow - Using Pretrained Models

## Quy Trình Thực Nghiệm Hoàn Chỉnh

**Note**: Hệ thống sử dụng GNN models đã được train sẵn trong engine → **KHÔNG CẦN TRAINING**

---

## 📋 Timeline Thực Nghiệm

| Phase | Task | Duration |
|-------|------|----------|
| **Phase 1** | CTI Agent Evaluation | 10-15 min |
| **Phase 2** | Attack Scenario 1 (APT29) | 15 min |
| **Phase 3** | Attack Scenario 2 (APT28) | 25 min |
| **Phase 4** | Attack Scenario 3 (Lazarus) | 35 min |
| **Phase 5** | Results Analysis | 15 min |
| **TOTAL** | | **~2 hours** |

---

## 🎯 Phase 1: CTI Agent Evaluation (10-15 phút)

### Mục tiêu
Đánh giá khả năng của LLM Agent trong việc:
- Extract MITRE ATT&CK techniques từ CTI reports
- Identify indicators of compromise (IOCs)
- Generate query graphs

### Setup

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Install g4f (free LLM backend)
pip install -r requirements/g4f.txt
```

### Run CTI Agent

```bash
# Run với nhiều nguồn CTI
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --out-cti runs/cti \
  --out-qg data/query_graphs \
  --llm-backend g4f \
  --per-source-limit 10

# Check outputs
echo "✅ CTI Seeds:"
cat runs/cti/seeds.json | python3 -m json.tool | head -50

echo ""
echo "✅ Query Graphs generated:"
ls -1 data/query_graphs/ | wc -l

echo ""
echo "✅ CTI items processed:"
ls -1 runs/cti/cti_*.json | wc -l
```

### Evaluate CTI Agent

**Option A: Với Ground Truth (nếu có)**

```bash
# Nếu bạn có ground truth file
python3 -m src.eval.agent_eval \
  --predicted runs/cti/seeds.json \
  --ground-truth path/to/ground_truth.json \
  --output runs/evaluation/agent_eval.json

# View results
cat runs/evaluation/agent_eval.json | python3 -m json.tool
```

**Option B: Manual Inspection**

```bash
# Inspect outputs
python3 << 'EOF'
import json
from pathlib import Path
from collections import Counter

# Load seeds
seeds = json.loads(Path('runs/cti/seeds.json').read_text())

print("=" * 60)
print("CTI AGENT EVALUATION RESULTS")
print("=" * 60)

# 1. Extraction counts
print(f"\n📊 Extraction Counts:")
print(f"  Techniques: {len(seeds.get('techniques', []))}")
print(f"  Indicators: {len(seeds.get('indicators', []))}")

# 2. Technique distribution
print(f"\n🎯 Top 10 Techniques:")
techs = [t['technique_id'] for t in seeds.get('techniques', [])]
for tid, count in Counter(techs).most_common(10):
    print(f"  {tid}: {count} occurrences")

# 3. Confidence stats
print(f"\n📈 Confidence Statistics:")
confidences = [t.get('confidence', 0) for t in seeds.get('techniques', [])]
if confidences:
    print(f"  Mean: {sum(confidences)/len(confidences):.2f}")
    print(f"  Min: {min(confidences):.2f}")
    print(f"  Max: {max(confidences):.2f}")
    
    # Confidence bins
    high = sum(1 for c in confidences if c >= 0.7)
    med = sum(1 for c in confidences if 0.4 <= c < 0.7)
    low = sum(1 for c in confidences if c < 0.4)
    print(f"\n  High (≥0.7): {high}")
    print(f"  Med (0.4-0.7): {med}")
    print(f"  Low (<0.4): {low}")

# 4. Indicator types
print(f"\n🔍 Indicator Types:")
ind_types = Counter([i.get('type') for i in seeds.get('indicators', [])])
for itype, count in ind_types.most_common():
    print(f"  {itype}: {count}")

# 5. Query graphs
qg_dir = Path('data/query_graphs')
if qg_dir.exists():
    qg_count = len(list(qg_dir.glob('*.json')))
    print(f"\n📊 Query Graphs: {qg_count} generated")

print("\n" + "=" * 60)
EOF
```

---

## 🎯 Phase 2-4: Attack Scenarios với Pretrained Models

### Setup (một lần)

```bash
# Verify pretrained models exist
ls -lh src/engine/graph_matcher/engine_repo/checkpoint/

# Should see .pt or .pth files
# Nếu không có, check trong dataset directories
find src/engine/graph_matcher/engine_repo/ -name "*.pt" -o -name "*.pth"

# Start auditd
sudo systemctl start auditd
sudo systemctl status auditd
```

### Run Scenarios Tự Động

**Option A: Run All Scenarios (Recommended)**

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Use tmux to avoid SSH disconnect
tmux new -s experiments

# Run all scenarios
bash experiments/scenarios/run_all_scenarios.sh

# Script sẽ tự động:
# 1. Chạy attack script
# 2. Collect audit events
# 3. Run hunting với pretrained model
# 4. Evaluate results
# 5. Generate report

# Detach: Ctrl+B, D
# Reattach later: tmux attach -t experiments
```

**Option B: Run Individual Scenarios**

```bash
# Scenario 1: APT29 (~15 phút)
bash experiments/scenarios/run_all_scenarios.sh --scenario 1

# Scenario 2: APT28 (~25 phút)
bash experiments/scenarios/run_all_scenarios.sh --scenario 2

# Scenario 3: Lazarus (~35 phút)
bash experiments/scenarios/run_all_scenarios.sh --scenario 3
```

### Manual Scenario Execution (nếu cần control từng bước)

```bash
# === Scenario 1 Example ===

# Step 1: Run attack
bash experiments/scenarios/scenario1_apt29/attack.sh

# Step 2: Collect events
python3 -m src.pipeline.hunting.collector \
  --audit-log /var/log/audit/audit.log \
  --out runs/events/scenario1_events.jsonl

# Step 3: Find pretrained checkpoint
CHECKPOINT=$(find src/engine/graph_matcher/engine_repo/ -name "*.pt" | head -1)
echo "Using checkpoint: $CHECKPOINT"

# Step 4: Run hunting with pretrained model
python3 -m src.pipeline.hunting.main \
  --dataset cadets \
  --events runs/events/scenario1_events.jsonl \
  --checkpoint "$CHECKPOINT" \
  --cti-seeds runs/cti/seeds.json

# Step 5: Evaluate
python3 -m src.eval.hunting_eval \
  --events runs/events/scenario1_events.jsonl \
  --ground-truth experiments/scenarios/scenario1_apt29/ground_truth.json \
  --output runs/evaluation/scenario1_eval.json

# Step 6: Cleanup
bash experiments/scenarios/cleanup.sh
```

---

## 🎯 Phase 5: Results Analysis (15 phút)

### Collect All Results

```bash
cd /opt/apt-detection

# Find latest results directory
RESULTS_DIR=$(ls -td runs/scenario_results/*/ | head -1)
echo "Results directory: $RESULTS_DIR"

# View summary
cat "$RESULTS_DIR/suite_summary.txt"
```

### Generate Consolidated Report

```bash
python3 << 'EOF'
import json
from pathlib import Path
from datetime import datetime

# Find latest results
results_dirs = sorted(Path('runs/scenario_results').glob('*/'), reverse=True)
if not results_dirs:
    print("No results found")
    exit()

latest = results_dirs[0]
print(f"Analyzing results from: {latest.name}\n")

# Collect evaluation results
scenarios = {}
for i in [1, 2, 3]:
    eval_file = latest / f"scenario{i}_eval.json"
    if eval_file.exists():
        scenarios[i] = json.loads(eval_file.read_text())

# Generate report
print("=" * 70)
print("EXPERIMENT RESULTS SUMMARY")
print("=" * 70)

for scenario_num, data in scenarios.items():
    scenario_names = {1: "APT29", 2: "APT28", 3: "Lazarus"}
    print(f"\n📊 Scenario {scenario_num}: {scenario_names[scenario_num]}")
    print("-" * 70)
    
    # Detection metrics
    if 'detection_metrics' in data:
        dm = data['detection_metrics']
        print(f"  Detection Rate: {dm.get('detection_rate', 0):.1%}")
        print(f"  Precision: {dm.get('precision', 0):.2f}")
        print(f"  Recall: {dm.get('recall', 0):.2f}")
        print(f"  F1-Score: {dm.get('f1_score', 0):.2f}")
        print(f"  FPR: {dm.get('false_positive_rate', 0):.1%}")
    
    # Performance metrics
    if 'performance_metrics' in data:
        pm = data['performance_metrics']
        print(f"\n  Performance:")
        print(f"    Latency: {pm.get('total_latency_seconds', 0):.1f}s")
        print(f"    Events processed: {pm.get('events_processed', 0)}")
        print(f"    Alerts generated: {pm.get('alerts_generated', 0)}")

print("\n" + "=" * 70)

# Overall statistics
if scenarios:
    all_f1 = [s['detection_metrics']['f1_score'] 
              for s in scenarios.values() 
              if 'detection_metrics' in s]
    
    if all_f1:
        print(f"\nOVERALL PERFORMANCE:")
        print(f"  Average F1-Score: {sum(all_f1)/len(all_f1):.2f}")
        print(f"  Best: {max(all_f1):.2f}")
        print(f"  Worst: {min(all_f1):.2f}")

print("\n" + "=" * 70)
EOF
```

### Visualize Results (nếu cần)

```bash
# Copy visualization notebook to results dir
cp experiments/scenarios/visualization.ipynb "$RESULTS_DIR/"

# If Jupyter is available:
# cd "$RESULTS_DIR"
# jupyter notebook visualization.ipynb
```

---

## 📥 Download Results to Local

**Từ macOS:**

```bash
# Download all results
gcloud compute scp --recurse \
  YOUR_VM:/opt/apt-detection/runs/scenario_results/ \
  ~/Desktop/apt-experiment-results/ \
  --zone=YOUR_ZONE

# Download evaluation
gcloud compute scp --recurse \
  YOUR_VM:/opt/apt-detection/runs/evaluation/ \
  ~/Desktop/apt-experiment-results/ \
  --zone=YOUR_ZONE

# Download CTI results
gcloud compute scp --recurse \
  YOUR_VM:/opt/apt-detection/runs/cti/ \
  ~/Desktop/apt-experiment-results/ \
  --zone=YOUR_ZONE

echo "✅ Results downloaded to ~/Desktop/apt-experiment-results/"
open ~/Desktop/apt-experiment-results/
```

---

## 📊 Expected Results

### CTI Agent Performance

| Metric | Expected Range |
|--------|----------------|
| Techniques extracted | 50-200 |
| Indicators identified | 100-500 |
| Query graphs generated | 10-50 |
| Average confidence | 0.6-0.8 |
| High confidence (≥0.7) | 40-60% |

### Attack Detection Performance

| Scenario | Expected Detection Rate | Expected F1 |
|----------|------------------------|-------------|
| APT29 (Medium) | 85-95% | 0.85-0.92 |
| APT28 (High) | 75-85% | 0.76-0.83 |
| Lazarus (Very High) | 65-80% | 0.66-0.73 |

---

## ✅ Experiment Checklist

### Pre-Experiment
- [ ] Code deployed to VM
- [ ] Dependencies installed
- [ ] CTI feeds configured
- [ ] Pretrained models verified
- [ ] Auditd running

### Phase 1: CTI Agent
- [ ] Run CTI Agent
- [ ] Verify seeds.json generated
- [ ] Check query graphs
- [ ] Evaluate/inspect results

### Phase 2-4: Attack Scenarios
- [ ] Run Scenario 1
- [ ] Run Scenario 2
- [ ] Run Scenario 3
- [ ] Verify hunting executed with pretrained models
- [ ] Check evaluation metrics

### Phase 5: Analysis
- [ ] Generate consolidated report
- [ ] Review detection rates
- [ ] Analyze false positives/negatives
- [ ] Document findings

### Post-Experiment
- [ ] Download results to local
- [ ] Cleanup attack artifacts
- [ ] Generate final report
- [ ] Stop/preserve VM

---

## 🎯 Quick Start Commands

```bash
# === Full Experiment Workflow ===

cd /opt/apt-detection
source .venv/bin/activate

# 1. CTI Agent
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --llm-backend g4f \
  --per-source-limit 10

# 2. Run all scenarios
tmux new -s exp
bash experiments/scenarios/run_all_scenarios.sh

# 3. Analyze (after scenarios complete)
RESULTS_DIR=$(ls -td runs/scenario_results/*/ | head -1)
cat "$RESULTS_DIR/suite_summary.txt"

# 4. Download (from macOS)
gcloud compute scp --recurse VM:/opt/apt-detection/runs/ ~/Desktop/results/ --zone=ZONE
```

---

## 📝 Notes

1. **Pretrained Models**: System uses models from `src/engine/graph_matcher/engine_repo/`
2. **No Training Required**: Skip training phase entirely
3. **Focus**: CTI Agent evaluation + Attack scenario testing
4. **Timeline**: ~2 hours for complete experiment
5. **Output**: Detection metrics, performance analysis, comprehensive reports

---

**Status**: ✅ Ready for experiments with pretrained models  
**Next**: `bash experiments/scenarios/run_all_scenarios.sh` 🚀
