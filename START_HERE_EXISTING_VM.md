# ✅ Deploy to Your Existing GCP VM - TÓM TẮT

## 🎯 Bạn Cần Làm Gì

Chỉ **4 BƯỚC ĐƠN GIẢN**:

1. ✅ Upload code lên VM
2. ✅ Extract code
3. ✅ Cài đặt dependencies  
4. ✅ Chạy thử nghiệm

**Thời gian**: ~30-40 phút để setup, sau đó có thể chạy experiments

---

## ⚡ CÁCH NHANH NHẤT (Recommended)

### One-Command Deploy từ macOS:

```bash
cd /Users/tranthehuuphuc/Downloads/APT-Attack-Detection

# Chạy script (thay YOUR_VM_NAME và YOUR_ZONE)
bash scripts/deploy_to_vm.sh YOUR_VM_NAME YOUR_ZONE

# Ví dụ:
# bash scripts/deploy_to_vm.sh apt-vm asia-southeast1-a
```

Script sẽ tự động:
- ✅ Nén code
- ✅ Upload lên VM
- ✅ Extract vào `/opt/apt-detection`

---

## 📖 CHI TIẾT TỪNG BƯỚC

### Bước 1: Upload Code (5-10 phút)

**Từ macOS**:
```bash
cd /Users/tranthehuuphuc/Downloads/APT-Attack-Detection

# Nén code
tar -czf /tmp/apt-code.tar.gz \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    .

# Upload (thay YOUR_VM_NAME và YOUR_ZONE)
gcloud compute scp /tmp/apt-code.tar.gz YOUR_VM_NAME:/tmp/ --zone=YOUR_ZONE

# Xóa file tạm
rm /tmp/apt-code.tar.gz
```

### Bước 2: SSH và Extract (2 phút)

```bash
# SSH vào VM
gcloud compute ssh YOUR_VM_NAME --zone=YOUR_ZONE

# Trên VM:
sudo mkdir -p /opt/apt-detection
sudo chown $USER:$USER /opt/apt-detection
cd /opt/apt-detection
tar -xzf /tmp/apt-code.tar.gz
rm /tmp/apt-code.tar.gz
```

### Bước 3: Setup Dependencies (15-20 phút)

**Trên VM, copy-paste toàn bộ**:

```bash
cd /opt/apt-detection

# One-command setup
bash << 'EOF'
set -e

# Install system packages
sudo apt update
sudo apt install -y \
  build-essential git wget curl python3.8 python3.8-venv python3.8-dev \
  libpq-dev graphviz libgraphviz-dev auditd audispd-plugins htop tmux

# Setup Python
python3.8 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel

# Install packages
pip install -q -r requirements/core.txt
pip install -q -r requirements/agent.txt
pip install -q -r requirements/hunting.txt
pip install -q -r src/engine/graph_matcher/engine_repo/requirements.txt

# Setup data
mkdir -p data/mitre data/cti_reports runs/{events,checkpoints,cti} data/query_graphs
wget -q https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
  -O data/mitre/enterprise-attack.json

cat > data/cti_reports/rss_seeds.txt << 'FEEDS'
https://www.cisa.gov/cybersecurity-advisories/all.xml
https://www.bleepingcomputer.com/feed/
https://thehackernews.com/feeds/posts/default
FEEDS

bash scripts/link_tc_datasets.sh

# Start auditd
sudo systemctl enable auditd
sudo systemctl start auditd

echo ""
echo "✅ Setup complete!"
python -c 'import torch, networkx, dgl; print("✅ All imports OK")'
EOF
```

### Bước 4: Chạy Thử Nghiệm

**Quick test (5 phút)**:
```bash
cd /opt/apt-detection
source .venv/bin/activate

bash experiments/scenarios/quick_test.sh
# Chọn option 1: Test CTI Agent
```

**Full experiment (~2-3 giờ)**:
```bash
# Dùng tmux để tránh mất session
tmux new -s exp

cd /opt/apt-detection
source .venv/bin/activate

# Run all scenarios
bash experiments/scenarios/run_all_scenarios.sh

# Detach: Ctrl+B, D
# Reattach: tmux attach -t exp
```

---

## 📥 Download Results

**Từ macOS**:
```bash
# Download results
gcloud compute scp --recurse \
  YOUR_VM_NAME:/opt/apt-detection/runs/scenario_results/ \
  ~/Desktop/apt-results/ \
  --zone=YOUR_ZONE

# Open
open ~/Desktop/apt-results/
```

---

## 📚 Documentation

| File | Mục đích |
|------|----------|
| **DEPLOY_TO_EXISTING_VM.md** | ⭐ Hướng dẫn chi tiết 4 bước |
| `scripts/deploy_to_vm.sh` | Script tự động upload |
| `GCP_DEPLOYMENT_GUIDE.md` | Full guide (nếu cần ref) |
| `experiments/scenarios/quick_test.sh` | Interactive testing |

---

## ✅ Quick Commands Cheat Sheet

```bash
# === Từ macOS ===
# Deploy code
bash scripts/deploy_to_vm.sh VM_NAME ZONE

# SSH to VM
gcloud compute ssh VM_NAME --zone=ZONE

# Download results
gcloud compute scp --recurse VM:/opt/apt-detection/runs/ ~/Desktop/ --zone=ZONE


# === Trên VM ===
# Activate environment
cd /opt/apt-detection && source .venv/bin/activate

# Quick test
bash experiments/scenarios/quick_test.sh

# Run all experiments
bash experiments/scenarios/run_all_scenarios.sh

# Monitor
htop
```

---

## ⏱️ Timeline

| Task | Duration | Where |
|------|----------|-------|
| Upload code | 5-10 min | macOS |
| Extract code | 2 min | VM |
| Install deps | 15-20 min | VM |
| Quick test | 5 min | VM |
| Train model | 30 min | VM |
| Run all scenarios | 80 min | VM |

---

## 🎯 YOUR NEXT STEP

```bash
# 1. Open terminal on macOS
cd /Users/tranthehuuphuc/Downloads/APT-Attack-Detection

# 2. Run deploy script (thay tên VM và zone của bạn)
bash scripts/deploy_to_vm.sh YOUR_VM_NAME YOUR_ZONE

# 3. SSH to VM (script sẽ show command)
gcloud compute ssh YOUR_VM_NAME --zone=YOUR_ZONE

# 4. On VM - setup (copy-paste from Bước 3)
cd /opt/apt-detection
bash << 'EOF'
...
EOF

# 5. Test
bash experiments/scenarios/quick_test.sh
```

---

**Status**: ✅ **READY**  
**Time to first experiment**: ~30-40 minutes  
**Start**: `bash scripts/deploy_to_vm.sh VM_NAME ZONE` 🚀
