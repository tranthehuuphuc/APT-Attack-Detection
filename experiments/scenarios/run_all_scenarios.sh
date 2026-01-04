#!/bin/bash
#############################################################################
# APT Attack Scenarios - Automated Execution Suite
# 
# Runs all 3 attack scenarios sequentially with collection and evaluation
# 
# Usage: bash run_all_scenarios.sh [--skip-cleanup] [--scenario N]
#############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESULTS_DIR="$PROJECT_ROOT/runs/scenario_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Options
SKIP_CLEANUP=false
SPECIFIC_SCENARIO=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-cleanup)
            SKIP_CLEANUP=true
            shift
            ;;
        --scenario)
            SPECIFIC_SCENARIO="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-cleanup       Don't cleanup between scenarios"
            echo "  --scenario N         Run only scenario N (1, 2, or 3)"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create results directory
mkdir -p "$RESULTS_DIR/$TIMESTAMP"

echo -e "${MAGENTA}════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  APT Attack Scenarios - Automated Test Suite      ${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Start time: $(date)${NC}"
echo -e "${GREEN}Results dir: $RESULTS_DIR/$TIMESTAMP${NC}"
echo

# Pre-flight checks
echo -e "${BLUE}[*] Running pre-flight checks...${NC}"

# Check if auditd is running
if ! systemctl is-active --quiet auditd 2>/dev/null; then
    echo -e "${YELLOW}[!] WARNING: auditd is not running${NC}"
    echo -e "${YELLOW}[!] Events may not be captured properly${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python environment
if ! source "$PROJECT_ROOT/.venv/bin/activate" 2>/dev/null; then
    echo -e "${YELLOW}[!] WARNING: Virtual environment not found${NC}"
    echo -e "${YELLOW}[!] Continuing with system Python${NC}"
fi

# Function to run scenario
run_scenario() {
    local scenario_num=$1
    local scenario_name=$2
    local scenario_dir="$SCRIPT_DIR/scenario${scenario_num}_${scenario_name}"
    
    echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Scenario $scenario_num: $(printf '%-39s' "$scenario_name" | tr '[:lower:]' '[:upper:]')  ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
    
    if [ ! -f "$scenario_dir/attack.sh" ]; then
        echo -e "${RED}[!] Attack script not found: $scenario_dir/attack.sh${NC}"
        return 1
    fi
    
    # Clear audit log marker
    AUDIT_MARK=$(date +%s)
    
    # Run attack
    echo -e "${GREEN}[*] Executing attack scenario ${scenario_num}...${NC}"
    bash "$scenario_dir/attack.sh" 2>&1 | tee "$RESULTS_DIR/$TIMESTAMP/scenario${scenario_num}_attack.log"
    
    sleep 5
    
    # Collect events
    echo -e "${GREEN}[*] Collecting audit events...${NC}"
    if command -v ausearch &> /dev/null; then
        sudo ausearch -ts $AUDIT_MARK --raw > "$RESULTS_DIR/$TIMESTAMP/scenario${scenario_num}_audit_raw.log" 2>/dev/null || true
    fi
    
    # Run collector if events file doesn't exist
    EVENTS_FILE="$PROJECT_ROOT/runs/events/scenario${scenario_num}_events.jsonl"
    if [ ! -f "$EVENTS_FILE" ]; then
        echo -e "${GREEN}[*] Running event collector...${NC}"
        python3 -m src.pipeline.hunting.collector \
            --audit-log /var/log/audit/audit.log \
            --out "$EVENTS_FILE" 2>&1 | tee "$RESULTS_DIR/$TIMESTAMP/scenario${scenario_num}_collector.log" || true
    fi
    
    # Check if checkpoint exists
    CHECKPOINT=$(find "$PROJECT_ROOT/runs/checkpoints" -name "*.pt" -type f | head -1)
    if [ -z "$CHECKPOINT" ]; then
        echo -e "${YELLOW}[!] No checkpoint found, skipping hunting${NC}"
    else
        # Run hunting
        echo -e "${GREEN}[*] Running hunting pipeline...${NC}"
        python3 -m src.pipeline.hunting.main \
            --dataset cadets \
            --events "$EVENTS_FILE" \
            --checkpoint "$CHECKPOINT" \
            --cti-seeds "$PROJECT_ROOT/runs/cti/seeds.json" \
            2>&1 | tee "$RESULTS_DIR/$TIMESTAMP/scenario${scenario_num}_hunting.log" || true
    fi
    
    # Run evaluation if ground truth exists
    if [ -f "$scenario_dir/ground_truth.json" ]; then
        echo -e "${GREEN}[*] Running evaluation...${NC}"
        python3 -m src.eval.hunting_eval \
            --events "$EVENTS_FILE" \
            --ground-truth "$scenario_dir/ground_truth.json" \
            --output "$RESULTS_DIR/$TIMESTAMP/scenario${scenario_num}_eval.json" \
            2>&1 | tee "$RESULTS_DIR/$TIMESTAMP/scenario${scenario_num}_eval.log" || true
    fi
    
    # Copy attack summary
    SUMMARY_SOURCES=(
        "/tmp/apt_scenario${scenario_num}_logs/attack_summary.txt"
        "/tmp/apt_scenario${scenario_num}_logs"
    )
    for src in "${SUMMARY_SOURCES[@]}"; do
        if [ -e "$src" ]; then
            cp -r "$src" "$RESULTS_DIR/$TIMESTAMP/" 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}[✓] Scenario $scenario_num completed${NC}"
    echo
    
    # Cleanup if not skipped
    if [ "$SKIP_CLEANUP" = false ]; then
        echo -e "${YELLOW}[*] Running cleanup...${NC}"
        bash "$SCRIPT_DIR/cleanup.sh" <<< "n" 2>&1 | tee "$RESULTS_DIR/$TIMESTAMP/scenario${scenario_num}_cleanup.log"
        echo
        sleep 3
    fi
}

# Main execution
SUITE_START=$(date +%s)

if [ -n "$SPECIFIC_SCENARIO" ]; then
    # Run specific scenario
    case $SPECIFIC_SCENARIO in
        1)
            run_scenario 1 "apt29"
            ;;
        2)
            run_scenario 2 "apt28"
            ;;
        3)
            run_scenario 3 "lazarus"
            ;;
        *)
            echo -e "${RED}[!] Invalid scenario number: $SPECIFIC_SCENARIO${NC}"
            echo "Valid options: 1, 2, 3"
            exit 1
            ;;
    esac
else
    # Run all scenarios
    run_scenario 1 "apt29"
    run_scenario 2 "apt28"
    run_scenario 3 "lazarus"
fi

SUITE_END=$(date +%s)
SUITE_DURATION=$((SUITE_END - SUITE_START))
SUITE_MINUTES=$((SUITE_DURATION / 60))
SUITE_SECONDS=$((SUITE_DURATION % 60))

# Generate final report
cat > "$RESULTS_DIR/$TIMESTAMP/suite_summary.txt" << EOF
APT Attack Scenarios - Test Suite Summary
==========================================

Execution Time: $(date -d @$SUITE_START 2>/dev/null || date -r $SUITE_START)
Completion Time: $(date)
Total Duration: ${SUITE_MINUTES}m ${SUITE_SECONDS}s

Scenarios Executed:
EOF

if [ -n "$SPECIFIC_SCENARIO" ]; then
    echo "  - Scenario $SPECIFIC_SCENARIO only" >> "$RESULTS_DIR/$TIMESTAMP/suite_summary.txt"
else
    echo "  - Scenario 1: APT29 Supply Chain" >> "$RESULTS_DIR/$TIMESTAMP/suite_summary.txt"
    echo "  - Scenario 2: APT28 Lateral Movement" >> "$RESULTS_DIR/$TIMESTAMP/suite_summary.txt"
    echo "  - Scenario 3: Lazarus Advanced APT" >> "$RESULTS_DIR/$TIMESTAMP/suite_summary.txt"
fi

cat >> "$RESULTS_DIR/$TIMESTAMP/suite_summary.txt" << EOF

Results Location: $RESULTS_DIR/$TIMESTAMP

Files Generated:
EOF

ls -1 "$RESULTS_DIR/$TIMESTAMP/" >> "$RESULTS_DIR/$TIMESTAMP/suite_summary.txt"

cat >> "$RESULTS_DIR/$TIMESTAMP/suite_summary.txt" << EOF

Next Steps:
1. Review individual scenario logs
2. Analyze evaluation metrics
3. Compare detection rates across scenarios
4. Generate consolidated report

Visualization:
  jupyter notebook experiments/scenarios/visualization.ipynb

Cleanup Status: $([ "$SKIP_CLEANUP" = true ] && echo "SKIPPED - Manual cleanup required" || echo "Completed after each scenario")
EOF

echo -e "${MAGENTA}════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  Test Suite Completed                              ${NC}"
echo -e "${MAGENTA}════════════════════════════════════════════════════${NC}"
cat "$RESULTS_DIR/$TIMESTAMP/suite_summary.txt"

echo
echo -e "${GREEN}[*] All results saved to: $RESULTS_DIR/$TIMESTAMP${NC}"
echo -e "${YELLOW}[*] View summary: cat $RESULTS_DIR/$TIMESTAMP/suite_summary.txt${NC}"
echo -e "${YELLOW}[*] Visualize: jupyter notebook experiments/scenarios/visualization.ipynb${NC}"

if [ "$SKIP_CLEANUP" = true ]; then
    echo
    echo -e "${RED}[!] CLEANUP WAS SKIPPED${NC}"
    echo -e "${RED}[!] Run manually: bash experiments/scenarios/cleanup.sh${NC}"
fi

echo
