# 🔧 PyTorch Installation Fix for Ubuntu

## Problem

Error when installing `requirements/hunting.txt`:
```
ERROR: Could not find a version that satisfies the requirement torch==1.11.0+cpu
ERROR: No matching distribution found for torch==1.11.0+cpu
```

## Solution

### Quick Fix (On VM)

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Install PyTorch separately with correct index
pip install --extra-index-url https://download.pytorch.org/whl/cpu \
  torch==1.11.0 \
  torchvision==0.12.0 \
  torchaudio==0.11.0

# Install PyTorch Geometric extensions
pip install torch-scatter torch-sparse torch-cluster torch-spline-conv torch-geometric \
  -f https://data.pyg.org/whl/torch-1.11.0+cpu.html

# Install other requirements
pip install -r requirements/core.txt
pip install -r requirements/agent.txt
pip install -r src/engine/graph_matcher/engine_repo/requirements.txt
pip install g4f

# Verify
python -c "import torch, torch_geometric; print('✅ PyTorch OK')"
```

## What Changed

**Fixed `requirements/hunting.txt`**:
- Changed `torch==1.11.0+cpu` → `torch==1.11.0`
- Changed `torchvision==0.12.0+cpu` → `torchvision==0.12.0`
- Changed `--find-links` → `--extra-index-url`

**Why**: PyPI doesn't recognize `+cpu` suffix directly. Need to use PyTorch's extra index URL.

## Updated Files

1. ✅ `requirements/hunting.txt` - Fixed PyTorch versions
2. ✅ `NEXT_STEPS.md` - Added fallback installation method

## Pull Latest Changes

```bash
# On local Mac (if needed)
cd /Users/tranthehuuphuc/Downloads/APT-Attack-Detection
git pull

# Push to GitHub
git add .
git commit -m "Fix PyTorch installation for Ubuntu"
git push

# On VM - pull updates
cd /opt/apt-detection
git pull
```

## Continue Setup

After fixing PyTorch installation, continue with setup:

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Complete data setup
mkdir -p data/mitre
wget -q https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
  -O data/mitre/enterprise-attack.json

cat > data/cti_reports/rss_seeds.txt << 'EOF'
https://www.cisa.gov/cybersecurity-advisories/all.xml
https://www.bleepingcomputer.com/feed/
https://thehackernews.com/feeds/posts/default
EOF

bash scripts/link_tc_datasets.sh

sudo systemctl start auditd

# Verify everything
python -c "import torch, networkx, dgl; print('✅ All OK')"
```

## Alternative: Use Newer PyTorch

If PyTorch 1.11.0 continues to have issues:

```bash
# Option: Use PyTorch 2.0+ (may require code adjustments)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install torch-scatter torch-sparse torch-cluster torch-spline-conv torch-geometric
```

**Note**: Engine repo expects PyTorch 1.11.0, so stick with that if possible.

---

**Status**: ✅ Fixed
**Continue**: Back to `NEXT_STEPS.md` Phase 1, Step 1.3
