# ⚡ RUN EXPERIMENTS - Quick Guide

## Sử Dụng Pretrained Models (Không Cần Training)

---

## 🎯 Một Command - Chạy Toàn Bộ

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Run everything: CTI Agent + 3 Scenarios
bash scripts/run_experiments.sh
```

**Script tự động chạy**:
1. ✅ CTI Agent evaluation (~10 phút)
2. ✅ Scenario 1: APT29 (~15 phút)
3. ✅ Scenario 2: APT28 (~25 phút)
4. ✅ Scenario 3: Lazarus (~35 phút)
5. ✅ Generate analysis report (~5 phút)

**Total**: ~90 phút (1.5 giờ)

---

## 📋 Manual Control (Từng Bước)

### Bước 1: CTI Agent (10 phút)

```bash
source .venv/bin/activate

python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --llm-backend g4f \
  --per-source-limit 10
```

### Bước 2: Run Scenarios (80 phút)

```bash
# Use tmux to avoid disconnect
tmux new -s exp

# Run all scenarios
bash experiments/scenarios/run_all_scenarios.sh

# Detach: Ctrl+B, D
# Reattach: tmux attach -t exp
```

### Bước 3: View Results

```bash
# Latest results
RESULTS=$(ls -td runs/scenario_results/*/ | head -1)
cat "$RESULTS/suite_summary.txt"
```

---

## 📥 Download Results

**Từ macOS**:

```bash
gcloud compute scp --recurse \
  YOUR_VM:/opt/apt-detection/runs/ \
  ~/Desktop/apt-results/ \
  --zone=YOUR_ZONE
```

---

## 🎯 Expected Output

### CTI Agent
- Techniques: 50-200
- Indicators: 100-500
- Query Graphs: 10-50

### Attack Scenarios
- Scenario 1: Detection 85-95%, F1: 0.85-0.92
- Scenario 2: Detection 75-85%, F1: 0.76-0.83
- Scenario 3: Detection 65-80%, F1: 0.66-0.73

---

## ✅ Quick Checklist

- [ ] Deploy code to VM
- [ ] Install dependencies
- [ ] Verify pretrained models exist
- [ ] Start auditd
- [ ] Run `bash scripts/run_experiments.sh`
- [ ] Wait ~90 minutes
- [ ] Download results
- [ ] Cleanup artifacts

---

## 📖 Full Documentation

- **EXPERIMENT_WORKFLOW.md** - Detailed workflow
- **scripts/run_experiments.sh** - Automation script
- **experiments/scenarios/run_all_scenarios.sh** - Scenarios only

---

**Next Step**: `bash scripts/run_experiments.sh` 🚀
