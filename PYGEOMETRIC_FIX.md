# Quick Fix: PyTorch Geometric Compatibility Issue

## Problem
```
AttributeError: 'builtin_function_or_method' object has no attribute 'default'
torch-sparse warning about sparse_csc_tensor
```

## Root Cause
PyTorch Geometric version installed is too new for PyTorch 1.11.0

## Solution

**On VM, run:**

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Uninstall incompatible versions
pip uninstall -y torch-geometric torch-scatter torch-sparse torch-cluster torch-spline-conv

# Install compatible versions for PyTorch 1.11.0
pip install torch-scatter==2.0.9 -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
pip install torch-sparse==0.6.13 -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
pip install torch-cluster==1.6.0 -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
pip install torch-spline-conv==1.2.1 -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
pip install torch-geometric==2.0.4

# Verify
python -c "import torch, torch_geometric; print(f'PyTorch: {torch.__version__}, PyG: {torch_geometric.__version__}')"
```

## One-Liner Fix

```bash
cd /opt/apt-detection && source .venv/bin/activate && pip uninstall -y torch-geometric torch-scatter torch-sparse torch-cluster torch-spline-conv && pip install torch-scatter==2.0.9 torch-sparse==0.6.13 torch-cluster==1.6.0 torch-spline-conv==1.2.1 -f https://data.pyg.org/whl/torch-1.11.0+cpu.html && pip install torch-geometric==2.0.4 && python -c "import torch, torch_geometric, networkx, dgl; print('✅ All OK')"
```

## Verify All Imports

```bash
python << 'EOF'
import torch
import torch_geometric
import networkx
import dgl
import yaml
import feedparser

print("✅ All critical imports successful!")
print(f"PyTorch: {torch.__version__}")
print(f"PyTorch Geometric: {torch_geometric.__version__}")
print(f"NetworkX: {networkx.__version__}")
print(f"DGL: {dgl.__version__}")
EOF
```

## Expected Output
```
✅ All critical imports successful!
PyTorch: 1.11.0+cpu
PyTorch Geometric: 2.0.4
NetworkX: 2.x.x
DGL: 0.6.1
```

## If Still Issues

Try complete reinstall:
```bash
# Remove .venv and start fresh
cd /opt/apt-detection
rm -rf .venv
python3.8 -m venv .venv
source .venv/bin/activate

# Install in correct order
pip install --upgrade pip
pip install -r requirements/core.txt
pip install -r requirements/agent.txt

# Install PyTorch first
pip install --extra-index-url https://download.pytorch.org/whl/cpu torch==1.11.0 torchvision==0.12.0 torchaudio==0.11.0

# Then PyG with specific versions
pip install torch-scatter==2.0.9 torch-sparse==0.6.13 torch-cluster==1.6.0 torch-spline-conv==1.2.1 -f https://data.pyg.org/whl/torch-1.11.0+cpu.html
pip install torch-geometric==2.0.4

# Then engine requirements
pip install -r src/engine/graph_matcher/engine_repo/requirements.txt
pip install g4f typing-extensions
```

---

**Next**: After fix, continue with `NEXT_STEPS.md` Phase 2
