#!/bin/bash
################################################################################
# Run Complete Experiments - With Pretrained Models
# 
# Chạy đầy đủ: CTI Agent + 3 Attack Scenarios
# NO TRAINING REQUIRED - Uses pretrained models
################################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
NC='\033[0m'

cd "$(dirname "$0")/.."

echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║   APT Attack Detection - Complete Experiment Suite      ║${NC}"
echo -e "${MAGENTA}║   Using Pretrained Models (No Training Required)        ║${NC}"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════╝${NC}"
echo

# Check environment
if [ ! -f ".venv/bin/activate" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Run setup first: see DEPLOY_TO_EXISTING_VM.md"
    exit 1
fi

source .venv/bin/activate

# Check pretrained models
echo -e "${BLUE}[*] Checking pretrained models...${NC}"
CHECKPOINT=$(find src/engine/graph_matcher/engine_repo/ -name "*.pt" -o -name "*.pth" 2>/dev/null | head -1)

if [ -z "$CHECKPOINT" ]; then
    echo -e "${RED}❌ No pretrained model found${NC}"
    echo "Expected location: src/engine/graph_matcher/engine_repo/"
    exit 1
fi

echo -e "${GREEN}✅ Found pretrained model: $CHECKPOINT${NC}"
echo

# Check auditd
echo -e "${BLUE}[*] Checking auditd...${NC}"
if ! sudo systemctl is-active --quiet auditd; then
    echo -e "${YELLOW}⚠️  auditd not running, starting...${NC}"
    sudo systemctl start auditd
fi
echo -e "${GREEN}✅ auditd running${NC}"
echo

# Create results timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="runs/experiments_$TIMESTAMP"
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}Results will be saved to: $RESULTS_DIR${NC}"
echo

# Phase 1: CTI Agent
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  PHASE 1: CTI Agent Evaluation                            ${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo

if [ ! -f "requirements/g4f.txt" ]; then
    echo -e "${YELLOW}[!] Creating g4f requirements...${NC}"
    echo "g4f>=0.1.0" > requirements/g4f.txt
fi

pip install -q -r requirements/g4f.txt 2>/dev/null || echo "g4f already installed"

echo -e "${GREEN}[*] Running CTI Agent...${NC}"
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --out-cti runs/cti \
  --out-qg data/query_graphs \
  --llm-backend g4f \
  --per-source-limit 10 \
  2>&1 | tee "$RESULTS_DIR/cti_agent.log"

# Quick stats
if [ -f "runs/cti/seeds.json" ]; then
    TECH_COUNT=$(cat runs/cti/seeds.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('techniques',[])))")
    IND_COUNT=$(cat runs/cti/seeds.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('indicators',[])))")
    
    echo
    echo -e "${GREEN}✅ CTI Agent Complete${NC}"
    echo -e "   Techniques: $TECH_COUNT"
    echo -e "   Indicators: $IND_COUNT"
    
    # Save summary
    cat > "$RESULTS_DIR/cti_summary.txt" << EOF
CTI Agent Results
=================
Techniques Extracted: $TECH_COUNT
Indicators Identified: $IND_COUNT
Query Graphs Generated: $(ls data/query_graphs/*.json 2>/dev/null | wc -l)
EOF
else
    echo -e "${RED}❌ CTI Agent failed${NC}"
    exit 1
fi

echo
read -t 5 -p "Press Enter to continue to attack scenarios (auto-continue in 5s)..." || true
echo

# Phase 2-4: Attack Scenarios
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  PHASE 2-4: Attack Scenarios with Pretrained Models       ${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo

# Run all scenarios
echo -e "${GREEN}[*] Running all 3 attack scenarios...${NC}"
echo -e "${YELLOW}[!] This will take ~80 minutes total${NC}"
echo

bash experiments/scenarios/run_all_scenarios.sh 2>&1 | tee "$RESULTS_DIR/scenarios.log"

# Phase 5: Analysis
echo
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  PHASE 5: Results Analysis                                ${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo

# Find scenario results
SCENARIO_RESULTS=$(ls -td runs/scenario_results/*/ 2>/dev/null | head -1)

if [ -n "$SCENARIO_RESULTS" ]; then
    echo -e "${GREEN}[*] Analyzing results from: $SCENARIO_RESULTS${NC}"
    
    # Copy results
    cp -r "$SCENARIO_RESULTS" "$RESULTS_DIR/scenario_results/"
    
    # Generate summary
    python3 << 'EOF' | tee "$RESULTS_DIR/final_summary.txt"
import json
from pathlib import Path
import sys

# Find latest scenario results
results_dirs = sorted(Path('runs/scenario_results').glob('*/'), reverse=True)
if not results_dirs:
    print("No scenario results found")
    sys.exit(1)

latest = results_dirs[0]
print(f"\n{'=' * 70}")
print(f"EXPERIMENT RESULTS SUMMARY - {latest.name}")
print(f"{'=' * 70}\n")

# Load scenario results
for i in [1, 2, 3]:
    eval_file = latest / f"scenario{i}_eval.json"
    
    scenario_names = {1: "APT29 (Supply Chain)", 2: "APT28 (Lateral Movement)", 3: "Lazarus (Advanced APT)"}
    
    print(f"{'─' * 70}")
    print(f"Scenario {i}: {scenario_names[i]}")
    print(f"{'─' * 70}")
    
    if eval_file.exists():
        try:
            data = json.loads(eval_file.read_text())
            
            if 'detection_metrics' in data:
                dm = data['detection_metrics']
                print(f"  Detection Rate: {dm.get('detection_rate', 0):.1%}")
                print(f"  Precision:      {dm.get('precision', 0):.3f}")
                print(f"  Recall:         {dm.get('recall', 0):.3f}")
                print(f"  F1-Score:       {dm.get('f1_score', 0):.3f}")
                print(f"  FPR:            {dm.get('false_positive_rate', 0):.1%}")
            else:
                print("  (Evaluation metrics not available)")
        except:
            print("  (Could not parse evaluation file)")
    else:
        print("  (No evaluation file found)")
    
    print()

print(f"{'=' * 70}\n")
print("✅ Experiment Complete!")
print(f"\nResults saved to: {latest}")
EOF

fi

# Final summary
echo
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ALL EXPERIMENTS COMPLETE!                              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo
echo -e "${BLUE}Results Location:${NC}"
echo "  Main: $RESULTS_DIR"
echo "  Scenarios: $SCENARIO_RESULTS"
echo
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Review results: cat $RESULTS_DIR/final_summary.txt"
echo "  2. Download to local: see EXPERIMENT_WORKFLOW.md"
echo "  3. Cleanup artifacts: bash experiments/scenarios/cleanup.sh"
echo
echo -e "${YELLOW}[*] Don't forget to cleanup attack artifacts!${NC}"
echo
