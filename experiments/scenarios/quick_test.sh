#!/bin/bash
############################################################################
# Quick Test Helper - APT Attack Detection
#
# Quickly test individual components without running full scenarios
############################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}🔧 APT Attack Detection - Quick Test Helper${NC}"
echo

# Activate venv
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
fi

# Function selection
show_menu() {
    echo
    echo -e "${YELLOW}Select test to run:${NC}"
    echo "  1) Test CTI Agent (quick)"
    echo "  2) Test Hunting Pipeline (requires checkpoint)"
    echo "  3) Run Scenario 1 only"
    echo "  4) Run Scenario 2 only  "
    echo "  5) Run Scenario 3 only"
    echo "  6) Test Event Collector"
    echo "  7) Run All Scenarios"
    echo "  8) Visualize Results (Jupyter)"
    echo "  9) Cleanup Artifacts"
    echo "  0) Exit"
    echo
}

test_cti_agent() {
    echo -e "${BLUE}Testing CTI Agent...${NC}"
    cd "$PROJECT_ROOT"
    
    # Check dependencies
    if [ ! -f "data/mitre/enterprise-attack.json" ]; then
        echo -e "${YELLOW}Downloading MITRE ATT&CK data...${NC}"
        mkdir -p data/mitre
        wget -q https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
            -O data/mitre/enterprise-attack.json
    fi
    
    # Quick test with 1 source
    echo -e "${GREEN}Running CTI Agent (1 source, 3 reports)...${NC}"
    python3 -m src.pipeline.agent.main \
        --rss "https://www.cisa.gov/cybersecurity-advisories/all.xml" \
        --stix data/mitre/enterprise-attack.json \
        --out-seeds runs/cti/test_seeds.json \
        --llm-backend g4f \
        --per-source-limit 3
    
    echo -e "${GREEN}✓ CTI Agent test complete${NC}"
    echo "Results: runs/cti/test_seeds.json"
}

test_hunting() {
    echo -e "${BLUE}Testing Hunting Pipeline...${NC}"
    cd "$PROJECT_ROOT"
    
    # Find checkpoint
    CHECKPOINT=$(find runs/checkpoints -name "*.pt" -type f | head -1)
    
    if [ -z "$CHECKPOINT" ]; then
        echo -e "${YELLOW}No checkpoint found. Would you like to train a quick model? (y/N)${NC}"
        read -r REPLY
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Training quick model (5 epochs)..."
            python3 -m src.pipeline.train.trainer \
                --dataset cadets \
                --epochs 5 \
                --save runs/checkpoints/quick_test.pt
            CHECKPOINT="runs/checkpoints/quick_test.pt"
        else
            echo "Skipping hunting test"
            return
        fi
    fi
    
    # Create test events if needed
    EVENTS="runs/events/test_events.jsonl"
    if [ ! -f "$EVENTS" ]; then
        echo "Creating sample events..."
        python3 << 'EOF'
import json, time
from pathlib import Path
events = []
for i in range(50):
    events.append({"kind": "process_start", "ts": time.time() + i, "pid": 1000 + i, "exe": "/bin/bash"})
Path("runs/events").mkdir(parents=True, exist_ok=True)
with open("runs/events/test_events.jsonl", "w") as f:
    for ev in events:
        f.write(json.dumps(ev) + "\n")
print(f"Created {len(events)} test events")
EOF
    fi
    
    echo -e "${GREEN}Running hunting pipeline...${NC}"
    python3 -m src.pipeline.hunting.main \
        --dataset cadets \
        --events "$EVENTS" \
        --checkpoint "$CHECKPOINT" \
        --cti-seeds runs/cti/seeds.json
    
    echo -e "${GREEN}✓ Hunting test complete${NC}"
}

run_scenario() {
    local scenario_num=$1
    echo -e "${BLUE}Running Scenario $scenario_num...${NC}"
    
    bash "$SCRIPT_DIR/run_all_scenarios.sh" --scenario $scenario_num
    
    echo -e "${GREEN}✓ Scenario $scenario_num complete${NC}"
}

test_collector() {
    echo -e "${BLUE}Testing Event Collector...${NC}"
    cd "$PROJECT_ROOT"
    
    if [ ! -f "/var/log/audit/audit.log" ]; then
        echo -e "${YELLOW}audit.log not found. Is auditd running?${NC}"
        sudo systemctl status auditd || echo "auditd not installed"
        return
    fi
    
    echo -e "${GREEN}Running collector (last 5 minutes of events)...${NC}"
    python3 -m src.pipeline.hunting.collector \
        --audit-log /var/log/audit/audit.log \
        --out runs/events/collector_test.jsonl \
        || echo "Collector test completed with warnings"
    
    if [ -f "runs/events/collector_test.jsonl" ]; then
        LINES=$(wc -l < runs/events/collector_test.jsonl)
        echo -e "${GREEN}✓ Collected $LINES events${NC}"
    fi
}

run_all() {
    echo -e "${BLUE}Running all scenarios...${NC}"
    bash "$SCRIPT_DIR/run_all_scenarios.sh"
}

visualize() {
    echo -e "${BLUE}Opening visualization notebook...${NC}"
    cd "$SCRIPT_DIR"
    
    if ! command -v jupyter &> /dev/null; then
        echo -e "${YELLOW}Jupyter not found. Installing...${NC}"
        pip install jupyter matplotlib seaborn networkx pandas
    fi
    
    jupyter notebook visualization.ipynb
}

cleanup() {
    echo -e "${BLUE}Running cleanup...${NC}"
    bash "$SCRIPT_DIR/cleanup.sh"
}

# Main loop
while true; do
    show_menu
    read -p "Enter choice [0-9]: " choice
    
    case $choice in
        1) test_cti_agent ;;
        2) test_hunting ;;
        3) run_scenario 1 ;;
        4) run_scenario 2 ;;
        5) run_scenario 3 ;;
        6) test_collector ;;
        7) run_all ;;
        8) visualize ;;
        9) cleanup ;;
        0) echo "Goodbye!"; exit 0 ;;
        *) echo -e "${YELLOW}Invalid choice${NC}" ;;
    esac
    
    echo
    read -p "Press Enter to continue..."
done
