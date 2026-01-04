#!/bin/bash
################################################################################
# System Readiness Verification Script
# 
# Kiểm tra toàn bộ môi trường đã sẵn sàng chạy experiments
################################################################################

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   APT Attack Detection - System Readiness Check          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo

# Check 1: Working directory
echo -e "${BLUE}[1/10] Checking working directory...${NC}"
if [ ! -f "README.md" ]; then
    echo -e "${RED}✗ Not in APT-Attack-Detection directory${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ In correct directory: $(pwd)${NC}"
fi
echo

# Check 2: Python environment
echo -e "${BLUE}[2/10] Checking Python environment...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    ERRORS=$((ERRORS + 1))
else
    source .venv/bin/activate
    PYTHON_VERSION=$(python --version 2>&1)
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
    echo -e "  Python: $PYTHON_VERSION"
fi
echo

# Check 3: Python packages
echo -e "${BLUE}[3/10] Checking Python packages...${NC}"
source .venv/bin/activate 2>/dev/null || true

check_package() {
    local package=$1
    local import_name=${2:-$1}
    
    if python -c "import $import_name" 2>/dev/null; then
        local version=$(python -c "import $import_name; print(getattr($import_name, '__version__', 'unknown'))" 2>/dev/null)
        echo -e "${GREEN}✓ $package ($version)${NC}"
    else
        echo -e "${RED}✗ $package not installed${NC}"
        ERRORS=$((ERRORS + 1))
    fi
}

check_package "torch" "torch"
check_package "torch-geometric" "torch_geometric"
check_package "networkx" "networkx"
check_package "dgl" "dgl"
check_package "pyyaml" "yaml"
check_package "feedparser" "feedparser"
check_package "requests" "requests"
check_package "beautifulsoup4" "bs4"
check_package "g4f" "g4f"

echo

# Check 4: MITRE ATT&CK data
echo -e "${BLUE}[4/10] Checking MITRE ATT&CK data...${NC}"
if [ -f "data/mitre/enterprise-attack.json" ]; then
    SIZE=$(du -h data/mitre/enterprise-attack.json | cut -f1)
    echo -e "${GREEN}✓ MITRE ATT&CK data exists ($SIZE)${NC}"
else
    echo -e "${RED}✗ MITRE ATT&CK data missing${NC}"
    echo -e "${YELLOW}  Run: wget https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json -O data/mitre/enterprise-attack.json${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo

# Check 5: CTI RSS feeds
echo -e "${BLUE}[5/10] Checking CTI RSS feeds...${NC}"
if [ -f "data/cti_reports/rss_seeds.txt" ]; then
    FEED_COUNT=$(grep -v '^#' data/cti_reports/rss_seeds.txt | grep -v '^$' | wc -l)
    echo -e "${GREEN}✓ RSS feeds configured ($FEED_COUNT feeds)${NC}"
else
    echo -e "${YELLOW}⚠ RSS feeds file missing${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo

# Check 6: GNN Engine
echo -e "${BLUE}[6/10] Checking GNN Engine...${NC}"
if [ -d "src/engine/graph_matcher/engine_repo/src" ]; then
    echo -e "${GREEN}✓ Engine repository exists${NC}"
    
    # Check for main.py
    if [ -f "src/engine/graph_matcher/engine_repo/src/main.py" ]; then
        echo -e "${GREEN}✓ Engine main.py found${NC}"
    else
        echo -e "${RED}✗ Engine main.py missing${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}✗ Engine repository missing${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo

# Check 7: Pretrained models
echo -e "${BLUE}[7/10] Checking pretrained models...${NC}"
MODEL_COUNT=$(find src/engine/graph_matcher/engine_repo/model -name "*.pt" 2>/dev/null | wc -l)
if [ $MODEL_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓ Found $MODEL_COUNT pretrained models${NC}"
    
    # Show some models
    echo "  Sample models:"
    find src/engine/graph_matcher/engine_repo/model -name "*.pt" 2>/dev/null | head -3 | while read model; do
        echo "    - $(basename $model)"
    done
else
    echo -e "${RED}✗ No pretrained models found${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo

# Check 8: Datasets
echo -e "${BLUE}[8/10] Checking DARPA TC datasets...${NC}"
DATASET_LINKED=0
for dataset in cadets theia trace; do
    if [ -d "data/datasets/darpa_$dataset" ]; then
        echo -e "${GREEN}✓ Dataset darpa_$dataset linked${NC}"
        DATASET_LINKED=$((DATASET_LINKED + 1))
    else
        echo -e "${YELLOW}⚠ Dataset darpa_$dataset not linked${NC}"
    fi
done

if [ $DATASET_LINKED -eq 0 ]; then
    echo -e "${YELLOW}⚠ No datasets linked (run: bash scripts/link_tc_datasets.sh)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo

# Check 9: Auditd
echo -e "${BLUE}[9/10] Checking auditd...${NC}"
if systemctl is-active --quiet auditd 2>/dev/null; then
    echo -e "${GREEN}✓ auditd is running${NC}"
    
    # Check audit log
    if [ -f "/var/log/audit/audit.log" ]; then
        echo -e "${GREEN}✓ Audit log exists${NC}"
    else
        echo -e "${YELLOW}⚠ Audit log not found${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}✗ auditd not running${NC}"
    echo -e "${YELLOW}  Run: sudo systemctl start auditd${NC}"
    ERRORS=$((ERRORS + 1))
fi
echo

# Check 10: Experiment scripts
echo -e "${BLUE}[10/10] Checking experiment scripts...${NC}"
SCRIPTS_OK=0
SCRIPTS_TOTAL=0

check_script() {
    local script=$1
    SCRIPTS_TOTAL=$((SCRIPTS_TOTAL + 1))
    
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo -e "${GREEN}✓ $script (executable)${NC}"
            SCRIPTS_OK=$((SCRIPTS_OK + 1))
        else
            echo -e "${YELLOW}⚠ $script (not executable)${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo -e "${RED}✗ $script missing${NC}"
        ERRORS=$((ERRORS + 1))
    fi
}

check_script "experiments/scenarios/scenario1_apt29/attack.sh"
check_script "experiments/scenarios/scenario2_apt28/attack.sh"
check_script "experiments/scenarios/scenario3_lazarus/attack.sh"
check_script "experiments/scenarios/cleanup.sh"
check_script "scripts/run_experiments.sh"

echo

# Summary
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Verification Summary                                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
    echo -e "${GREEN}System is ready to run experiments${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Quick test:"
    echo "     bash experiments/scenarios/quick_test.sh"
    echo
    echo "  2. Run full experiments:"
    echo "     bash scripts/run_experiments.sh"
    echo
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  MINOR ISSUES FOUND${NC}"
    echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
    echo
    echo -e "${YELLOW}System should work, but some optional features may not be available${NC}"
    echo -e "${BLUE}You can proceed with experiments${NC}"
    echo
    exit 0
else
    echo -e "${RED}❌ CRITICAL ISSUES FOUND${NC}"
    echo -e "${RED}Errors: $ERRORS${NC}"
    echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
    echo
    echo -e "${RED}Please fix errors before running experiments${NC}"
    echo
    echo -e "${BLUE}Common fixes:${NC}"
    echo "  - Missing packages: pip install -r requirements/core.txt requirements/agent.txt requirements/hunting.txt"
    echo "  - Missing MITRE data: wget https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json -O data/mitre/enterprise-attack.json"
    echo "  - Start auditd: sudo systemctl start auditd"
    echo "  - Link datasets: bash scripts/link_tc_datasets.sh"
    echo
    exit 1
fi
