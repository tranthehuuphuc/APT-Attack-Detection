# 🎯 APT Attack Scenarios for Testing

## Overview

3 kịch bản tấn công APT **thực tế** được thiết kế dựa trên:
- MITRE ATT&CK Framework
- Real-world APT campaigns (APT29, APT28, Lazarus)
- DARPA TC evaluation methodology

---

## 📋 Scenarios Summary

| Scenario | APT Group | Complexity | Techniques | Duration | Detection Difficulty |
|----------|-----------|------------|------------|----------|---------------------|
| **Scenario 1** | APT29 (Cozy Bear) | Medium | 8 techniques | ~15 min | Medium |
| **Scenario 2** | APT28 (Fancy Bear) | High | 12 techniques | ~25 min | Hard |
| **Scenario 3** | Lazarus Group | Very High | 15 techniques | ~35 min | Very Hard |

---

## 🎭 Scenario 1: APT29 Supply Chain Attack

### Threat Profile
- **APT Group**: APT29 (Cozy Bear)
- **Target**: Software supply chain
- **Goal**: Establish persistence, steal credentials
- **Based On**: SolarWinds compromise (2020)

### MITRE ATT&CK Techniques

| Phase | Technique ID | Technique Name | Description |
|-------|--------------|----------------|-------------|
| Initial Access | T1195.002 | Compromise Software Supply Chain | Malicious npm package |
| Execution | T1059.004 | Command and Scripting Interpreter: Unix Shell | Bash execution |
| Persistence | T1053.003 | Scheduled Task/Job: Cron | Cron job backdoor |
| Defense Evasion | T1070.004 | Indicator Removal: File Deletion | Clean log files |
| Credential Access | T1552.001 | Unsecured Credentials: Credentials In Files | Extract SSH keys |
| Discovery | T1082 | System Information Discovery | Enumerate system |
| Collection | T1005 | Data from Local System | Collect sensitive files |
| Exfiltration | T1041 | Exfiltration Over C2 Channel | Upload to C2 server |

### Attack Flow

```
┌─────────────────┐
│ 1. Download     │
│ malicious npm   │
│ package         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Execute      │
│ install script  │
│ (postinstall)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Create cron  │
│ backdoor        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Collect      │
│ SSH keys        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. Enumerate    │
│ system info     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. Exfiltrate   │
│ data via curl   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 7. Clean logs   │
└─────────────────┘
```

### Expected Detection

- **Seeds**: Suspicious npm process, /tmp/ file access
- **Graph Patterns**: npm → bash → cron → ssh file access
- **Alerts**: 3-5 high-confidence detections

### Files
- `scenario1_attack.sh`: Attack simulation script
- `scenario1_events.jsonl`: Pre-generated event log
- `scenario1_ground_truth.json`: Ground truth labels
- `scenario1_iocs.json`: Indicators of Compromise

---

## 🎭 Scenario 2: APT28 Spear Phishing to Lateral Movement

### Threat Profile
- **APT Group**: APT28 (Fancy Bear)
- **Target**: Corporate network
- **Goal**: Lateral movement, data exfiltration
- **Based On**: Democratic National Committee hack (2016)

### MITRE ATT&CK Techniques

| Phase | Technique ID | Technique Name | Description |
|-------|--------------|----------------|-------------|
| Initial Access | T1566.001 | Phishing: Spearphishing Attachment | Malicious PDF |
| Execution | T1204.002 | User Execution: Malicious File | User opens PDF |
| Persistence | T1053.003 | Scheduled Task/Job: Cron | Persistence via cron |
| Privilege Escalation | T1068 | Exploitation for Privilege Escalation | CVE exploit |
| Defense Evasion | T1036.005 | Masquerading: Match Legitimate Name | sshd impersonation |
| Credential Access | T1003.001 | OS Credential Dumping: LSASS Memory | Memory scraping |
| Discovery | T1018 | Remote System Discovery | Network scanning |
| Lateral Movement | T1021.004 | Remote Services: SSH | SSH to other hosts |
| Collection | T1119 | Automated Collection | Mass file collection |
| Command & Control | T1071.001 | Application Layer Protocol: Web Protocols | HTTPS C2 |
| Exfiltration | T1048.003 | Exfiltration Over Alternative Protocol: Exfiltration Over Unencrypted Non-C2 Protocol | DNS tunneling |
| Impact | T1485 | Data Destruction | Wiper malware |

### Attack Flow

```
┌──────────────┐
│ 1. User      │
│ opens PDF    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 2. Payload   │
│ execution    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 3. Privilege │
│ escalation   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 4. Credential│
│ dumping      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 5. Network   │
│ discovery    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 6. Lateral   │
│ movement     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 7. Data      │
│ collection   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 8. DNS       │
│ exfiltration │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 9. Wiper     │
│ deployment   │
└──────────────┘
```

### Expected Detection

- **Seeds**: Suspicious PDF reader process, memory access patterns
- **Graph Patterns**: Complex multi-hop lateral movement
- **Alerts**: 7-10 high/medium confidence detections

### Files
- `scenario2_attack.sh`: Attack simulation script
- `scenario2_events.jsonl`: Pre-generated event log
- `scenario2_ground_truth.json`: Ground truth labels
- `scenario2_iocs.json`: Indicators of Compromise

---

## 🎭 Scenario 3: Lazarus Group Advanced Persistent Threat

### Threat Profile
- **APT Group**: Lazarus Group (Hidden Cobra)
- **Target**: Financial institution
- **Goal**: Financial theft, long-term espionage
- **Based On**: Sony Pictures hack, SWIFT attacks

### MITRE ATT&CK Techniques (15 techniques)

| Phase | Technique ID | Technique Name |
|-------|--------------|----------------|
| Initial Access | T1190 | Exploit Public-Facing Application |
| Execution | T1059.001 | Command and Scripting Interpreter: PowerShell |
| Persistence | T1078.003 | Valid Accounts: Local Accounts |
| Persistence | T1543.003 | Create or Modify System Process: Windows Service |
| Privilege Escalation | T1055 | Process Injection |
| Defense Evasion | T1027 | Obfuscated Files or Information |
| Defense Evasion | T1562.001 | Impair Defenses: Disable or Modify Tools |
| Credential Access | T1110.003 | Brute Force: Password Spraying |
| Discovery | T1046 | Network Service Scanning |
| Discovery | T1087.001 | Account Discovery: Local Account |
| Lateral Movement | T1570 | Lateral Tool Transfer |
| Collection | T1560.001 | Archive Collected Data: Archive via Utility |
| Command & Control | T1095 | Non-Application Layer Protocol |
| Exfiltration | T1020 | Automated Exfiltration |
| Impact | T1486 | Data Encrypted for Impact |

### Attack Flow

```
      ┌──────────────────┐
      │ 1. Web exploit   │
      │ (CVE-2021-xxxx)  │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ 2. Webshell      │
      │ deployment       │
      └────────┬─────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌──────────┐     ┌──────────┐
│ 3a. User │     │ 3b. Service│
│ creation │     │ backdoor   │
└─────┬────┘     └─────┬────┘
      │                │
      └───────┬────────┘
              ▼
      ┌──────────────────┐
      │ 4. Process       │
      │ injection        │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ 5. Disable AV    │
      │ (defense evasion)│
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ 6. Password spray│
      │ attack           │
      └────────┬─────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌──────────┐     ┌──────────┐
│ 7a. Network│   │ 7b. Account│
│ scanning   │   │ discovery  │
└─────┬────┘     └─────┬────┘
      │                │
      └───────┬────────┘
              ▼
      ┌──────────────────┐
      │ 8. Lateral tool  │
      │ transfer         │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ 9. Mass data     │
      │ collection       │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ 10. Archive +    │
      │  encrypt         │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ 11. Covert C2    │
      │ (raw TCP)        │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ 12. Auto-        │
      │ exfiltration     │
      └────────┬─────────┘
               │
               ▼
      ┌──────────────────┐
      │ 13. Ransomware   │
      │ deployment       │
      └──────────────────┘
```

### Expected Detection

- **Seeds**: Web server suspicious processes, service creation, network anomalies
- **Graph Patterns**: Complex multi-stage attack with parallel execution paths
- **Alerts**: 12-18 detections (various confidence levels)

### Files
- `scenario3_attack.sh`: Attack simulation script
- `scenario3_events.jsonl`: Pre-generated event log
- `scenario3_ground_truth.json`: Ground truth labels
- `scenario3_iocs.json`: Indicators of Compromise

---

## 📊 Evaluation Metrics

### For Each Scenario

1. **Detection Rate**:
   - True Positives / Total Attack Actions
   - Target: >85% for Scenario 1, >75% for Scenario 2, >65% for Scenario 3

2. **False Positive Rate**:
   - False Positives / (False Positives + True Negatives)
   - Target: <10%

3. **Time to Detection**:
   - Time from attack start to first alert
   - Target: <5 minutes for critical techniques

4. **Graph Quality**:
   - Completeness of provenance graph
   - Accuracy of seed identification

5. **Resource Usage**:
   - Memory consumption
   - CPU utilization
   - Processing latency

### Ground Truth Format

```json
{
  "scenario": "scenario1_apt29",
  "techniques": [
    {
      "technique_id": "T1195.002",
      "timestamp": 1704340920.123,
      "pid": 12345,
      "process": "npm",
      "is_malicious": true,
      "severity": "high"
    }
  ],
  "nodes": [
    {
      "node_id": "p:12345",
      "is_malicious": true,
      "attack_stage": "initial_access"
    }
  ],
  "expected_seeds": ["p:12345", "f:/tmp/backdoor.sh"],
  "attack_start": 1704340920.0,
  "attack_end": 1704341820.0
}
```

---

## 🚀 Running Scenarios

### Automated Execution

```bash
# Run all scenarios
bash experiments/scenarios/run_all_scenarios.sh

# Run individual scenario
bash experiments/scenarios/scenario1_attack.sh
```

### Manual Execution with Evaluation

```bash
# 1. Run attack
bash experiments/scenarios/scenario1_attack.sh

# 2. Collect events (auditd already running)
# Events automatically logged to /var/log/audit/audit.log

# 3. Run collector
python3 -m src.pipeline.hunting.collector \
  --audit-log /var/log/audit/audit.log \
  --out runs/events/scenario1_events.jsonl

# 4. Run hunting
python3 -m src.pipeline.hunting.main \
  --dataset cadets \
  --events runs/events/scenario1_events.jsonl \
  --checkpoint runs/checkpoints/model.pt \
  --cti-seeds runs/cti/seeds.json

# 5. Evaluate
python3 -m src.eval.hunting_eval \
  --events runs/events/scenario1_events.jsonl \
  --ground-truth experiments/scenarios/scenario1_ground_truth.json \
  --predictions runs/predictions/scenario1_results.json
```

---

## 📁 Directory Structure

```
experiments/scenarios/
├── README.md                           # This file
├── run_all_scenarios.sh                # Run all scenarios
├── evaluate_all.sh                     # Evaluate all results
│
├── scenario1_apt29/
│   ├── attack.sh                       # Attack script
│   ├── events.jsonl                    # Pre-generated events
│   ├── ground_truth.json               # Ground truth labels
│   ├── iocs.json                       # IOCs
│   └── report.md                       # Detailed report
│
├── scenario2_apt28/
│   ├── attack.sh
│   ├── events.jsonl
│   ├── ground_truth.json
│   ├── iocs.json
│   └── report.md
│
└── scenario3_lazarus/
    ├── attack.sh
    ├── events.jsonl
    ├── ground_truth.json
    ├── iocs.json
    └── report.md
```

---

## ⚠️ Safety & Ethics

### Important Notes

1. **Isolated Environment**: Run ONLY on dedicated test VMs
2. **No Real Targets**: Never target production systems
3. **Cleanup**: Always run cleanup scripts after testing
4. **Logging**: Keep detailed logs for analysis
5. **Legal**: Ensure you have authorization for all testing

### Cleanup

```bash
# After each scenario
bash experiments/scenarios/cleanup.sh

# Removes:
# - Backdoor files
# - Cron jobs
# - Temporary files
# - Test artifacts
```

---

## 📈 Expected Results

### Scenario 1 (Medium Complexity)
- Detection Rate: 85-95%
- FPR: 5-10%
- Time to Detection: 2-5 min
- Alerts: 3-5

### Scenario 2 (High Complexity)
- Detection Rate: 75-85%
- FPR: 8-12%
- Time to Detection: 3-7 min
- Alerts: 7-10

### Scenario 3 (Very High Complexity)
- Detection Rate: 65-80%
- FPR: 10-15%
- Time to Detection: 5-10 min
- Alerts: 12-18

---

## 📝 Next Steps

1. Review each scenario's detailed report
2. Run scenarios in order (1 → 2 → 3)
3. Collect metrics for each run
4. Analyze false positives/negatives
5. Tune detection parameters
6. Document findings

---

**Created**: 2026-01-04  
**Purpose**: System evaluation and validation  
**Status**: Ready for testing on Ubuntu 22.04
