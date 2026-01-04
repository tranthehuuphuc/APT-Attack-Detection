#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y auditd audispd-plugins
# Basic syscall audit rules (minimal). You can extend as needed.
RULES_FILE="/etc/audit/rules.d/apt_hunting.rules"
sudo bash -c "cat > $RULES_FILE" <<'EOF'
-D
-b 8192
-f 1
-a always,exit -F arch=b64 -S execve -k apt_exec
-a always,exit -F arch=b64 -S open,openat,creat,unlink,rename,chmod,chown -k apt_file
-a always,exit -F arch=b64 -S connect,accept,bind,listen,sendto,recvfrom -k apt_net
EOF
sudo augenrules --load
sudo systemctl restart auditd
echo "[OK] auditd rules installed to $RULES_FILE"
