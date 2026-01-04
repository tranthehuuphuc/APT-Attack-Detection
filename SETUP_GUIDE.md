# 🚀 Complete Setup Script - Quick Guide

## Automated Setup từ A-Z

Script `scripts/setup.sh` tự động setup toàn bộ môi trường, xử lý tất cả issues đã biết.

---

## ⚡ Quick Start

### On Fresh Ubuntu 22.04 VM

```bash
# 1. Clone repo
cd /opt
sudo mkdir -p apt-detection && sudo chown $USER:$USER apt-detection
cd apt-detection
git clone https://github.com/tranthehuuphuc/APT-Attack-Detection.git .

# 2. Run setup script
bash scripts/setup.sh

# Setup takes ~15-20 minutes
# Script will:
# - Install system packages
# - Setup Python 3.8 virtual environment
# - Install all Python packages (correct versions)
# - Download MITRE data
# - Configure CTI feeds
# - Start auditd
# - Verify everything
```

---

## 📋 What Setup Script Does

### 8 Automated Steps

1. **System Packages** (2-3 min)
   - Build tools, git, wget, curl
   - Python 3.8 + development headers
   - System libraries (libpq, graphviz)
   - auditd

2. **Python Virtual Environment** (1 min)
   - Creates .venv with Python 3.8
   - Upgrades pip, setuptools, wheel
   - Sets compatible setuptools version (59.8.0)

3. **Core Python Packages** (2-3 min)
   - Core dependencies (networkx, yaml, etc.)
   - Agent dependencies (feedparser, beautifulsoup4)
   - Fixes typing-extensions conflict

4. **PyTorch & PyTorch Geometric** (5-7 min) ⚠️ **Critical**
   - PyTorch 1.11.0 (CPU) với correct index URL
   - PyTorch Geometric 2.1.0
   - Extensions: scatter, sparse, cluster, spline-conv
   - Specific versions to avoid compatibility issues

5. **GNN Engine Dependencies** (2-3 min)
   - Engine-specific requirements
   - DGL, gensim, pystardog
   - g4f for free LLM

6. **Data Setup** (1-2 min)
   - Downloads MITRE ATT&CK (4MB)
   - Creates CTI RSS feeds configuration
   - Links DARPA TC datasets

7. **System Services** (<1 min)
   - Enables and starts auditd
   - Verifies service running

8. **Verification** (1 min)
   - Makes scripts executable
   - Runs verify_system.sh
   - Shows final status

**Total Time**: ~15-20 minutes

---

## ✅ Success Indicators

Setup script exits with code 0 and shows:

```
╔══════════════════════════════════════════════════════════╗
║   Setup Complete!                                         ║
╚══════════════════════════════════════════════════════════╝

✅ All components installed and verified
Setup time: 18m 34s

Next steps:
  1. Activate environment:
     source .venv/bin/activate

  2. Quick test:
     bash experiments/scenarios/quick_test.sh

  3. Run full experiments:
     bash scripts/run_experiments.sh
```

---

## 🔧 Error Handling

Script automatically handles:
- ✅ PyTorch version conflicts → Uses --extra-index-url
- ✅ PyTorch Geometric build errors → Uses setuptools==59.8.0
- ✅ typing-extensions conflicts → Upgrades to >=4.12.2
- ✅ Missing Python 3.8 → Adds deadsnakes PPA
- ✅ Package order issues → Installs in correct sequence

Script **exits on error** (`set -e`):
- If critical package fails → stops immediately
- Shows error message
- Exit code 1

---

## 📊 Verification

After setup, script runs `verify_system.sh`:
- Checks all 10 components
- Shows detailed status
- Confirms system ready

---

## 🔄 Re-run Setup

Safe to re-run if needed:

```bash
# Clean start (removes .venv)
bash scripts/setup.sh

# Script automatically:
# - Removes old .venv
# - Reinstalls everything
# - Verifies setup
```

---

## 🆘 If Setup Fails

1. **Check error message** - Script shows which step failed

2. **Common fixes**:
   ```bash
   # Ubuntu packages issue
   sudo apt update
   
   # Network issue
   # Check DNS, retry download
   
   # Permission issue
   # Don't run as root, script uses sudo when needed
   ```

3. **Manual verification**:
   ```bash
   source .venv/bin/activate
   python -c "import torch, torch_geometric, networkx, dgl"
   ```

4. **Get help from**:
   - Error output from script
   - `PYTORCH_FIX.md`
   - `PYGEOMETRIC_FIX.md`
   - `VERIFY_SYSTEM.md`

---

## 💡 Pro Tips

1. **Use tmux** to avoid SSH disconnect:
   ```bash
   tmux new -s setup
   bash scripts/setup.sh
   # Ctrl+B, D to detach
   ```

2. **Monitor progress**:
   - Script shows live progress
   - Each step has clear indicators
   - ~15-20 minutes total

3. **After successful setup**:
   ```bash
   # Always activate venv first
   source .venv/bin/activate
   
   # Then run experiments
   bash scripts/run_experiments.sh
   ```

---

## 📝 Comparison

### Before (Manual Setup)
- 30+ commands
- Multiple error fixes needed
- 40-60 minutes
- Easy to miss steps

### After (Automated Setup)
- 1 command: `bash scripts/setup.sh`
- All errors handled automatically
- 15-20 minutes
- Verified complete

---

## ✅ Quick Command Reference

```bash
# Fresh setup
cd /opt/apt-detection
bash scripts/setup.sh

# After setup
source .venv/bin/activate
bash scripts/verify_system.sh
bash scripts/run_experiments.sh
```

---

**Status**: ✅ Ready to use  
**Time**: ~15-20 minutes  
**Command**: `bash scripts/setup.sh` 🚀
