#!/bin/bash
################################################################################
# Cleanup Script for APT Attack Scenarios
#
# Removes all attack artifacts, backdoors, and temporary files created during
# attack simulations.
#
# Usage: bash cleanup.sh [scenario_number]
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[*] Starting cleanup of attack artifacts...${NC}"
echo

# Scenario-specific directories
BACKDOOR_DIRS=(
    "/tmp/.npm_cache"
    "/tmp/.system_"*
    "/tmp/.hidden"
    "/tmp/apt_scenario"*
)

LOG_DIRS=(
    "/tmp/apt_scenario1_logs"
    "/tmp/apt_scenario2_logs"
    "/tmp/apt_scenario3_logs"
)

EXFIL_DIRS=(
    "/tmp/exfil_"*
    "/tmp/.system_"*
)

# Remove backdoor directories
echo -e "${GREEN}[*] Removing backdoor directories...${NC}"
for dir in "${BACKDOOR_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        rm -rf "$dir"
        echo "  - Removed: $dir"
    fi
done

# Remove exfiltration staging
echo -e "${GREEN}[*] Removing exfiltration staging...${NC}"
for dir in "${EXFIL_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        rm -rf "$dir"
        echo "  - Removed: $dir"
    fi
done

# Clean up temporary files
echo -e "${GREEN}[*] Removing temporary files...${NC}"
rm -f /tmp/curl_* 2>/dev/null || true
rm -f /tmp/wget_* 2>/dev/null || true
rm -f /tmp/*.tar.gz 2>/dev/null || true
rm -f /tmp/stage*.sh 2>/dev/null || true
echo "  - Cleaned /tmp/ artifacts"

# Restore bash history if backed up
echo -e "${GREEN}[*] Checking bash history...${NC}"
for logdir in "${LOG_DIRS[@]}"; do
    if [ -f "$logdir/bash_history_backup.txt" ]; then
        echo "  - Found backup in $logdir"
        echo -e "${YELLOW}[!] Original bash history was modified${NC}"
        echo -e "${YELLOW}[!] Backup available at: $logdir/bash_history_backup.txt${NC}"
    fi
done

# Check for malicious cron entries (don't auto-remove for safety)
echo -e "${GREEN}[*] Checking for cron entries...${NC}"
if crontab -l 2>/dev/null | grep -q "npm_cache\|.hidden\|check.sh"; then
    echo -e "${RED}[!] WARNING: Malicious cron entries found!${NC}"
    echo -e "${YELLOW}[!] Please manually review and remove:${NC}"
    crontab -l | grep -E "npm_cache|.hidden|check.sh"
    echo
    echo -e "${YELLOW}[!] To remove: crontab -e${NC}"
else
    echo "  - No malicious cron entries found"
fi

# Kill any lingering processes
echo -e "${GREEN}[*] Checking for lingering processes...${NC}"
SUSPICIOUS_PROCS=$(ps aux | grep -E "npm_cache|stage2|check.sh" | grep -v grep | awk '{print $2}')
if [ -n "$SUSPICIOUS_PROCS" ]; then
    echo "  - Found suspicious processes: $SUSPICIOUS_PROCS"
    echo "$SUSPICIOUS_PROCS" | xargs kill -9 2>/dev/null || true
    echo "  - Killed lingering processes"
else
    echo "  - No lingering processes found"
fi

# Keep logs for analysis (optional)
echo
echo -e "${YELLOW}[?] Keep attack logs for analysis? (y/N)${NC}"
read -t 10 -r KEEP_LOGS || KEEP_LOGS="n"

if [[ ! $KEEP_LOGS =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}[*] Removing log directories...${NC}"
    for dir in "${LOG_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            rm -rf "$dir"
            echo "  - Removed: $dir"
        fi
    done
else
    echo -e "${GREEN}[*] Logs preserved at: ${LOG_DIRS[@]}${NC}"
fi

echo
echo -e "${GREEN}[*] ===== Cleanup Complete =====${NC}"
echo -e "${YELLOW}[!] Manually verify the following:${NC}"
echo "  1. Check crontab: crontab -l"
echo "  2. Check processes: ps aux | grep -E 'npm|stage|check'"
echo "  3. Check /tmp: ls -la /tmp/"
echo "  4. Review auditd logs if needed"
echo
