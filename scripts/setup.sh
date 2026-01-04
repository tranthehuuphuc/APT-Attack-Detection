#!/bin/bash
################################################################################
# APT Attack Detection - Complete Setup Script
# 
# Automated setup from scratch - handles all known issues
# Tested on: Ubuntu 22.04 LTS, Python 3.8
################################################################################

set -e  # Exit on error

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║   APT Attack Detection - Complete Setup                  ║${NC}"
echo -e "${MAGENTA}║   From Zero to Ready                                      ║${NC}"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════╝${NC}"
echo

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}❌ Please do not run as root${NC}"
   echo "Run without sudo. Script will ask for sudo when needed."
   exit 1
fi

# Check if in correct directory
if [ ! -f "README.md" ]; then
    echo -e "${RED}❌ Not in APT-Attack-Detection directory${NC}"
    echo "Please cd to the repository root first"
    exit 1
fi

SETUP_START_TIME=$(date +%s)

# =============================================================================
# STEP 1: System Packages
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}[1/8] Installing System Packages${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

sudo apt update

echo -e "${GREEN}Installing build tools and Python...${NC}"
sudo apt install -y \
  build-essential \
  git \
  wget \
  curl \
  htop \
  tmux \
  vim

# Add Python 3.8 repo if needed
if ! command -v python3.8 &> /dev/null; then
    echo -e "${YELLOW}Adding Python 3.8 repository...${NC}"
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
fi

sudo apt install -y \
  python3.8 \
  python3.8-venv \
  python3.8-dev \
  python3-pip

echo -e "${GREEN}Installing system dependencies...${NC}"
sudo apt install -y \
  libpq-dev \
  graphviz \
  libgraphviz-dev \
  auditd \
  audispd-plugins

echo -e "${GREEN}✓ System packages installed${NC}"
echo

# =============================================================================
# STEP 2: Python Virtual Environment
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}[2/8] Setting Up Python Virtual Environment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Remove old venv if exists
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Removing old virtual environment...${NC}"
    rm -rf .venv
fi

echo -e "${GREEN}Creating new virtual environment...${NC}"
python3.8 -m venv .venv

echo -e "${GREEN}Activating virtual environment...${NC}"
source .venv/bin/activate

echo -e "${GREEN}Upgrading pip, setuptools, wheel...${NC}"
pip install --upgrade pip setuptools wheel

# Downgrade setuptools to avoid PyG build issues
echo -e "${GREEN}Setting compatible setuptools version...${NC}"
pip install setuptools==59.8.0

echo -e "${GREEN}✓ Virtual environment ready${NC}"
echo

# =============================================================================
# STEP 3: Core Python Packages
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}[3/8] Installing Core Python Packages${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo -e "${GREEN}Installing core dependencies...${NC}"
pip install -q -r requirements/core.txt

echo -e "${GREEN}Installing agent dependencies...${NC}"
pip install -q -r requirements/agent.txt

# Fix typing-extensions version conflict
echo -e "${GREEN}Upgrading typing-extensions...${NC}"
pip install --upgrade "typing-extensions>=4.12.2"

echo -e "${GREEN}✓ Core packages installed${NC}"
echo

# =============================================================================
# STEP 4: PyTorch & PyTorch Geometric (Critical - Handle Carefully)
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}[4/8] Installing PyTorch & PyTorch Geometric${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo -e "${GREEN}Installing PyTorch 1.11.0 (CPU version)...${NC}"
pip install --extra-index-url https://download.pytorch.org/whl/cpu \
  torch==1.11.0 \
  torchvision==0.12.0 \
  torchaudio==0.11.0

echo -e "${GREEN}Installing PyTorch Geometric extensions...${NC}"
pip install \
  torch-scatter==2.0.9 \
  torch-sparse==0.6.13 \
  torch-cluster==1.6.0 \
  torch-spline-conv==1.2.1 \
  -f https://data.pyg.org/whl/torch-1.11.0+cpu.html

echo -e "${GREEN}Installing PyTorch Geometric 2.1.0...${NC}"
pip install --no-cache-dir torch-geometric==2.1.0

# Verify PyTorch installation
echo -e "${GREEN}Verifying PyTorch installation...${NC}"
python -c "import torch; print(f'PyTorch: {torch.__version__}')" || {
    echo -e "${RED}❌ PyTorch installation failed${NC}"
    exit 1
}

python -c "import torch_geometric; print(f'PyTorch Geometric: {torch_geometric.__version__}')" || {
    echo -e "${RED}❌ PyTorch Geometric installation failed${NC}"
    exit 1
}

echo -e "${GREEN}✓ PyTorch ecosystem installed${NC}"
echo

# =============================================================================
# STEP 5: GNN Engine Dependencies
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}[5/8] Installing GNN Engine Dependencies${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ -f "src/engine/graph_matcher/engine_repo/requirements.txt" ]; then
    echo -e "${GREEN}Installing engine requirements...${NC}"
    pip install -q -r src/engine/graph_matcher/engine_repo/requirements.txt
    echo -e "${GREEN}✓ Engine dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ Engine requirements not found (skipping)${NC}"
fi

# Install g4f for free LLM backend
echo -e "${GREEN}Installing g4f (free LLM)...${NC}"
pip install -q g4f

echo -e "${GREEN}✓ Additional dependencies installed${NC}"
echo

# Verify all critical imports
echo -e "${GREEN}Verifying all Python packages...${NC}"
python << 'EOF'
try:
    import torch
    import torch_geometric
    import networkx
    import dgl
    import yaml
    import feedparser
    import requests
    from bs4 import BeautifulSoup
    import g4f
    
    print("✅ All critical packages imported successfully")
    print(f"  PyTorch: {torch.__version__}")
    print(f"  PyTorch Geometric: {torch_geometric.__version__}")
    print(f"  NetworkX: {networkx.__version__}")
    print(f"  DGL: {dgl.__version__}")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Python package verification failed${NC}"
    exit 1
fi

echo

# =============================================================================
# STEP 6: Data Setup
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}[6/8] Setting Up Data${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Create directories
echo -e "${GREEN}Creating data directories...${NC}"
mkdir -p data/mitre
mkdir -p data/cti_reports
mkdir -p runs/{events,checkpoints,cti}
mkdir -p data/query_graphs

# Download MITRE ATT&CK
if [ ! -f "data/mitre/enterprise-attack.json" ]; then
    echo -e "${GREEN}Downloading MITRE ATT&CK data...${NC}"
    wget -q https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
      -O data/mitre/enterprise-attack.json
    
    SIZE=$(du -h data/mitre/enterprise-attack.json | cut -f1)
    echo -e "${GREEN}✓ Downloaded MITRE ATT&CK ($SIZE)${NC}"
else
    echo -e "${GREEN}✓ MITRE ATT&CK already exists${NC}"
fi

# Create CTI RSS feeds
if [ ! -f "data/cti_reports/rss_seeds.txt" ]; then
    echo -e "${GREEN}Creating CTI RSS feeds configuration...${NC}"
    cat > data/cti_reports/rss_seeds.txt << 'EOF'
# Government & Official Sources
https://www.cisa.gov/cybersecurity-advisories/all.xml
https://www.us-cert.gov/ncas/current-activity.xml

# Security News
https://www.bleepingcomputer.com/feed/
https://thehackernews.com/feeds/posts/default
https://feeds.feedburner.com/TheHackersNews

# Threat Research
https://www.crowdstrike.com/blog/feed/
https://www.fireeye.com/blog/threat-research.html/feed
EOF
    echo -e "${GREEN}✓ CTI feeds configured${NC}"
else
    echo -e "${GREEN}✓ CTI feeds already exist${NC}"
fi

# Link datasets
if [ -f "scripts/link_tc_datasets.sh" ]; then
    echo -e "${GREEN}Linking DARPA TC datasets...${NC}"
    bash scripts/link_tc_datasets.sh || echo -e "${YELLOW}⚠ Dataset linking returned warnings (OK if datasets don't exist)${NC}"
fi

echo -e "${GREEN}✓ Data setup complete${NC}"
echo

# =============================================================================
# STEP 7: System Services
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}[7/8] Configuring System Services${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Start and enable auditd
echo -e "${GREEN}Configuring auditd...${NC}"
sudo systemctl enable auditd
sudo systemctl start auditd

if systemctl is-active --quiet auditd; then
    echo -e "${GREEN}✓ auditd is running${NC}"
else
    echo -e "${RED}❌ auditd failed to start${NC}"
    exit 1
fi

echo

# =============================================================================
# STEP 8: Verification
# =============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}[8/8] Final Verification${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Make scripts executable
echo -e "${GREEN}Making scripts executable...${NC}"
chmod +x experiments/scenarios/scenario*/attack.sh 2>/dev/null || true
chmod +x experiments/scenarios/cleanup.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

# Run verification script
if [ -f "scripts/verify_system.sh" ]; then
    echo -e "${GREEN}Running system verification...${NC}"
    echo
    bash scripts/verify_system.sh
else
    echo -e "${YELLOW}⚠ Verification script not found (skipping)${NC}"
fi

# Calculate setup time
SETUP_END_TIME=$(date +%s)
SETUP_DURATION=$((SETUP_END_TIME - SETUP_START_TIME))
SETUP_MINUTES=$((SETUP_DURATION / 60))
SETUP_SECONDS=$((SETUP_DURATION % 60))

echo
echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║   Setup Complete!                                         ║${NC}"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════╝${NC}"
echo
echo -e "${GREEN}✅ All components installed and verified${NC}"
echo -e "${BLUE}Setup time: ${SETUP_MINUTES}m ${SETUP_SECONDS}s${NC}"
echo
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Activate environment:"
echo "     source .venv/bin/activate"
echo
echo "  2. Quick test:"
echo "     bash experiments/scenarios/quick_test.sh"
echo
echo "  3. Run full experiments:"
echo "     bash scripts/run_experiments.sh"
echo
echo -e "${YELLOW}Remember: Always activate .venv before running experiments!${NC}"
echo
