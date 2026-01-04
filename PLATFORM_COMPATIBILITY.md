# Platform Compatibility Analysis

## 🖥️ Development vs Production Environment

### Development (macOS M1)
- **OS**: macOS (arm64)
- **Hardware**: MacBook Pro M1, 8 GB RAM
- **Python**: 3.14.2 (detected)
- **Purpose**: Code development, testing

### Production (Ubuntu 22.04 GCP)
- **OS**: Ubuntu 22.04 LTS (x86_64)
- **Hardware**: e2-standard-4 (4 vCPUs, 16 GB Memory)
- **Python**: 3.8-3.11 (recommended 3.8 for compatibility)
- **Purpose**: Experiments, production deployment

---

## ✅ Cross-Platform Compatibility Analysis

### 1. **Python Dependencies**

#### Core Dependencies (Platform Independent)
✅ **100% Compatible**:
- `pyyaml`, `networkx`, `tqdm`, `psutil` - Pure Python
- `feedparser`, `requests`, `beautifulsoup4` - Pure Python
- `openai`, `pydantic`, `tiktoken` - Pure Python

#### PyTorch (Platform Specific)

**macOS M1**:
```bash
# Requires special build for Apple Silicon
pip install torch==1.11.0 torchvision==0.12.0 torchaudio==0.11.0
# Note: May need to use newer version for M1 native support
```

**Ubuntu x86_64**:
```bash
pip install torch==1.11.0+cpu torchvision==0.12.0+cpu torchaudio==0.11.0 \
  --extra-index-url https://download.pytorch.org/whl/cpu
```

⚠️ **ISSUE**: PyTorch 1.11.0 may not have native M1 support
**Solution**: Use different requirements for dev vs prod

#### PyTorch Geometric Dependencies

**macOS M1**:
```bash
# May require building from source or use conda
pip install torch-scatter torch-sparse torch-cluster torch-spline-conv torch-geometric
```

**Ubuntu x86_64**:
```bash
pip install torch-scatter -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
pip install torch-sparse -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
pip install torch-cluster -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
pip install torch-spline-conv -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
pip install torch-geometric
```

⚠️ **ISSUE**: Geometric libs need platform-specific wheels
**Solution**: Separate requirements files

#### DGL (Deep Graph Library)

**macOS M1**:
```bash
# May need to use conda or build from source
pip install dgl==0.6.1  # May fail on M1
```

**Ubuntu x86_64**:
```bash
pip install dgl==0.6.1  # Works fine
```

⚠️ **ISSUE**: DGL 0.6.1 may not support M1
**Solution**: Use newer version on M1, use 0.6.1 on Ubuntu

---

## 🔧 Recommended Setup Strategy

### Strategy 1: **Development on M1 (Recommended)**

Use **newer versions** on M1 for development:
```bash
# macOS M1 - Development
pip install torch torchvision torchaudio  # Latest versions
pip install torch-geometric  # Latest
pip install dgl -f https://data.dgl.ai/wheels/repo.html  # Latest
```

**Benefits**:
- Native M1 support
- Faster development
- Better performance

**Testing**:
- Test business logic on M1
- Final validation on Ubuntu VM/container

### Strategy 2: **Docker for Dev-Prod Parity**

Run Ubuntu container on M1:
```bash
docker run -it --platform linux/amd64 ubuntu:22.04
# Install dependencies matching production
```

**Benefits**:
- Exact environment match
- Early detection of platform issues

**Drawbacks**:
- Slower on M1 (emulation)
- More complex setup

---

## 📦 Recommended Dependency Structure

### Create Platform-Specific Requirements

```
requirements/
├── core.txt              # Platform-independent
├── agent.txt             # Platform-independent
├── g4f.txt               # Platform-independent
├── hunting-macos.txt     # M1 optimized
├── hunting-ubuntu.txt    # Production (current hunting.txt)
└── engine-ubuntu.txt     # Engine deps for Ubuntu
```

### hunting-macos.txt (NEW)
```txt
-r core.txt
# Latest PyTorch for M1
torch>=2.0.0
torchvision>=0.15.0
torchaudio>=2.0.0

# PyG latest
torch-geometric>=2.3.0

# DGL latest
dgl>=1.1.0

# Note: For development only, not for production
```

### hunting-ubuntu.txt (Production)
```txt
-r core.txt
torch==1.11.0+cpu
torchvision==0.12.0+cpu
torchaudio==0.11.0
--find-links https://download.pytorch.org/whl/cpu
torch-scatter -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
torch-sparse -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
torch-cluster -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
torch-spline-conv -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
torch-geometric
```

---

## 🚀 Ubuntu 22.04 Deployment Guide

### Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.8 (for compatibility)
sudo apt install -y python3.8 python3.8-venv python3.8-dev

# Install build tools
sudo apt install -y build-essential git wget curl

# Install system dependencies
sudo apt install -y \
  libpq-dev \
  graphviz \
  libgraphviz-dev
```

### Setup Application

```bash
# Clone or upload repository
cd /opt
sudo git clone <repo_url> APT-Attack-Detection
cd APT-Attack-Detection

# Create virtual environment
python3.8 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel

# Install in order
pip install -r requirements/core.txt
pip install -r requirements/agent.txt
pip install -r requirements/hunting-ubuntu.txt
pip install -r src/engine/graph_matcher/engine_repo/requirements.txt
```

### Setup Auditd (for Real Events)

```bash
# Install auditd
sudo apt install -y auditd audispd-plugins

# Configure audit rules
sudo bash scripts/auditd/setup_auditd.sh

# Start auditd
sudo systemctl enable auditd
sudo systemctl start auditd
```

### Setup Data Directories

```bash
# Create necessary directories
mkdir -p data/mitre
mkdir -p data/cti_reports
mkdir -p runs/events
mkdir -p runs/checkpoints
mkdir -p runs/cti
mkdir -p data/query_graphs

# Download MITRE ATT&CK
wget https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
  -O data/mitre/enterprise-attack.json

# Setup RSS feeds
cat > data/cti_reports/rss_seeds.txt << 'EOF'
https://www.cisa.gov/cybersecurity-advisories/all.xml
https://www.bleepingcomputer.com/feed/
https://thehackernews.com/feeds/posts/default
EOF

# Link datasets
bash scripts/link_tc_datasets.sh
```

---

## ⚙️ Resource Allocation (16 GB RAM)

### Memory Budget

| Component | Memory Usage | Allocation |
|-----------|--------------|------------|
| OS + Services | ~2 GB | Fixed |
| Python Base | ~500 MB | Fixed |
| CTI Agent (LLM) | ~1-2 GB | Variable |
| Training (GNN) | ~4-8 GB | Tunable |
| Hunting Pipeline | ~2-4 GB | Tunable |
| **Buffer** | ~2 GB | Reserve |

### Training Configuration

```bash
# Adjust batch size for 16 GB RAM
python3 -m src.pipeline.train.trainer \
  --dataset cadets \
  --epochs 50 \
  --batch-size 32 \  # Reduce if OOM
  --save runs/checkpoints/model.pt
```

### Hunting Configuration

```yaml
# configs/hunting.yaml
window_seconds: 120  # Reduce for less memory
max_nodes: 100000    # Reduce from 200k to 100k
k_hop: 2             # Keep at 2
```

---

## 🔒 Security Considerations (GCP)

### Firewall Rules

```bash
# Only allow necessary ports
gcloud compute firewall-rules create apt-detection-ssh \
  --allow tcp:22 \
  --source-ranges YOUR_IP/32

# Close all other ports (detection runs locally)
```

### Service Account

```bash
# Run with minimal permissions
sudo useradd -m -s /bin/bash aptdetect
sudo chown -R aptdetect:aptdetect /opt/APT-Attack-Detection
```

---

## ✅ Compatibility Checklist

### Development (macOS M1)

- [ ] Install Python 3.8+ (3.14 works)
- [ ] Install requirements/core.txt
- [ ] Install requirements/agent.txt
- [ ] Install requirements/hunting-macos.txt (use latest PyTorch)
- [ ] Test CTI Agent pipeline
- [ ] Test evaluation scripts
- [ ] Code development & unit tests

### Production (Ubuntu 22.04)

- [ ] Install Python 3.8
- [ ] Install requirements/core.txt
- [ ] Install requirements/agent.txt
- [ ] Install requirements/hunting-ubuntu.txt (exact versions)
- [ ] Install engine requirements
- [ ] Setup auditd
- [ ] Link datasets
- [ ] Test all 3 pipelines
- [ ] Run attack scenarios
- [ ] Monitor resource usage

---

## 🎯 Recommendation

### **Hybrid Approach** (Best Balance)

1. **Development on M1**:
   - Use latest PyTorch/DGL for speed
   - Develop & test business logic
   - Use `requirements/hunting-macos.txt`

2. **CI/CD with Ubuntu Container**:
   - Use Docker with `--platform linux/amd64`
   - Test with production dependencies
   - Catch platform-specific issues early

3. **Final Testing on GCP**:
   - Deploy to e2-standard-4
   - Run full attack scenarios
   - Performance benchmarking

### Quick Setup Commands

**macOS (Development)**:
```bash
pip install -r requirements/core.txt
pip install -r requirements/agent.txt
pip install torch torchvision torchaudio
pip install torch-geometric dgl
```

**Ubuntu 22.04 (Production)**:
```bash
pip install -r requirements/core.txt
pip install -r requirements/agent.txt
pip install -r requirements/hunting.txt  # Use existing file
pip install -r src/engine/graph_matcher/engine_repo/requirements.txt
```

---

## 🚨 Known Issues & Solutions

### Issue 1: PyTorch Geometric on M1
**Error**: `Failed building wheel for torch-scatter`
**Solution**: Use conda or install from source
```bash
conda install pytorch-geometric -c pyg
```

### Issue 2: DGL on M1
**Error**: `dgl 0.6.1 not compatible with M1`
**Solution**: Use newer version
```bash
pip install dgl>=1.1.0
```

### Issue 3: OOM on GCP
**Error**: `CUDA out of memory` or Python killed
**Solution**: Reduce batch size and window size
```python
# configs/hunting.yaml
max_nodes: 50000  # Reduce from 200k
```

---

## 📊 Testing Protocol

1. **Unit Tests** (M1): Business logic
2. **Integration Tests** (Docker): Platform compatibility
3. **System Tests** (GCP): Full scenarios
4. **Performance Tests** (GCP): Benchmarking

---

**Verdict**: ✅ **Repository FULLY Compatible**

With proper dependency management, the system will run on both platforms. Use platform-specific requirements for optimal performance.
