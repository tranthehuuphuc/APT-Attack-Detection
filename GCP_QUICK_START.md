# 🎯 Complete Google Cloud Deployment - Quick Start

## Tổng Quan

Bạn đã có **HOÀN CHỈNH** hướng dẫn để deploy APT Attack Detection lên Google Cloud Platform.

---

## 📁 Files Created

1. **GCP_DEPLOYMENT_GUIDE.md** - Hướng dẫn chi tiết (500+ dòng)
2. **scripts/gcp_helper.sh** - Script tự động hóa

---

## 🚀 Quick Start (3 Bước)

### Bước 1: Cài Đặt Google Cloud CLI (Trên macOS)

```bash
# Cài gcloud CLI
brew install --cask google-cloud-sdk

# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### Bước 2: Tạo VM và Upload Code (Dùng Helper Script)

```bash
cd /Users/tranthehuuphuc/Downloads/APT-Attack-Detection

# Chạy helper script
bash scripts/gcp_helper.sh

# Trong menu chọn:
# 1 - Create VM Instance   (tạo VM e2-standard-4 tự động)
# 3 - Upload code to VM    (upload toàn bộ code lên VM)
# 2 - SSH into VM          (connect vào VM)
```

### Bước 3: Setup và Chạy (Trên VM)

```bash
# Trên VM, chạy commands này:
cd /opt/apt-detection

# Install dependencies
bash << 'EOF'
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential git wget curl python3.8 python3.8-venv python3.8-dev \
  libpq-dev graphviz libgraphviz-dev auditd audispd-plugins

# Setup Python
python3.8 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements/core.txt
pip install -r requirements/agent.txt
pip install -r requirements/hunting.txt
pip install -r src/engine/graph_matcher/engine_repo/requirements.txt

# Setup data
mkdir -p data/mitre
wget https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
  -O data/mitre/enterprise-attack.json

bash scripts/link_tc_datasets.sh

sudo systemctl start auditd
EOF

# Test quick
bash experiments/scenarios/quick_test.sh
# Chọn option 1-7 để test từng phần
```

---

## 📊 Deployment Options

### Option A: Interactive Helper (Recommended)

```bash
# Trên macOS
bash scripts/gcp_helper.sh

# Menu options:
# 1 - Create VM (auto-config)
# 2 - SSH to VM
# 3 - Upload code
# 4 - Download results
# 5 - Start VM
# 6 - Stop VM
```

### Option B: Manual Commands

```bash
# Tạo VM
gcloud compute instances create apt-detection-vm \
  --zone=asia-southeast1-a \
  --machine-type=e2-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB

# SSH
gcloud compute ssh apt-detection-vm --zone=asia-southeast1-a

# Upload code
gcloud compute scp --recurse \
  APT-Attack-Detection \
  apt-detection-vm:/opt/ \
  --zone=asia-southeast1-a
```

---

## 🎓 Full Experimental Workflow

### Timeline: ~3 hours

```
1. Create VM (5 min)
   └─> bash scripts/gcp_helper.sh → option 1

2. Upload code (10 min)
   └─> bash scripts/gcp_helper.sh → option 3

3. SSH and setup (15 min)
   └─> Follow section 3 in GCP_DEPLOYMENT_GUIDE.md

4. Install dependencies (10 min)
   └─> Follow section 4 in GCP_DEPLOYMENT_GUIDE.md

5. Test CTI Agent (5 min)
   └─> python3 -m src.pipeline.agent.main ...

6. Train model (30 min)
   └─> python3 -m src.pipeline.train.trainer ...

7. Run scenarios (80 min)
   └─> bash experiments/scenarios/run_all_scenarios.sh

8. Download results (5 min)
   └─> bash scripts/gcp_helper.sh → option 4

9. Stop VM (1 min)
   └─> bash scripts/gcp_helper.sh → option 6
```

---

## 💰 Cost Management

**e2-standard-4 in asia-southeast1**:
- ~$0.15/hour = ~$110/month
- Disk 100GB: ~$10/month

**Tips tiết kiệm**:
```bash
# Stop khi không dùng (chỉ tính phí disk)
gcloud compute instances stop apt-detection-vm --zone=asia-southeast1-a

# Start lại khi cần
gcloud compute instances start apt-detection-vm --zone=asia-southeast1-a
```

---

## 📋 Checklist

### Pre-Deployment (macOS)
- [ ] Cài gcloud CLI: `brew install --cask google-cloud-sdk`
- [ ] Login: `gcloud auth login`
- [ ] Set project: `gcloud config set project YOUR_PROJECT_ID`
- [ ] Verify: `gcloud config list`

### Deployment
- [ ] Run `bash scripts/gcp_helper.sh`
- [ ] Option 1: Create VM
- [ ] Option 3: Upload code
- [ ] Option 2: SSH to VM

### On VM
- [ ] Install system packages (section 3)
- [ ] Setup Python environment (section 4)
- [ ] Download MITRE data
- [ ] Link datasets
- [ ] Test CTI Agent

### Experiments
- [ ] Train model (30 min)
- [ ] Run Scenario 1 (15 min)
- [ ] Run Scenario 2 (25 min)
- [ ] Run Scenario 3 (35 min)
- [ ] Evaluate results
- [ ] Download to local

### Cleanup
- [ ] Download results: helper option 4
- [ ] Stop VM: helper option 6
- [ ] (Optional) Delete VM: helper option 7

---

## 🔍 Verification

### Test GCP CLI Working

```bash
# Check gcloud installed
gcloud version

# Check current project
gcloud config get-value project

# List VMs
gcloud compute instances list
```

### Test Deployment Working

```bash
# SSH to VM
gcloud compute ssh apt-detection-vm --zone=asia-southeast1-a

# On VM, check setup
cd /opt/apt-detection
source .venv/bin/activate
python -c "import torch, networkx, dgl; print('✅ OK')"
```

---

## 📞 Support

- **Full Guide**: `GCP_DEPLOYMENT_GUIDE.md`
- **Helper Script**: `scripts/gcp_helper.sh`
- **Ubuntu Guide**: `UBUNTU_DEPLOYMENT.md`
- **System Status**: `SYSTEM_STATUS.md`

---

## 🎯 Expected Results

Sau khi deploy thành công:

✅ VM e2-standard-4 running on GCP  
✅ Ubuntu 22.04 with all dependencies  
✅ Python 3.8 + virtual environment  
✅ All code and data uploaded  
✅ CTI Agent tested and working  
✅ Can train models  
✅ Can run attack scenarios  
✅ Can collect metrics  
✅ Can download results  

---

## Quick Commands Reference

```bash
# === On macOS Local ===

# Helper menu
bash scripts/gcp_helper.sh

# Direct SSH
gcloud compute ssh apt-detection-vm --zone=asia-southeast1-a

# Upload file
gcloud compute scp localfile.txt apt-detection-vm:/remote/path/ --zone=asia-southeast1-a

# Download file
gcloud compute scp apt-detection-vm:/remote/file.txt ./ --zone=asia-southeast1-a

# Stop VM
gcloud compute instances stop apt-detection-vm --zone=asia-southeast1-a

# Start VM  
gcloud compute instances start apt-detection-vm --zone=asia-southeast1-a


# === On GCP VM ===

# Quick setup
cd /opt/apt-detection
source .venv/bin/activate

# Interactive test
bash experiments/scenarios/quick_test.sh

# Run all scenarios
bash experiments/scenarios/run_all_scenarios.sh

# Monitor
htop
```

---

**Status**: ✅ Ready to deploy  
**Estimated Time**: 2-3 hours for complete setup  
**Cost**: ~$0.15/hour (~$3-4 for full experiment)  

**Next Step**: `bash scripts/gcp_helper.sh` → Option 1 🚀
