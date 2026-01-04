# 🚀 Ubuntu 22.04 Deployment Guide for APT Attack Detection

## 📋 System Requirements

### Hardware (GCP e2-standard-4)
- **vCPUs**: 4
- **Memory**: 16 GB
- **Disk**: 50 GB minimum (100 GB recommended)
- **Network**: 10 Gbps

### Software
- **OS**: Ubuntu 22.04 LTS (x86_64)
- **Python**: 3.8 (primary), 3.9-3.11 (compatible)
- **Kernel**: 5.15+ (for auditd features)

---

## 🎯 Quick Deployment (15 minutes)

### Step 1: Initial Setup

```bash
# SSH into GCP instance
gcloud compute ssh your-instance-name --zone=your-zone

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.8
sudo apt install -y python3.8 python3.8-venv python3.8-dev python3-pip

# Install system dependencies
sudo apt install -y \
  build-essential \
  git \
  wget \
  curl \
  libpq-dev \
  graphviz \
  libgraphviz-dev \
  auditd \
  audispd-plugins \
  htop \
  tmux
```

### Step 2: Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/apt-detection
sudo chown $USER:$USER /opt/apt-detection
cd /opt/apt-detection

# Clone repository (replace with your repo URL)
git clone https://github.com/your-username/APT-Attack-Detection.git .

# Verify structure
ls -la
```

### Step 3: Setup Python Environment

```bash
# Create virtual environment
python3.8 -m venv .venv

# Activate environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies in order
pip install -r requirements/core.txt
pip install -r requirements/agent.txt  
pip install -r requirements/hunting.txt
pip install -r src/engine/graph_matcher/engine_repo/requirements.txt

# Verify installations
python -c "import torch, networkx, dgl; print('All imports OK')"
```

### Step 4: Setup Data

```bash
# Create directories
mkdir -p data/mitre data/cti_reports runs/{events,checkpoints,cti} data/query_graphs

# Download MITRE ATT&CK
wget https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
  -O data/mitre/enterprise-attack.json

# Create RSS feeds
cat > data/cti_reports/rss_seeds.txt << 'EOF'
https://www.cisa.gov/cybersecurity-advisories/all.xml
https://www.bleepingcomputer.com/feed/
https://thehackernews.com/feeds/posts/default
EOF

# Link datasets
bash scripts/link_tc_datasets.sh

# Verify data
ls -lh data/mitre/enterprise-attack.json
du -sh src/engine/graph_matcher/engine_repo/dataset/
```

### Step 5: Setup Auditd

```bash
# Start auditd
sudo systemctl enable auditd
sudo systemctl start auditd
sudo systemctl status auditd

# Configure audit rules (if setup script exists)
if [ -f scripts/auditd/setup_auditd.sh]; then
  sudo bash scripts/auditd/setup_auditd.sh
fi

# Verify audit is working
sudo ausearch -m SYSCALL -ts recent | head -20
```

---

## 🧪 Testing Deployment

### Test 1: CTI Agent

```bash
source .venv/bin/activate

# Install g4f (free LLM)
pip install -r requirements/g4f.txt

# Run CTI Agent (should take 2-5 minutes)
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --llm-backend g4f \
  --per-source-limit 3

# Check results
cat runs/cti/seeds.json | python3 -m json.tool | head -50
ls -lh runs/cti/
```

### Test 2: Train Model

```bash
# Create sample events if needed
python3 << 'PYEOF'
import json
import time
from pathlib import Path

events = []
for i in range(100):
    events.append({
        "kind": "process_start",
        "ts": time.time() + i,
        "pid": 1000 + i,
        "ppid": 999,
        "exe": "/usr/bin/bash",
        "comm": "bash"
    })

out_dir = Path("runs/events")
out_dir.mkdir(parents=True, exist_ok=True)
with open(out_dir / "test_events.jsonl", "w") as f:
    for ev in events:
        f.write(json.dumps(ev) + "\n")
print(f"Created {len(events)} events")
PYEOF

# Train model (may take 10-30 minutes depending on data)
python3 -m src.pipeline.train.trainer \
  --dataset cadets \
  --epochs 5 \
  --save runs/checkpoints/test_model.pt

# Check checkpoint
ls -lh runs/checkpoints/test_model.pt
```

### Test 3: Run Hunting

```bash
# Run hunting pipeline
python3 -m src.pipeline.hunting.main \
  --dataset cadets \
  --events runs/events/test_events.jsonl \
  --checkpoint runs/checkpoints/test_model.pt \
  --cti-seeds runs/cti/seeds.json

# Check results
ls -lh data/datasets/darpa_cadets/experiments/DEMO/raw/torch_prediction/
```

---

## 🎭 Running Attack Scenarios

### Setup Scenarios

```bash
# Make scripts executable
chmod +x experiments/scenarios/scenario1_apt29/attack.sh
chmod +x experiments/scenarios/cleanup.sh

# Create scenario log directory
sudo mkdir -p /var/log/apt_scenarios
sudo chown $USER:$USER /var/log/apt_scenarios
```

### Run Scenario 1

```bash
# Terminal 1: Monitor auditd
sudo tail -f /var/log/audit/audit.log

# Terminal 2: Run attack
cd /opt/apt-detection
tmux new -s attack

source .venv/bin/activate
bash experiments/scenarios/scenario1_apt29/attack.sh

# Wait for completion (~15 minutes)
```

### Collect & Analyze

```bash
# Collect audit events
python3 -m src.pipeline.hunting.collector \
  --audit-log /var/log/audit/audit.log \
  --out runs/events/scenario1_events.jsonl

# Run hunting
python3 -m src.pipeline.hunting.main \
  --dataset cadets \
  --events runs/events/scenario1_events.jsonl \
  --checkpoint runs/checkpoints/test_model.pt \
  --cti-seeds runs/cti/seeds.json

# Evaluate
python3 -m src.eval.hunting_eval \
  --events runs/events/scenario1_events.jsonl \
  --ground-truth experiments/scenarios/scenario1_apt29/ground_truth.json

# Cleanup
bash experiments/scenarios/cleanup.sh
```

---

## ⚙️ Performance Tuning (16 GB RAM)

### Memory Optimization

Edit `configs/hunting.yaml`:
```yaml
window_seconds: 90        # Reduced from 120
max_nodes: 100000         # Reduced from 200000
k_hop: 2                  # Keep at 2
```

### Training Optimization

For 16 GB RAM, adjust batch size:
```bash
# Edit src/pipeline/train/trainer.py or use custom args
python3 -m src.pipeline.train.trainer \
  --dataset cadets \
  --epochs 50 \
  --batch-size 16 \  # Reduced from default 32
  --save runs/checkpoints/model.pt
```

### Monitor Resources

```bash
# Install monitoring
sudo apt install -y htop nethogs iotop

# Monitor during execution
htop  # CPU & Memory
sudo nethogs  # Network
sudo iotop  # Disk I/O

# Python memory profiling
pip install memory_profiler
python -m memory_profiler your_script.py
```

---

## 🔒 Security Hardening

### Firewall Configuration

```bash
# Enable UFW
sudo ufw allow 22/tcp
sudo ufw enable

# Verify
sudo ufw status
```

### Service Account

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash aptdetect
sudo usermod -aG sudo aptdetect

# Transfer ownership
sudo chown -R aptdetect:aptdetect /opt/apt-detection

# Switch user
sudo su - aptdetect
```

### Auditd Security

```bash
# Secure audit logs
sudo chmod 600 /var/log/audit/audit.log

# Prevent tampering
sudo auditctl -e 2  # Mark configuration immutable

# Verify
sudo auditctl -l
```

---

## 🚨 Troubleshooting

### Issue 1: Out of Memory

**Symptoms**: Process killed, `dmesg` shows OOM
**Solutions**:
```bash
# Reduce batch size
# Reduce max_nodes in hunting.yaml
# Add swap (not ideal but helps)
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue 2: PyTorch Installation Fails

**Symptoms**: `pip install torch` fails
**Solution**:
```bash
# Use exact CPU version
pip install torch==1.11.0+cpu torchvision==0.12.0+cpu \
  --extra-index-url https://download.pytorch.org/whl/cpu
```

### Issue 3: Auditd Not Capturing Events

**Symptoms**: Empty audit.log
**Solution**:
```bash
# Check auditd status
sudo systemctl status auditd

# Check rules
sudo auditctl -l

# Restart auditd
sudo systemctl restart auditd

# Manual test
sudo ausearch -m SYSCALL -ts today
```

### Issue 4: DGL Installation Fails

**Symptoms**: `ImportError: cannot import name 'dgl'`
**Solution**:
```bash
# Try different version
pip uninstall dgl
pip install dgl==0.9.0  # or latest compatible

# Or use conda
conda install -c dglteam dgl
```

---

## 📊 Monitoring & Logging

### Setup Logging

```bash
# Create log directory
sudo mkdir -p /var/log/apt-detection
sudo chown $USER:$USER /var/log/apt-detection

# Configure Python logging
export APT_LOG_DIR=/var/log/apt-detection
export APT_LOG_LEVEL=INFO
```

### Systemd Service (Optional)

Create `/etc/systemd/system/apt-detection.service`:
```ini
[Unit]
Description=APT Attack Detection Service
After=network.target auditd.service

[Service]
Type=simple
User=aptdetect
WorkingDirectory=/opt/apt-detection
Environment="PATH=/opt/apt-detection/.venv/bin"
ExecStart=/opt/apt-detection/.venv/bin/python3 -m src.pipeline.hunting.main \
  --dataset cadets \
  --events /var/log/apt-detection/events.jsonl \
  --checkpoint /opt/apt-detection/runs/checkpoints/production.pt \
  --cti-seeds /opt/apt-detection/runs/cti/seeds.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable apt-detection
sudo systemctl start apt-detection
sudo systemctl status apt-detection
```

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] GCP instance created (e2-standard-4)
- [ ] Ubuntu 22.04 installed
- [ ] SSH access configured
- [ ] Firewall rules set

### Installation
- [ ] Python 3.8 installed
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] MITRE data downloaded
- [ ] Datasets linked

### Configuration
- [ ] Auditd running
- [ ] config files tuned for 16GB RAM
- [ ] Logging configured
- [ ] Service account created

### Testing
- [ ] CTI Agent tested
- [ ] Training tested
- [ ] Hunting tested
- [ ] Evaluation tested

### Scenarios
- [ ] Scenario scripts executable
- [ ] Scenario 1 tested
- [ ] Cleanup verified
- [ ] Ground truth validated

---

## 📈 Performance Benchmarks

### Expected Performance (e2-standard-4)

| Metric | Value |
|--------|-------|
| CTI Processing | 5-10 reports/min |
| Training (10 epochs) | 10-30 minutes |
| Hunting (1K events) | <5 seconds |
| Memory Usage (Training) | 4-8 GB |
| Memory Usage (Hunting) | 2-4 GB |
| Disk I/O | <100 MB/s |

---

## 📞 Support

- **Documentation**: `/opt/apt-detection/*.md`
- **Logs**: `/var/log/apt-detection/`
- **Audit**: `/var/log/audit/audit.log`
- **System**: `journalctl -u apt-detection`

---

**Last Updated**: 2026-01-04  
**Platform**: Ubuntu 22.04 LTS (x86_64)  
**Hardware**: GCP e2-standard-4 (4 vCPUs, 16 GB RAM)
