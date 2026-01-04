# 🚀 NEXT STEPS - Complete Deployment Roadmap

## 🎯 Repo đã có trên GitHub: https://github.com/tranthehuuphuc/APT-Attack-Detection.git

---

## 📊 Overview

Bạn đã hoàn thành:
- ✅ Code repository hoàn chỉnh
- ✅ 3 attack scenarios
- ✅ Evaluation code
- ✅ Automation scripts
- ✅ Documentation đầy đủ
- ✅ Push lên GitHub

**Next**: Deploy lên GCP VM và chạy experiments

---

## 🎯 PHASE 1: Deploy to GCP VM (30-40 phút)

### Step 1.1: Clone Repository

```bash
# SSH vào GCP VM
gcloud compute ssh YOUR_VM_NAME --zone=YOUR_ZONE

# Trên VM:
cd /opt
sudo mkdir -p apt-detection
sudo chown $USER:$USER apt-detection
cd apt-detection

# Clone từ GitHub
git clone https://github.com/tranthehuuphuc/APT-Attack-Detection.git .

# Verify
ls -la
```

### Step 1.2: Setup Environment

```bash
cd /opt/apt-detection

# Copy-paste toàn bộ script này:
bash << 'SETUP'
set -e

echo "📦 Installing system packages..."
sudo apt update
sudo apt install -y \
  build-essential \
  git \
  wget \
  curl \
  python3.8 \
  python3.8-venv \
  python3.8-dev \
  libpq-dev \
  graphviz \
  libgraphviz-dev \
  auditd \
  audispd-plugins \
  htop \
  tmux

sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

echo "🐍 Setting up Python environment..."
python3.8 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel

echo "📚 Installing Python packages..."
pip install -q -r requirements/core.txt
pip install -q -r requirements/agent.txt

# Install hunting packages (PyTorch + PyG)
# Method 1: Try direct install
pip install -q -r requirements/hunting.txt || {
  echo "⚠️  Hunting requirements failed, trying alternative method..."
  
  # Method 2: Install packages separately
  pip install -q --extra-index-url https://download.pytorch.org/whl/cpu torch==1.11.0 torchvision==0.12.0 torchaudio==0.11.0
  pip install -q torch-scatter torch-sparse torch-cluster torch-spline-conv torch-geometric -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
}

# Install engine requirements
pip install -q -r src/engine/graph_matcher/engine_repo/requirements.txt

# Install g4f for free LLM
pip install -q g4f

echo "📊 Setting up data..."
mkdir -p data/mitre data/cti_reports runs/{events,checkpoints,cti} data/query_graphs

# Download MITRE ATT&CK
wget -q https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
  -O data/mitre/enterprise-attack.json

# Create RSS feeds
cat > data/cti_reports/rss_seeds.txt << 'EOF'
https://www.cisa.gov/cybersecurity-advisories/all.xml
https://www.bleepingcomputer.com/feed/
https://thehackernews.com/feeds/posts/default
EOF

# Link datasets
bash scripts/link_tc_datasets.sh

# Start auditd
sudo systemctl enable auditd
sudo systemctl start auditd

echo ""
echo "✅ Setup complete!"
echo ""
python -c 'import torch, networkx, dgl; print("✅ All imports OK")'
SETUP
```

### Step 1.3: Verify Setup

```bash
source .venv/bin/activate

# Check Python
python --version

# Check imports
python -c "import torch, networkx, dgl; print('✅')"

# Check pretrained models
find src/engine/graph_matcher/engine_repo/ -name "*.pt" -o -name "*.pth"

# Check auditd
sudo systemctl status auditd

# Check data
ls -lh data/mitre/enterprise-attack.json

echo "✅ All systems ready!"
```

**Checklist**:
- [ ] Repo cloned
- [ ] Dependencies installed
- [ ] Python environment working
- [ ] Pretrained models verified
- [ ] Auditd running
- [ ] MITRE data downloaded

---

## 🎯 PHASE 2: Run Quick Test (5-10 phút)

### Test CTI Agent

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Quick test với 3 reports
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/test_seeds.json \
  --llm-backend g4f \
  --per-source-limit 3

# Check results
cat runs/cti/test_seeds.json | python3 -m json.tool | head -50
```

**Expected**:
- File `runs/cti/test_seeds.json` created
- Contains techniques and indicators
- No errors

**Checklist**:
- [ ] CTI Agent runs successfully
- [ ] Seeds.json generated
- [ ] Contains valid data

---

## 🎯 PHASE 3: Run Full Experiments (90 phút)

### Option A: Automated (Recommended)

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Use tmux to avoid disconnect
tmux new -s experiments

# Run everything
bash scripts/run_experiments.sh

# Detach: Ctrl+B, D
# Reattach later: tmux attach -t experiments
```

### Option B: Step by Step

```bash
# 1. Full CTI Agent
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --llm-backend g4f \
  --per-source-limit 10

# 2. Run all scenarios
bash experiments/scenarios/run_all_scenarios.sh

# 3. View results
ls -ltr runs/scenario_results/
```

**Timeline**:
- CTI Agent: ~10-15 phút
- Scenario 1: ~15 phút
- Scenario 2: ~25 phút
- Scenario 3: ~35 phút
- **Total**: ~90 phút

**Checklist**:
- [ ] CTI Agent completed
- [ ] Scenario 1 executed
- [ ] Scenario 2 executed
- [ ] Scenario 3 executed
- [ ] Results generated

---

## 🎯 PHASE 4: Collect Results (10 phút)

### On VM: Review Results

```bash
# Find latest results
RESULTS=$(ls -td runs/scenario_results/*/ | head -1)

# View summary
cat "$RESULTS/suite_summary.txt"

# View detailed eval
cat "$RESULTS/scenario1_eval.json" | python3 -m json.tool
cat "$RESULTS/scenario2_eval.json" | python3 -m json.tool
cat "$RESULTS/scenario3_eval.json" | python3 -m json.tool
```

### Download to macOS

```bash
# Từ macOS local
gcloud compute scp --recurse \
  YOUR_VM:/opt/apt-detection/runs/ \
  ~/Desktop/apt-results-$(date +%Y%m%d)/ \
  --zone=YOUR_ZONE

# Open results
open ~/Desktop/apt-results-*/
```

**Checklist**:
- [ ] Results reviewed on VM
- [ ] Results downloaded to local
- [ ] All eval files present

---

## 🎯 PHASE 5: Analysis & Documentation (1-2 giờ)

### Generate Visualizations (Optional)

```bash
# On local macOS
cd ~/Desktop/apt-results-*/

# If you have Jupyter:
jupyter notebook scenario_results/*/visualization.ipynb
```

### Document Findings

**Create experiment report with**:
1. **Setup**:
   - VM configuration
   - Software versions
   - Dataset details

2. **CTI Agent Results**:
   - Techniques extracted
   - Indicators identified
   - Confidence distribution

3. **Detection Results**:
   - Per-scenario metrics
   - Detection rates
   - False positive analysis

4. **Performance**:
   - Execution times
   - Resource usage
   - Scalability notes

5. **Conclusions**:
   - Key findings
   - Limitations
   - Future work

**Checklist**:
- [ ] Metrics documented
- [ ] Graphs/charts created
- [ ] Findings analyzed
- [ ] Report written

---

## 🎯 PHASE 6: Cleanup (5 phút)

### On VM

```bash
# Cleanup attack artifacts
bash experiments/scenarios/cleanup.sh

# Verify cleanup
sudo crontab -l  # Should be clean
ps aux | grep -E 'npm|stage|check'  # Should be clean
ls -la /tmp/  # No attack artifacts

# Stop VM to save costs
exit
```

### From macOS

```bash
# Stop VM
gcloud compute instances stop YOUR_VM_NAME --zone=YOUR_ZONE

# VM will stop billing (only disk charges remain)
```

**Checklist**:
- [ ] Attack artifacts cleaned
- [ ] VM verified clean
- [ ] VM stopped
- [ ] Results backed up locally

---

## 📊 COMPLETE TIMELINE

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| **1** | Deploy to GCP | 30-40 min | ⏳ |
| **2** | Quick test | 5-10 min | ⏳ |
| **3** | Full experiments | 90 min | ⏳ |
| **4** | Collect results | 10 min | ⏳ |
| **5** | Analysis | 1-2 hours | ⏳ |
| **6** | Cleanup | 5 min | ⏳ |
| **TOTAL** | | **~3-4 hours** | |

---

## ✅ MASTER CHECKLIST

### Pre-Deployment
- [x] Code complete
- [x] Pushed to GitHub
- [ ] GCP VM available
- [ ] gcloud CLI configured

### Deployment  
- [ ] Clone repo to VM
- [ ] Install dependencies
- [ ] Verify setup
- [ ] Quick test passed

### Experiments
- [ ] CTI Agent evaluation
- [ ] Scenario 1 complete
- [ ] Scenario 2 complete
- [ ] Scenario 3 complete
- [ ] Results collected

### Post-Experiment
- [ ] Results analyzed
- [ ] Documentation complete
- [ ] VM cleaned
- [ ] VM stopped

### Thesis/Publication
- [ ] Metrics compiled
- [ ] Visualizations created
- [ ] Report written
- [ ] Ready to present

---

## 🎯 YOUR IMMEDIATE NEXT STEPS

### Step 1: SSH to VM (Now)

```bash
gcloud compute ssh YOUR_VM_NAME --zone=YOUR_ZONE
```

### Step 2: Clone & Setup (30 min)

```bash
cd /opt
sudo mkdir -p apt-detection && sudo chown $USER:$USER apt-detection
cd apt-detection
git clone https://github.com/tranthehuuphuc/APT-Attack-Detection.git .

# Run setup (see Phase 1, Step 1.2)
```

### Step 3: Quick Test (5 min)

```bash
source .venv/bin/activate
python3 -m src.pipeline.agent.main --llm-backend g4f --per-source-limit 3
```

### Step 4: Full Experiments (90 min)

```bash
tmux new -s exp
bash scripts/run_experiments.sh
```

---

## 📚 DOCUMENTATION REFERENCE

| File | Purpose |
|------|---------|
| **NEXT_STEPS.md** | This file - Complete roadmap |
| `START_HERE_EXISTING_VM.md` | Deploy guide |
| `EXPERIMENT_WORKFLOW.md` | Detailed experiment steps |
| `RUN_EXPERIMENTS.md` | Quick reference |
| `scripts/run_experiments.sh` | Automation script |

---

## 💡 TIPS

1. **Use tmux**: Avoid losing work if SSH disconnects
   ```bash
   tmux new -s exp
   # Your work
   # Ctrl+B, D to detach
   # tmux attach -t exp to reattach
   ```

2. **Monitor progress**: In separate terminal
   ```bash
   tail -f runs/experiments_*/cti_agent.log
   ```

3. **Check resources**: 
   ```bash
   htop  # CPU/Memory
   df -h  # Disk
   ```

4. **Save costs**: Stop VM when not in use
   ```bash
   gcloud compute instances stop VM_NAME --zone=ZONE
   ```

---

## 🎉 SUCCESS CRITERIA

After completing all phases, you should have:

✅ **Working System**:
- Deployed on GCP
- All components functional
- Pretrained models working

✅ **Experimental Results**:
- CTI Agent metrics
- 3 scenario evaluations
- Detection performance data

✅ **Documentation**:
- Setup documented
- Results analyzed
- Report ready

✅ **Ready for**:
- Thesis defense
- Paper submission
- Production deployment

---

**Your Next Command**: 
```bash
gcloud compute ssh YOUR_VM_NAME --zone=YOUR_ZONE
```

🚀 **LET'S GO!**
