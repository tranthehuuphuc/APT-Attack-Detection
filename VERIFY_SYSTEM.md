# ✅ System Verification - Quick Guide

## 🎯 Mục Đích

Kiểm tra toàn bộ môi trường đã sẵn sàng chạy experiments.

---

## ⚡ Quick Check (On VM)

```bash
cd /opt/apt-detection
bash scripts/verify_system.sh
```

Script sẽ check:
1. ✅ Working directory
2. ✅ Python environment  
3. ✅ Python packages (torch, dgl, networkx, etc.)
4. ✅ MITRE ATT&CK data
5. ✅ CTI RSS feeds
6. ✅ GNN Engine
7. ✅ Pretrained models
8. ✅ DARPA TC datasets
9. ✅ auditd service
10. ✅ Experiment scripts

---

## 📊 Expected Output

### ✅ All OK
```
╔══════════════════════════════════════════════════════════╗
║   Verification Summary                                    ║
╚══════════════════════════════════════════════════════════╝

✅ ALL CHECKS PASSED!
System is ready to run experiments

Next steps:
  1. Quick test:
     bash experiments/scenarios/quick_test.sh

  2. Run full experiments:
     bash scripts/run_experiments.sh
```

### ⚠️ Warnings Only
```
⚠️  MINOR ISSUES FOUND
Warnings: 2

System should work, but some optional features may not be available
You can proceed with experiments
```

### ❌ Critical Errors
```
❌ CRITICAL ISSUES FOUND
Errors: 3
Warnings: 1

Please fix errors before running experiments

Common fixes:
  - Missing packages: pip install -r requirements/...
  - Missing MITRE data: wget ...
  - Start auditd: sudo systemctl start auditd
```

---

## 🔧 Manual Verification

### 1. Check Python Packages

```bash
cd /opt/apt-detection
source .venv/bin/activate

python << 'EOF'
import torch
import torch_geometric
import networkx
import dgl
import yaml
import feedparser
import g4f

print("✅ All imports successful!")
print(f"PyTorch: {torch.__version__}")
print(f"PyTorch Geometric: {torch_geometric.__version__}")
print(f"NetworkX: {networkx.__version__}")
print(f"DGL: {dgl.__version__}")
EOF
```

### 2. Check Data Files

```bash
# MITRE ATT&CK
ls -lh data/mitre/enterprise-attack.json

# RSS feeds
cat data/cti_reports/rss_seeds.txt

# Expected: 3+ RSS feed URLs
```

### 3. Check Pretrained Models

```bash
# List models
find src/engine/graph_matcher/engine_repo/model -name "*.pt"

# Should show multiple .pt files
# Example:
# src/engine/graph_matcher/engine_repo/model/megrapt/darpa_cadets/...pt
# src/engine/graph_matcher/engine_repo/model/megrapt/darpa_theia/...pt
```

### 4. Check Datasets

```bash
# Check linked datasets
ls -l data/datasets/

# Should show:
# darpa_cadets -> ../src/engine/graph_matcher/engine_repo/dataset/darpa_cadets
# darpa_theia -> ...
# darpa_trace -> ...
```

### 5. Check Auditd

```bash
# Status
sudo systemctl status auditd

# Should show: active (running)

# Check log
sudo tail /var/log/audit/audit.log

# Should show recent audit events
```

### 6. Check Experiment Scripts

```bash
# List scripts
ls -lh experiments/scenarios/scenario*/attack.sh
ls -lh scripts/run_experiments.sh

# All should be executable (-rwxr-xr-x)
```

---

## 🛠️ Common Fixes

### Fix 1: Missing Python Packages

```bash
cd /opt/apt-detection
source .venv/bin/activate

pip install -r requirements/core.txt
pip install -r requirements/agent.txt
pip install setuptools==59.8.0
pip install torch-scatter==2.0.9 torch-sparse==0.6.13 torch-cluster==1.6.0 torch-spline-conv==1.2.1 -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
pip install torch-geometric==2.1.0
pip install -r src/engine/graph_matcher/engine_repo/requirements.txt
pip install g4f typing-extensions
```

### Fix 2: Missing MITRE Data

```bash
mkdir -p data/mitre
wget https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
  -O data/mitre/enterprise-attack.json
```

### Fix 3: Missing RSS Feeds

```bash
mkdir -p data/cti_reports
cat > data/cti_reports/rss_seeds.txt << 'EOF'
https://www.cisa.gov/cybersecurity-advisories/all.xml
https://www.bleepingcomputer.com/feed/
https://thehackernews.com/feeds/posts/default
EOF
```

### Fix 4: Auditd Not Running

```bash
sudo systemctl enable auditd
sudo systemctl start auditd
sudo systemctl status auditd
```

### Fix 5: Link Datasets

```bash
cd /opt/apt-detection
bash scripts/link_tc_datasets.sh
```

### Fix 6: Make Scripts Executable

```bash
chmod +x experiments/scenarios/scenario*/attack.sh
chmod +x experiments/scenarios/cleanup.sh
chmod +x scripts/run_experiments.sh
chmod +x scripts/verify_system.sh
```

---

## ✅ Complete Verification Checklist

- [ ] `bash scripts/verify_system.sh` returns all OK
- [ ] All Python packages import successfully
- [ ] MITRE ATT&CK data exists and valid
- [ ] Pretrained models found (>0 .pt files)
- [ ] auditd is running
- [ ] Experiment scripts are executable
- [ ] Can run quick test without errors

---

## 🚀 After Verification

If all checks pass:

```bash
# Option 1: Quick test
bash experiments/scenarios/quick_test.sh

# Option 2: Run full experiments  
bash scripts/run_experiments.sh
```

---

## 📞 If Issues Persist

1. Check detailed log from verify_system.sh
2. Review error messages
3. Consult:
   - `PYTORCH_FIX.md` for PyTorch issues
   - `PYGEOMETRIC_FIX.md` for PyG issues
   - `NEXT_STEPS.md` for setup steps

---

**Quick Command**: `bash scripts/verify_system.sh` ✅
