# ⚡ Quick Deploy to Existing GCP VM

## Bạn đã có VM, chỉ cần 4 bước này:

---

## 🎯 Bước 1: Upload Code lên VM (5-10 phút)

### Từ macOS của bạn:

```bash
cd /Users/tranthehuuphuc/Downloads/APT-Attack-Detection

# Nén code (bỏ qua file không cần thiết)
tar -czf /tmp/apt-code.tar.gz \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='runs' \
    .

# Upload lên VM (thay YOUR_VM_NAME và YOUR_ZONE)
gcloud compute scp /tmp/apt-code.tar.gz \
    YOUR_VM_NAME:/tmp/ \
    --zone=YOUR_ZONE

# Xóa file tạm
rm /tmp/apt-code.tar.gz

echo "✅ Code uploaded!"
```

**Hoặc dùng helper script**:
```bash
# Edit script - sửa tên VM và zone của bạn
# Sau đó chạy:
bash scripts/gcp_helper.sh
# → Chọn 3: Upload code
```

---

## 🎯 Bước 2: SSH vào VM và Extract Code

```bash
# SSH vào VM
gcloud compute ssh YOUR_VM_NAME --zone=YOUR_ZONE

# Trên VM:
sudo mkdir -p /opt/apt-detection
sudo chown $USER:$USER /opt/apt-detection
cd /opt/apt-detection
tar -xzf /tmp/apt-code.tar.gz
rm /tmp/apt-code.tar.gz

echo "✅ Code extracted to /opt/apt-detection"
```

---

## 🎯 Bước 3: Cài Đặt Dependencies (15-20 phút)

**Trên VM, chạy script sau:**

```bash
cd /opt/apt-detection

# One-command setup
bash << 'SETUP_SCRIPT'
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

echo "🐍 Setting up Python environment..."
python3.8 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel

echo "📚 Installing Python packages..."
pip install -q -r requirements/core.txt
pip install -q -r requirements/agent.txt
pip install -q -r requirements/hunting.txt
pip install -q -r src/engine/graph_matcher/engine_repo/requirements.txt

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
echo "Verify with:"
echo "  python -c 'import torch, networkx, dgl; print(\"All OK\")'"
SETUP_SCRIPT

# Verify
source .venv/bin/activate
python -c 'import torch, networkx, dgl; print("✅ All imports OK")'
```

---

## 🎯 Bước 4: Chạy Thử Nghiệm

### Option A: Interactive Testing (Recommended for Learning)

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Menu tương tác
bash experiments/scenarios/quick_test.sh

# Menu options:
# 1 - Test CTI Agent (~5 phút)
# 2 - Test Hunting (~10 phút, cần model)
# 3-5 - Run individual scenarios
# 7 - Run ALL scenarios (~80 phút)
```

### Option B: Quick Test CTI Agent (5 phút)

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Install g4f (free LLM)
pip install -r requirements/g4f.txt

# Run CTI Agent
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --llm-backend g4f \
  --per-source-limit 3

# Check results
cat runs/cti/seeds.json | python3 -m json.tool
```

### Option C: Full Workflow (2-3 giờ)

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Use tmux để tránh mất session
tmux new -s experiments

# 1. Train model (~30 phút)
python3 -m src.pipeline.train.trainer \
  --dataset cadets \
  --epochs 50 \
  --save runs/checkpoints/model.pt

# 2. Run all scenarios (~80 phút)
bash experiments/scenarios/run_all_scenarios.sh

# 3. Results
ls -ltr runs/scenario_results/

# Detach tmux: Ctrl+B, D
# Reattach later: tmux attach -t experiments
```

---

## 📥 Download Results về macOS

**Từ macOS:**

```bash
# Download all results
gcloud compute scp --recurse \
  YOUR_VM_NAME:/opt/apt-detection/runs/scenario_results/ \
  ~/Desktop/apt-results/ \
  --zone=YOUR_ZONE

# Download specific files
gcloud compute scp \
  YOUR_VM_NAME:/opt/apt-detection/runs/cti/seeds.json \
  ~/Downloads/ \
  --zone=YOUR_ZONE

# Open results
open ~/Desktop/apt-results/
```

---

## ⚡ All-in-One Copy-Paste Script

**Chạy toàn bộ từ macOS** (upload + setup + test):

```bash
#!/bin/bash
# Replace these
VM_NAME="your-vm-name"
ZONE="asia-southeast1-a"

# 1. Upload code
cd /Users/tranthehuuphuc/Downloads/APT-Attack-Detection
tar -czf /tmp/apt-code.tar.gz --exclude='.git' --exclude='*.pyc' --exclude='__pycache__' --exclude='.venv' .
gcloud compute scp /tmp/apt-code.tar.gz $VM_NAME:/tmp/ --zone=$ZONE
rm /tmp/apt-code.tar.gz

# 2. Setup on VM
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
  sudo mkdir -p /opt/apt-detection && \
  sudo chown \$USER:\$USER /opt/apt-detection && \
  cd /opt/apt-detection && \
  tar -xzf /tmp/apt-code.tar.gz && \
  rm /tmp/apt-code.tar.gz && \
  echo '✅ Code extracted'
"

# 3. Install dependencies
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
  cd /opt/apt-detection && \
  sudo apt update && \
  sudo apt install -y build-essential python3.8 python3.8-venv python3.8-dev libpq-dev graphviz libgraphviz-dev auditd && \
  python3.8 -m venv .venv && \
  source .venv/bin/activate && \
  pip install -q --upgrade pip && \
  pip install -q -r requirements/core.txt -r requirements/agent.txt && \
  wget -q https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json -O data/mitre/enterprise-attack.json && \
  echo '✅ Setup complete'
"

# 4. SSH to start experiments
gcloud compute ssh $VM_NAME --zone=$ZONE
```

---

## 🔍 Verify Setup

**Trên VM, test nhanh:**

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Check Python
python --version  # Should be 3.8+

# Check imports
python -c "import torch, networkx, dgl; print('✅ PyTorch OK')"

# Check data
ls -lh data/mitre/enterprise-attack.json  # Should exist

# Check engine
ls src/engine/graph_matcher/engine_repo/src/main.py  # Should exist

# Check auditd
sudo systemctl status auditd  # Should be running

echo "✅ All systems ready!"
```

---

## 🎯 Quick Reference

```bash
# === On macOS ===
# Upload code
gcloud compute scp --recurse APT-Attack-Detection VM:/opt/ --zone=ZONE

# SSH to VM
gcloud compute ssh VM_NAME --zone=ZONE

# Download results
gcloud compute scp --recurse VM:/opt/apt-detection/runs/ ~/Desktop/ --zone=ZONE


# === On GCP VM ===
# Activate env
cd /opt/apt-detection && source .venv/bin/activate

# Quick test
bash experiments/scenarios/quick_test.sh

# Run all
bash experiments/scenarios/run_all_scenarios.sh

# Monitor
htop
```

---

## 💡 Pro Tips

1. **Dùng tmux**: Tránh mất session khi SSH disconnect
   ```bash
   tmux new -s main
   # Work...
   # Ctrl+B, D to detach
   # Later: tmux attach -t main
   ```

2. **Monitor resources**:
   ```bash
   htop  # CPU/Memory
   df -h  # Disk
   ```

3. **Background jobs**:
   ```bash
   nohup bash experiments/scenarios/run_all_scenarios.sh > output.log 2>&1 &
   tail -f output.log
   ```

---

## ⏱️ Timeline

| Task | Duration |
|------|----------|
| Upload code | 5-10 min |
| Install dependencies | 15-20 min |
| Quick test CTI Agent | 5 min |
| Train model | 30 min |
| Run all scenarios | 80 min |
| **TOTAL** | **~2-3 hours** |

---

## 🆘 Troubleshooting

**SSH connection issues?**
```bash
gcloud compute ssh VM_NAME --zone=ZONE --force-key-file-overwrite
```

**Permission denied?**
```bash
sudo chown -R $USER:$USER /opt/apt-detection
```

**Out of memory?**
```bash
# Add swap temporarily
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**Python import errors?**
```bash
source .venv/bin/activate
pip install --upgrade -r requirements/hunting.txt
```

---

## ✅ Success Checklist

- [ ] Code uploaded to `/opt/apt-detection`
- [ ] Virtual environment created
- [ ] All dependencies installed
- [ ] MITRE data downloaded
- [ ] Datasets linked
- [ ] Auditd running
- [ ] CTI Agent tested
- [ ] Ready to run experiments!

---

**Next Step**: SSH vào VM và chạy `bash experiments/scenarios/quick_test.sh` 🚀
