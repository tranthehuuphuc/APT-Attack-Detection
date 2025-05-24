def add_custom_rule(self, category: str, condition: Dict, ttp_label: TTPLabel):
        """Thêm luật TTP tùy chỉnh"""
        if category not in self.rules:
            self.rules[category] = []
        
        self.rules[category].append({
            "condition": condition,
            "ttp": ttp_label
        })
        logger.info(f"Added custom rule to category '{category}': {ttp_label.technique_id}")
    
    def load_rules_from_file(self, rules_file_path: str):
        """Tải luật từ file JSON"""
        try:
            with open(rules_file_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
                
            for category, rules in rules_data.items():
                for rule in rules:
                    ttp_info = rule["ttp"]
                    ttp_label = TTPLabel(
                        technique_id=ttp_info["technique_id"],
                        technique_name=ttp_info["technique_name"],
                        tactic=ttp_info["tactic"],
                        description=ttp_info["description"],
                        confidence=ttp_info.get("confidence", 1.0)
                    )
                    self.add_custom_rule(category, rule["condition"], ttp_label)
                    
            logger.info(f"Loaded rules from file: {rules_file_path}")
            
        except Exception as e:
            logger.error(f"Error loading rules from file: {e}")
    
    def export_rules_template(self, output_path: str):
        """Export template file để tạo custom rules"""
        template = {
            "custom_category": [
                {
                    "condition": {
                        "event_type": "EVENT_EXAMPLE",
                        "command_patterns": [".*example.*"],
                        "file_patterns": [".*\\.example$"],
                        "port_patterns": ["8080", "9999"],
                        "external_ip": True,
                        "executable_permissions": True,
                        "hidden_file": True,
                        "high_ports": True,
                        "uid_change": True,
                        "properties_check": {
                            "property_name": ["expected_value1", "expected_value2"]
                        }
                    },
                    "#!/usr/bin/env python3
"""
TTP Labeling System for Linux Audit Logs
Xây dựng bộ gán nhãn TTP từ log hệ thống để phát hiện hành vi tấn công
"""

import json
import re
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TTPLabel:
    """Lớp đại diện cho một nhãn TTP"""
    technique_id: str
    technique_name: str
    tactic: str
    description: str
    confidence: float = 1.0

@dataclass
class LogEvent:
    """Lớp đại diện cho một sự kiện log đã được chuẩn hóa"""
    event_id: str
    event_type: str
    timestamp: int
    subject_id: str
    object_id: str
    thread_id: Optional[int]
    host_id: str
    properties: Dict[str, Any]
    source: str
    ttp_labels: List[TTPLabel]

class TTPRuleEngine:
    """Engine để áp dụng các luật gán nhãn TTP"""
    
    def __init__(self):
        self.rules = self._load_ttp_rules()
        
    def _load_ttp_rules(self) -> Dict[str, List[Dict]]:
        """Tải các luật TTP mapping mở rộng"""
        return {
            # Memory Protection Rules - Phát hiện các kỹ thuật injection
            "memory_protection": [
                {
                    "condition": {
                        "event_type": "EVENT_MPROTECT",
                        "protection_pattern": ["3", "5"]  # RW -> RWX
                    },
                    "ttp": TTPLabel(
                        technique_id="T1055",
                        technique_name="Process Injection",
                        tactic="Defense Evasion",
                        description="Memory protection change RW->RWX indicating potential code injection"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_MPROTECT",
                        "protection_pattern": ["1", "5"]  # R -> RWX
                    },
                    "ttp": TTPLabel(
                        technique_id="T1055.012",
                        technique_name="Process Hollowing",
                        tactic="Defense Evasion",
                        description="Memory protection change R->RWX indicating potential process hollowing"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_MMAP",
                        "properties_check": {"prot": ["PROT_EXEC", "PROT_WRITE"]}
                    },
                    "ttp": TTPLabel(
                        technique_id="T1055.009",
                        technique_name="Proc Memory",
                        tactic="Defense Evasion",
                        description="Executable memory mapping detected"
                    )
                }
            ],
            
            # Process Execution Rules
            "process_execution": [
                {
                    "condition": {
                        "event_type": "EVENT_EXECUTE",
                        "command_patterns": [r".*powershell.*", r".*pwsh.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1059.001",
                        technique_name="PowerShell",
                        tactic="Execution",
                        description="PowerShell execution detected"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_EXECUTE", 
                        "command_patterns": [r".*/bin/bash.*", r".*/bin/sh.*", r".*/bin/zsh.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1059.004",
                        technique_name="Unix Shell",
                        tactic="Execution",
                        description="Unix shell execution detected"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_EXECUTE",
                        "command_patterns": [r".*python.*", r".*perl.*", r".*ruby.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1059.006",
                        technique_name="Python",
                        tactic="Execution",
                        description="Scripting language execution detected"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_FORK",
                        "suspicious_timing": True
                    },
                    "ttp": TTPLabel(
                        technique_id="T1106",
                        technique_name="Native API",
                        tactic="Execution",
                        description="Suspicious process forking pattern"
                    )
                }
            ],
            
            # Network Connection Rules
            "network_activity": [
                {
                    "condition": {
                        "event_type": "EVENT_CONNECT",
                        "external_ip": True
                    },
                    "ttp": TTPLabel(
                        technique_id="T1071.001",
                        technique_name="Web Protocols",
                        tactic="Command and Control",
                        description="External network connection detected"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_SENDTO",
                        "port_patterns": ["53", "443", "80"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1071.004",
                        technique_name="DNS",
                        tactic="Command and Control",
                        description="Potential DNS tunneling or C2 communication"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_BIND",
                        "high_ports": True
                    },
                    "ttp": TTPLabel(
                        technique_id="T1572",
                        technique_name="Protocol Tunneling",
                        tactic="Command and Control",
                        description="Suspicious port binding for potential backdoor"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_ACCEPT",
                        "reverse_connection": True
                    },
                    "ttp": TTPLabel(
                        technique_id="T1105",
                        technique_name="Ingress Tool Transfer",
                        tactic="Command and Control",
                        description="Potential reverse shell or tool download"
                    )
                }
            ],
            
            # File System Rules
            "file_operations": [
                {
                    "condition": {
                        "event_type": "EVENT_WRITE",
                        "file_patterns": [r".*\.so$", r".*\.dll$"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1055.001",
                        technique_name="Dynamic-link Library Injection",
                        tactic="Defense Evasion",
                        description="Suspicious library file write detected"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_READ",
                        "file_patterns": [r".*/etc/passwd$", r".*/etc/shadow$", r".*/etc/group$"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1082",
                        technique_name="System Information Discovery",
                        tactic="Discovery",
                        description="System information file access detected"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_WRITE",
                        "file_patterns": [r".*/tmp/.*", r".*/var/tmp/.*", r".*/dev/shm/.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1036.005",
                        technique_name="Match Legitimate Name or Location",
                        tactic="Defense Evasion",
                        description="File written to temporary/volatile location"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_CHMOD",
                        "executable_permissions": True
                    },
                    "ttp": TTPLabel(
                        technique_id="T1222.002",
                        technique_name="Linux and Mac File and Directory Permissions Modification",
                        tactic="Defense Evasion",
                        description="File permissions modified to executable"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_RENAME",
                        "hidden_file": True
                    },
                    "ttp": TTPLabel(
                        technique_id="T1564.001",
                        technique_name="Hidden Files and Directories",
                        tactic="Defense Evasion",
                        description="File renamed to hidden (dot prefix)"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_READ",
                        "file_patterns": [r".*/proc/.*/maps$", r".*/proc/.*/mem$"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1055.009",
                        technique_name="Proc Memory",
                        tactic="Defense Evasion",
                        description="Process memory inspection via /proc filesystem"
                    )
                }
            ],
            
            # Persistence Rules
            "persistence_mechanisms": [
                {
                    "condition": {
                        "event_type": "EVENT_WRITE",
                        "file_patterns": [r".*/\.bashrc$", r".*/\.profile$", r".*/\.bash_profile$"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1546.004",
                        technique_name="Unix Shell Configuration Modification",
                        tactic="Persistence",
                        description="Shell configuration file modified for persistence"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_WRITE",
                        "file_patterns": [r".*/etc/crontab$", r".*/var/spool/cron/.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1053.003",
                        technique_name="Cron",
                        tactic="Persistence",
                        description="Cron job configuration modified"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_WRITE",
                        "file_patterns": [r".*/etc/systemd/system/.*\.service$"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1543.002",
                        technique_name="Systemd Service",
                        tactic="Persistence",
                        description="Systemd service file created/modified"
                    )
                }
            ],
            
            # Privilege Escalation Rules
            "privilege_escalation": [
                {
                    "condition": {
                        "event_type": "EVENT_EXECUTE",
                        "command_patterns": [r".*sudo.*", r".*su\s+.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1548.003",
                        technique_name="Sudo and Sudo Caching",
                        tactic="Privilege Escalation",
                        description="Sudo/su command execution detected"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_SETUID",
                        "uid_change": True
                    },
                    "ttp": TTPLabel(
                        technique_id="T1548.001",
                        technique_name="Setuid and Setgid",
                        tactic="Privilege Escalation",
                        description="UID elevation detected"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_WRITE",
                        "file_patterns": [r".*/etc/sudoers.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1548.003",
                        technique_name="Sudo and Sudo Caching",
                        tactic="Privilege Escalation",
                        description="Sudoers file modification detected"
                    )
                }
            ],
            
            # Discovery Rules
            "discovery_activities": [
                {
                    "condition": {
                        "event_type": "EVENT_EXECUTE",
                        "command_patterns": [r".*ps\s+.*", r".*pstree.*", r".*top.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1057",
                        technique_name="Process Discovery",
                        tactic="Discovery",
                        description="Process enumeration command executed"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_EXECUTE",
                        "command_patterns": [r".*netstat.*", r".*ss\s+.*", r".*lsof.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1049",
                        technique_name="System Network Connections Discovery",
                        tactic="Discovery",
                        description="Network connection enumeration"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_EXECUTE",
                        "command_patterns": [r".*whoami.*", r".*id\s+.*", r".*groups.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1033",
                        technique_name="System Owner/User Discovery",
                        tactic="Discovery",
                        description="User identity enumeration"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_EXECUTE",
                        "command_patterns": [r".*find\s+.*", r".*locate.*", r".*ls\s+-la.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1083",
                        technique_name="File and Directory Discovery",
                        tactic="Discovery",
                        description="File system enumeration"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_READ",
                        "file_patterns": [r".*/proc/version$", r".*/etc/os-release$", r".*/etc/issue$"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1082",
                        technique_name="System Information Discovery",
                        tactic="Discovery",
                        description="Operating system information gathered"
                    )
                }
            ],
            
            # Collection Rules
            "collection_activities": [
                {
                    "condition": {
                        "event_type": "EVENT_READ",
                        "file_patterns": [r".*\.ssh/.*", r".*\.gnupg/.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1552.004",
                        technique_name="Private Keys",
                        tactic="Credential Access",
                        description="Private key file access detected"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_EXECUTE",
                        "command_patterns": [r".*history.*", r".*cat.*bash_history.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1552.003",
                        technique_name="Bash History",
                        tactic="Credential Access",
                        description="Command history access detected"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_READ",
                        "file_patterns": [r".*\.mozilla/.*", r".*\.config/google-chrome/.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1555.003",
                        technique_name="Credentials from Web Browsers",
                        tactic="Credential Access",
                        description="Browser data access detected"
                    )
                }
            ],
            
            # Defense Evasion Rules
            "defense_evasion": [
                {
                    "condition": {
                        "event_type": "EVENT_EXECUTE",
                        "command_patterns": [r".*unset\s+HISTFILE.*", r".*export\s+HISTSIZE=0.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1070.003",
                        technique_name="Clear Command History",
                        tactic="Defense Evasion",
                        description="Command history clearing attempt"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_UNLINK",
                        "file_patterns": [r".*/var/log/.*", r".*/tmp/.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1070.004",
                        technique_name="File Deletion",
                        tactic="Defense Evasion",
                        description="Log or temporary file deletion"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_EXECUTE",
                        "command_patterns": [r".*pkill.*", r".*killall.*rsyslog.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1562.001",
                        technique_name="Disable or Modify Tools",
                        tactic="Defense Evasion",
                        description="Security tool process termination"
                    )
                }
            ],
            
            # Lateral Movement Rules
            "lateral_movement": [
                {
                    "condition": {
                        "event_type": "EVENT_CONNECT",
                        "port_patterns": ["22", "3389"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1021.004",
                        technique_name="SSH",
                        tactic="Lateral Movement",
                        description="SSH connection for potential lateral movement"
                    )
                },
                {
                    "condition": {
                        "event_type": "EVENT_EXECUTE",
                        "command_patterns": [r".*scp\s+.*", r".*rsync\s+.*"]
                    },
                    "ttp": TTPLabel(
                        technique_id="T1105",
                        technique_name="Ingress Tool Transfer",
                        tactic="Command and Control",
                        description="File transfer tool execution"
                    )
                }
            ]
        }
    
    def apply_rules(self, log_event: LogEvent) -> List[TTPLabel]:
        """Áp dụng các luật để gán nhãn TTP cho một sự kiện log"""
        labels = []
        
        for rule_category, rules in self.rules.items():
            for rule in rules:
                if self._match_rule(log_event, rule["condition"]):
                    labels.append(rule["ttp"])
                    logger.debug(f"Matched rule {rule_category}: {rule['ttp'].technique_id}")
        
        return labels
    
    def _match_rule(self, log_event: LogEvent, condition: Dict) -> bool:
        """Kiểm tra xem một sự kiện log có khớp với điều kiện không"""
        
        # Kiểm tra event type
        if "event_type" in condition:
            if log_event.event_type != condition["event_type"]:
                return False
        
        # Kiểm tra memory protection pattern (đặc biệt cho MPROTECT)
        if "protection_pattern" in condition:
            if log_event.event_type == "EVENT_MPROTECT":
                protection = log_event.properties.get("protection", "")
                return protection in condition["protection_pattern"]
        
        # Kiểm tra command patterns
        if "command_patterns" in condition:
            command = log_event.properties.get("command", "")
            exe_path = log_event.properties.get("exe", "")
            cmdline = log_event.properties.get("cmdline", "")
            
            # Tìm trong tất cả các trường có thể chứa command
            search_text = f"{command} {exe_path} {cmdline}".lower()
            
            for pattern in condition["command_patterns"]:
                if re.search(pattern, search_text, re.IGNORECASE):
                    return True
        
        # Kiểm tra file patterns
        if "file_patterns" in condition:
            file_path = log_event.properties.get("file_path", "")
            name = log_event.properties.get("name", "")
            path = log_event.properties.get("path", "")
            
            # Tìm trong tất cả các trường có thể chứa file path
            search_paths = f"{file_path} {name} {path}"
            
            for pattern in condition["file_patterns"]:
                if re.search(pattern, search_paths, re.IGNORECASE):
                    return True
        
        # Kiểm tra external IP connection
        if "external_ip" in condition:
            dest_ip = log_event.properties.get("dest_ip", "")
            remote_address = log_event.properties.get("remote_address", "")
            
            for ip in [dest_ip, remote_address]:
                if ip and self._is_external_ip(ip):
                    return True
        
        # Kiểm tra port patterns
        if "port_patterns" in condition:
            dest_port = str(log_event.properties.get("dest_port", ""))
            remote_port = str(log_event.properties.get("remote_port", ""))
            port = str(log_event.properties.get("port", ""))
            
            for check_port in [dest_port, remote_port, port]:
                if check_port in condition["port_patterns"]:
                    return True
        
        # Kiểm tra executable permissions
        if "executable_permissions" in condition:
            mode = log_event.properties.get("mode", "")
            permissions = log_event.properties.get("permissions", "")
            
            # Kiểm tra xem có quyền execute không (bit thứ 3, 6, 9)
            if mode and (int(mode, 8) & 0o111):  # Có quyền execute
                return True
            if "x" in permissions.lower():
                return True
        
        # Kiểm tra hidden file (bắt đầu bằng dấu chấm)
        if "hidden_file" in condition:
            name = log_event.properties.get("name", "")
            file_path = log_event.properties.get("file_path", "")
            
            if name.startswith('.') or '/.' in file_path:
                return True
        
        # Kiểm tra high ports (> 1024)
        if "high_ports" in condition:
            port = log_event.properties.get("port", 0)
            if isinstance(port, (int, str)) and int(port) > 1024:
                return True
        
        # Kiểm tra reverse connection patterns
        if "reverse_connection" in condition:
            # Heuristic: connection từ external IP tới high port
            remote_ip = log_event.properties.get("remote_address", "")
            local_port = log_event.properties.get("local_port", 0)
            
            if remote_ip and self._is_external_ip(remote_ip) and int(local_port) > 1024:
                return True
        
        # Kiểm tra UID changes
        if "uid_change" in condition:
            old_uid = log_event.properties.get("old_uid", "")
            new_uid = log_event.properties.get("new_uid", "")
            uid = log_event.properties.get("uid", "")
            
            # Kiểm tra elevation to root (UID 0)
            if new_uid == "0" or uid == "0":
                return True
        
        # Kiểm tra suspicious timing patterns
        if "suspicious_timing" in condition:
            # Đây là placeholder - có thể implement logic phức tạp hơn
            # để phát hiện patterns bất thường về timing
            return True
        
        # Kiểm tra properties cụ thể
        if "properties_check" in condition:
            for prop_key, expected_values in condition["properties_check"].items():
                actual_value = log_event.properties.get(prop_key, "")
                if any(val in str(actual_value) for val in expected_values):
                    return True
        
        return True  # Nếu không có điều kiện đặc biệt, coi như khớp

    def _is_external_ip(self, ip: str) -> bool:
        """Kiểm tra xem IP có phải là external không"""
        # Đây là implementation đơn giản, có thể mở rộng
        private_ranges = ["192.168.", "10.", "172.16.", "127."]
        return not any(ip.startswith(prefix) for prefix in private_ranges)

class LogProcessor:
    """Lớp xử lý log chính"""
    
    def __init__(self):
        self.rule_engine = TTPRuleEngine()
        self.processed_events = []
        self.ttp_statistics = defaultdict(int)
        
    def parse_cdm_log(self, log_line: str) -> Optional[LogEvent]:
        """Parse một dòng log CDM format thành LogEvent"""
        try:
            data = json.loads(log_line.strip())
            datum = data.get("datum", {})
            
            # Xử lý Event
            if "com.bbn.tc.schema.avro.cdm18.Event" in datum:
                event_data = datum["com.bbn.tc.schema.avro.cdm18.Event"]
                
                # Trích xuất thông tin cơ bản
                event = LogEvent(
                    event_id=event_data.get("uuid", ""),
                    event_type=event_data.get("type", ""),
                    timestamp=event_data.get("timestampNanos", 0),
                    subject_id=event_data.get("subject", {}).get("com.bbn.tc.schema.avro.cdm18.UUID", ""),
                    object_id=event_data.get("predicateObject", {}).get("com.bbn.tc.schema.avro.cdm18.UUID", ""),
                    thread_id=event_data.get("threadId", {}).get("int"),
                    host_id=event_data.get("hostId", ""),
                    properties=event_data.get("properties", {}).get("map", {}),
                    source=data.get("source", ""),
                    ttp_labels=[]
                )
                
                return event
                
            # Xử lý các loại object khác (MemoryObject, FileObject, etc.) nếu cần
            # Hiện tại tập trung vào Event
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing log line: {e}")
            
        return None
    
    def process_log_file(self, file_path: str) -> List[LogEvent]:
        """Xử lý một file log"""
        logger.info(f"Processing log file: {file_path}")
        events = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        event = self.parse_cdm_log(line)
                        if event:
                            # Áp dụng luật TTP
                            event.ttp_labels = self.rule_engine.apply_rules(event)
                            events.append(event)
                            
                            # Cập nhật thống kê
                            for label in event.ttp_labels:
                                self.ttp_statistics[label.technique_id] += 1
                            
                        if line_num % 1000 == 0:
                            logger.info(f"Processed {line_num} lines")
                            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            
        self.processed_events.extend(events)
        logger.info(f"Processed {len(events)} events from {file_path}")
        return events
    
    def process_directory(self, directory_path: str) -> List[LogEvent]:
        """Xử lý tất cả file JSON trong thư mục"""
        logger.info(f"Processing directory: {directory_path}")
        all_events = []
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    events = self.process_log_file(file_path)
                    all_events.extend(events)
        
        return all_events
    
    def export_labeled_data(self, output_path: str, format_type: str = "json"):
        """Export dữ liệu đã gán nhãn"""
        logger.info(f"Exporting labeled data to: {output_path}")
        
        if format_type == "json":
            self._export_json(output_path)
        elif format_type == "graph":
            self._export_graph_format(output_path)
        else:
            logger.error(f"Unsupported export format: {format_type}")
    
    def _export_json(self, output_path: str):
        """Export dữ liệu dạng JSON"""
        export_data = []
        
        for event in self.processed_events:
            event_dict = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "subject_id": event.subject_id,
                "object_id": event.object_id,
                "thread_id": event.thread_id,
                "host_id": event.host_id,
                "properties": event.properties,
                "source": event.source,
                "ttp_labels": [
                    {
                        "technique_id": label.technique_id,
                        "technique_name": label.technique_name,
                        "tactic": label.tactic,
                        "description": label.description,
                        "confidence": label.confidence
                    }
                    for label in event.ttp_labels
                ]
            }
            export_data.append(event_dict)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def _export_graph_format(self, output_path: str):
        """Export dữ liệu dạng graph (nodes và edges)"""
        nodes = []
        edges = []
        
        # Tạo nodes và edges từ events
        for event in self.processed_events:
            # Subject node
            if event.subject_id:
                nodes.append({
                    "id": event.subject_id,
                    "type": "subject",
                    "ttp_labels": [label.technique_id for label in event.ttp_labels]
                })
            
            # Object node
            if event.object_id:
                nodes.append({
                    "id": event.object_id,
                    "type": "object",
                    "ttp_labels": []
                })
            
            # Edge
            if event.subject_id and event.object_id:
                edges.append({
                    "source": event.subject_id,
                    "target": event.object_id,
                    "relation": event.event_type,
                    "timestamp": event.timestamp,
                    "ttp_labels": [label.technique_id for label in event.ttp_labels]
                })
        
        # Remove duplicates
        unique_nodes = {node["id"]: node for node in nodes}.values()
        
        graph_data = {
            "nodes": list(unique_nodes),
            "edges": edges
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
    
    def print_statistics(self):
        """In thống kê TTP đã phát hiện"""
        logger.info("=== TTP Detection Statistics ===")
        logger.info(f"Total events processed: {len(self.processed_events)}")
        logger.info(f"Events with TTP labels: {sum(1 for e in self.processed_events if e.ttp_labels)}")
        
        if self.ttp_statistics:
            logger.info("TTP Techniques detected:")
            for technique_id, count in sorted(self.ttp_statistics.items()):
                logger.info(f"  {technique_id}: {count} events")
        else:
            logger.info("No TTP techniques detected")

def main():
    """Hàm main để chạy chương trình"""
    # Khởi tạo processor
    processor = LogProcessor()
    
    # Ví dụ sử dụng
    # Xử lý một file
    # events = processor.process_log_file("path/to/your/logfile.json")
    
    # Hoặc xử lý toàn bộ thư mục
    # events = processor.process_directory("path/to/your/log/directory")
    
    # Export kết quả
    # processor.export_labeled_data("output_labeled_events.json", "json")
    # processor.export_labeled_data("output_graph.json", "graph")
    
    # In thống kê
    # processor.print_statistics()
    
    print("TTP Labeling System initialized successfully!")
    print("Usage:")
    print("1. processor.process_log_file('file.json') - Process single file")
    print("2. processor.process_directory('directory/') - Process all JSON files in directory")
    print("3. processor.export_labeled_data('output.json') - Export results")
    print("4. processor.print_statistics() - Show detection statistics")

if __name__ == "__main__":
    main()
