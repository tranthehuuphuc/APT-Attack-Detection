# 🚀 Google Cloud Platform Deployment Guide

## Hướng dẫn triển khai APT Attack Detection lên Google Cloud

**Môi trường**: Ubuntu 22.04 LTS, e2-standard-4 (4 vCPUs, 16GB RAM)

---

## 📋 Mục Lục

1. [Chuẩn Bị Google Cloud](#1-chuẩn-bị-google-cloud)
2. [Tạo VM Instance](#2-tạo-vm-instance)
3. [Kết Nối và Cài Đặt Cơ Bản](#3-kết-nối-và-cài-đặt-cơ-bản)
4. [Deploy Application](#4-deploy-application)
5. [Chạy Thử Nghiệm](#5-chạy-thử-nghiệm)
6. [Monitoring & Logging](#6-monitoring--logging)
7. [Troubleshooting](#7-troubleshooting)

---

## 1️⃣ Chuẩn Bị Google Cloud

### 1.1 Cài Đặt Google Cloud CLI (trên máy local)

**macOS**:
```bash
# Cài đặt gcloud CLI
brew install --cask google-cloud-sdk

# Hoặc download từ: https://cloud.google.com/sdk/docs/install
```

**Linux/Windows**: 
- Tải từ: https://cloud.google.com/sdk/docs/install

### 1.2 Đăng Nhập và Config

```bash
# Đăng nhập
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Xem project hiện tại
gcloud config get-value project

# List các zones có sẵn (chọn gần bạn nhất)
gcloud compute zones list | grep asia
```

### 1.3 Enable APIs Cần Thiết

```bash
# Enable Compute Engine API
gcloud services enable compute.googleapis.com

# Enable Cloud Logging API
gcloud services enable logging.googleapis.com

# Enable Cloud Monitoring API  
gcloud services enable monitoring.googleapis.com
```

---

## 2️⃣ Tạo VM Instance

### Option 1: Qua Console (Web UI) - Dễ Nhất

1. Truy cập: https://console.cloud.google.com/compute/instances
2. Click **"CREATE INSTANCE"**
3. Điền thông tin:
   - **Name**: `apt-detection-vm`
   - **Region**: `asia-southeast1` (Singapore) hoặc gần bạn
   - **Zone**: `asia-southeast1-a`
   - **Machine configuration**: 
     - Series: **E2**
     - Machine type: **e2-standard-4** (4 vCPUs, 16GB memory)
   - **Boot disk**:
     - Click **"CHANGE"**
     - Operating system: **Ubuntu**
     - Version: **Ubuntu 22.04 LTS**
     - Boot disk type: **Balanced persistent disk**
     - Size: **100 GB**
   - **Firewall**:
     - ✅ Allow HTTP traffic (nếu cần web interface)
     - ✅ Allow HTTPS traffic
4. Click **"CREATE"**

### Option 2: Qua Command Line - Nhanh Hơn

```bash
# Tạo VM instance
gcloud compute instances create apt-detection-vm \
  --zone=asia-southeast1-a \
  --machine-type=e2-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-balanced \
  --tags=http-server,https-server

# Xem instance đã tạo
gcloud compute instances list
```

### 2.1 Configure Firewall (nếu cần)

```bash
# Cho phép SSH (mặc định đã có)
gcloud compute firewall-rules create allow-ssh \
  --allow tcp:22 \
  --source-ranges=0.0.0.0/0 \
  --description="Allow SSH from anywhere"

# Nếu muốn restrict SSH chỉ từ IP của bạn
gcloud compute firewall-rules create allow-ssh-myip \
  --allow tcp:22 \
  --source-ranges=YOUR_IP_ADDRESS/32 \
  --description="Allow SSH from my IP only"
```

---

## 3️⃣ Kết Nối và Cài Đặt Cơ Bản

### 3.1 SSH vào VM

**Option 1: Qua gcloud CLI (Recommended)**:
```bash
# SSH vào VM
gcloud compute ssh apt-detection-vm --zone=asia-southeast1-a

# Hoặc với port forwarding (nếu cần Jupyter)
gcloud compute ssh apt-detection-vm --zone=asia-southeast1-a -- -L 8888:localhost:8888
```

**Option 2: Qua Console**:
- Vào https://console.cloud.google.com/compute/instances
- Click nút **"SSH"** bên cạnh instance

### 3.2 Update System

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y \
  build-essential \
  git \
  wget \
  curl \
  htop \
  tmux \
  vim \
  python3.8 \
  python3.8-venv \
  python3.8-dev \
  python3-pip
```

### 3.3 Cài Đặt Dependencies Hệ Thống

```bash
# Dependencies cho PyTorch Geometric
sudo apt install -y \
  libpq-dev \
  graphviz \
  libgraphviz-dev

# Auditd cho event collection
sudo apt install -y auditd audispd-plugins

# Start auditd
sudo systemctl enable auditd
sudo systemctl start auditd
sudo systemctl status auditd
```

---

## 4️⃣ Deploy Application

### 4.1 Clone Repository

```bash
# Tạo thư mục application
sudo mkdir -p /opt/apt-detection
sudo chown $USER:$USER /opt/apt-detection

# Clone repo (từ local hoặc GitHub)
cd /opt/apt-detection

# Option A: Nếu đã push lên GitHub
git clone https://github.com/YOUR_USERNAME/APT-Attack-Detection.git .

# Option B: Upload từ máy local
# (Trên máy local):
# gcloud compute scp --recurse APT-Attack-Detection apt-detection-vm:/opt/apt-detection/
```

### 4.2 Upload Code từ macOS Local

Nếu chưa có trên GitHub, upload từ máy Mac:

```bash
# Trên máy Mac của bạn
cd /Users/tranthehuuphuc/Downloads

# Compress code
tar -czf apt-detection.tar.gz APT-Attack-Detection/

# Upload lên GCP VM
gcloud compute scp apt-detection.tar.gz apt-detection-vm:/tmp/ --zone=asia-southeast1-a

# SSH vào VM và extract
gcloud compute ssh apt-detection-vm --zone=asia-southeast1-a

# Trên VM:
cd /opt
sudo mkdir -p apt-detection
sudo chown $USER:$USER apt-detection
cd apt-detection
tar -xzf /tmp/apt-detection.tar.gz --strip-components=1
rm /tmp/apt-detection.tar.gz
```

### 4.3 Setup Python Environment

```bash
cd /opt/apt-detection

# Tạo virtual environment
python3.8 -m venv .venv

# Activate
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements/core.txt
pip install -r requirements/agent.txt
pip install -r requirements/hunting.txt

# Install engine dependencies
pip install -r src/engine/graph_matcher/engine_repo/requirements.txt

# Verify
python -c "import torch, networkx, dgl; print('✅ All imports OK')"
```

### 4.4 Setup Data

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

# Link datasets (engine đã có sẵn)
bash scripts/link_tc_datasets.sh
```

---

## 5️⃣ Chạy Thử Nghiệm

### 5.1 Test CTI Agent (Quick Test - 5 phút)

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Install g4f cho free LLM
pip install -r requirements/g4f.txt

# Run CTI Agent
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --llm-backend g4f \
  --per-source-limit 3

# Check results
cat runs/cti/seeds.json | python3 -m json.tool | head -50
```

### 5.2 Train Model (30 phút)

```bash
# Train GNN model
python3 -m src.pipeline.train.trainer \
  --dataset cadets \
  --epochs 50 \
  --save runs/checkpoints/cadets_model.pt

# Verify checkpoint
ls -lh runs/checkpoints/
```

### 5.3 Chạy Attack Scenario 1 (15 phút)

```bash
# Use tmux để chạy background
tmux new -s attack

# Run scenario
bash experiments/scenarios/scenario1_apt29/attack.sh

# Detach: Ctrl+B, D
# Reattach: tmux attach -t attack
```

### 5.4 Collect Events và Run Hunting

```bash
# Collect events
python3 -m src.pipeline.hunting.collector \
  --audit-log /var/log/audit/audit.log \
  --out runs/events/scenario1_events.jsonl

# Run hunting
python3 -m src.pipeline.hunting.main \
  --dataset cadets \
  --events runs/events/scenario1_events.jsonl \
  --checkpoint runs/checkpoints/cadets_model.pt \
  --cti-seeds runs/cti/seeds.json

# Evaluate
python3 -m src.eval.hunting_eval \
  --events runs/events/scenario1_events.jsonl \
  --ground-truth experiments/scenarios/scenario1_apt29/ground_truth.json
```

### 5.5 Run All Scenarios (Automated - 80 phút)

```bash
# Run tất cả scenarios
bash experiments/scenarios/run_all_scenarios.sh

# Results sẽ ở:
ls -ltr runs/scenario_results/
```

---

## 6️⃣ Monitoring & Logging

### 6.1 Monitor Resources

**Terminal 1 - System Monitor**:
```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Monitor CPU/Memory
htop

# Monitor disk I/O
sudo iotop

# Monitor network
sudo nethogs
```

**Terminal 2 - Application Logs**:
```bash
# Tail audit log
sudo tail -f /var/log/audit/audit.log

# Tail application logs
tail -f runs/scenario_results/*/suite_summary.txt
```

### 6.2 Setup Cloud Logging (Optional)

```bash
# Install logging agent
curl -sSO https://dl.google.com/cloudagents/add-logging-agent-repo.sh
sudo bash add-logging-agent-repo.sh
sudo apt update
sudo apt install -y google-fluentd

# Start logging agent
sudo service google-fluentd start

# View logs in Cloud Console:
# https://console.cloud.google.com/logs
```

### 6.3 Performance Monitoring Script

```bash
# Tạo monitoring script
cat > /opt/apt-detection/monitor.sh << 'EOF'
#!/bin/bash
while true; do
  echo "=== $(date) ==="
  echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
  echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
  echo "Disk: $(df -h / | grep / | awk '{print $3 "/" $2}')"
  echo "---"
  sleep 60
done
EOF

chmod +x /opt/apt-detection/monitor.sh

# Run in background
nohup /opt/apt-detection/monitor.sh > /opt/apt-detection/monitor.log 2>&1 &
```

---

## 7️⃣ Troubleshooting

### Issue 1: Out of Memory

**Triệu chứng**: Process bị killed, `dmesg | tail` shows OOM
**Giải pháp**:
```bash
# Giảm batch size
# Edit configs/hunting.yaml:
# max_nodes: 100000 → 50000

# Add swap (temporary solution)
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Verify
free -h
```

### Issue 2: SSH Connection Lost

**Giải pháp**:
```bash
# Use tmux để tránh mất session
tmux new -s main

# Detach: Ctrl+B, D
# Reconnect:
gcloud compute ssh apt-detection-vm --zone=asia-southeast1-a
tmux attach -t main
```

### Issue 3: Slow Performance

**Kiểm tra**:
```bash
# Check CPU throttling
cat /proc/cpuinfo | grep MHz

# Check disk I/O
iostat -x 1

# Check network
iftop

# Upgrade to n2-standard-4 nếu cần
gcloud compute instances stop apt-detection-vm --zone=asia-southeast1-a
gcloud compute instances set-machine-type apt-detection-vm \
  --machine-type=n2-standard-4 \
  --zone=asia-southeast1-a
gcloud compute instances start apt-detection-vm --zone=asia-southeast1-a
```

### Issue 4: Auditd Not Working

**Giải pháp**:
```bash
# Check status
sudo systemctl status auditd

# Restart
sudo systemctl restart auditd

# Check rules
sudo auditctl -l

# Manual test
sudo ausearch -ts recent

# If nothing shows up
sudo auditctl -w /tmp -p wa -k test_key
touch /tmp/test_file
sudo ausearch -k test_key
```

---

## 8️⃣ Automation Scripts

### 8.1 Startup Script (Chạy khi VM boot)

```bash
# Create startup script
sudo tee /opt/apt-detection/startup.sh > /dev/null << 'EOF'
#!/bin/bash
# Wait for network
sleep 10

# Activate venv
cd /opt/apt-detection
source .venv/bin/activate

# Start monitoring
nohup /opt/apt-detection/monitor.sh > /opt/apt-detection/monitor.log 2>&1 &

# Start auditd
sudo systemctl start auditd

echo "APT Detection VM ready at $(date)"
EOF

chmod +x /opt/apt-detection/startup.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "@reboot /opt/apt-detection/startup.sh") | crontab -
```

### 8.2 Quick Test Script

```bash
cat > /opt/apt-detection/quick-test.sh << 'EOF'
#!/bin/bash
cd /opt/apt-detection
source .venv/bin/activate

echo "Running interactive test menu..."
bash experiments/scenarios/quick_test.sh
EOF

chmod +x /opt/apt-detection/quick-test.sh

# Usage:
# /opt/apt-detection/quick-test.sh
```

---

## 9️⃣ Data Transfer

### Download Results về Local

```bash
# Trên máy Mac local
# Download toàn bộ results
gcloud compute scp --recurse \
  apt-detection-vm:/opt/apt-detection/runs/scenario_results/ \
  ~/Downloads/apt-results/ \
  --zone=asia-southeast1-a

# Download specific files
gcloud compute scp \
  apt-detection-vm:/opt/apt-detection/runs/cti/seeds.json \
  ~/Downloads/ \
  --zone=asia-southeast1-a
```

### Upload Files lên VM

```bash
# Upload checkpoint
gcloud compute scp \
  ~/Downloads/pretrained_model.pt \
  apt-detection-vm:/opt/apt-detection/runs/checkpoints/ \
  --zone=asia-southeast1-a
```

---

## 🔟 Cost Management

### Ước Tính Chi Phí

**e2-standard-4** trong region `asia-southeast1`:
- **On-demand**: ~$0.15/hour = ~$110/month
- **Preemptible**: ~$0.04/hour = ~$30/month (có thể bị shutdown)

**Disk** (100GB balanced):
- ~$10/month

### Tiết Kiệm Chi Phí

**1. Stop VM khi không dùng**:
```bash
# Stop VM
gcloud compute instances stop apt-detection-vm --zone=asia-southeast1-a

# Start lại khi cần
gcloud compute instances start apt-detection-vm --zone=asia-southeast1-a
```

**2. Sử dụng Scheduled Shutdown**:
```bash
# Auto-shutdown lúc 11pm every day
gcloud compute instances add-metadata apt-detection-vm \
  --metadata shutdown-time="23:00" \
  --zone=asia-southeast1-a

# Create cron job on VM
(crontab -l 2>/dev/null; echo "0 23 * * * sudo shutdown -h now") | crontab -
```

**3. Sử dụng Preemptible VM** (rẻ hơn 70% nhưng có thể bị shutdown):
```bash
gcloud compute instances create apt-detection-vm-preempt \
  --zone=asia-southeast1-a \
  --machine-type=e2-standard-4 \
  --preemptible \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB
```

---

## 📊 Quick Reference Commands

```bash
# SSH vào VM
gcloud compute ssh apt-detection-vm --zone=asia-southeast1-a

# Activate environment
cd /opt/apt-detection && source .venv/bin/activate

# Run quick test
bash experiments/scenarios/quick_test.sh

# Run all scenarios
bash experiments/scenarios/run_all_scenarios.sh

# Stop VM
gcloud compute instances stop apt-detection-vm --zone=asia-southeast1-a

# Start VM
gcloud compute instances start apt-detection-vm --zone=asia-southeast1-a

# Delete VM (careful!)
gcloud compute instances delete apt-detection-vm --zone=asia-southeast1-a

# View VM info
gcloud compute instances describe apt-detection-vm --zone=asia-southeast1-a
```

---

## ✅ Deployment Checklist

### Initial Setup
- [ ] Cài gcloud CLI trên máy local
- [ ] Login và set project
- [ ] Enable required APIs
- [ ] Tạo VM instance (e2-standard-4, Ubuntu 22.04, 100GB)
- [ ] Configure firewall rules

### VM Setup
- [ ] SSH vào VM
- [ ] Update system packages
- [ ] Install Python 3.8 và dependencies
- [ ] Install auditd
- [ ] Upload/clone code
- [ ] Create virtual environment
- [ ] Install Python packages

### Data Setup
- [ ] Download MITRE ATT&CK data
- [ ] Setup RSS feeds
- [ ] Link datasets
- [ ] Verify engine repository

### Testing
- [ ] Test CTI Agent
- [ ] Train model
- [ ] Run scenario 1
- [ ] Collect events và hunting
- [ ] Evaluate results

### Production
- [ ] Setup monitoring
- [ ] Configure auto-startup
- [ ] Test backup/restore
- [ ] Document findings

---

## 📞 Support

- **GCP Documentation**: https://cloud.google.com/compute/docs
- **Project Documentation**: `UBUNTU_DEPLOYMENT.md`, `SYSTEM_STATUS.md`
- **Troubleshooting**: `PLATFORM_COMPATIBILITY.md`

---

**Last Updated**: 2026-01-04  
**Tested On**: GCP e2-standard-4, Ubuntu 22.04 LTS  
**Region**: asia-southeast1 (Singapore)
