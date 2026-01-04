#!/usr/bin/env python3
"""
Create demo CTI seeds for testing without LLM
Generates realistic MITRE techniques and IOCs
"""

import json
from pathlib import Path

# Realistic CTI seeds based on common APT patterns
demo_seeds = {
    "techniques": [
        # Initial Access
        {"technique_id": "T1566.001", "name": "Spearphishing Attachment", "confidence": 0.85, "tactics": ["initial-access"]},
        {"technique_id": "T1190", "name": "Exploit Public-Facing Application", "confidence": 0.78, "tactics": ["initial-access"]},
        
        # Execution
        {"technique_id": "T1059.001", "name": "PowerShell", "confidence": 0.90, "tactics": ["execution"]},
        {"technique_id": "T1059.003", "name": "Windows Command Shell", "confidence": 0.82, "tactics": ["execution"]},
        
        # Persistence
        {"technique_id": "T1053.005", "name": "Scheduled Task", "confidence": 0.76, "tactics": ["persistence"]},
        {"technique_id": "T1543.003", "name": "Windows Service", "confidence": 0.73, "tactics": ["persistence"]},
        
        # Defense Evasion
        {"technique_id": "T1027", "name": "Obfuscated Files or Information", "confidence": 0.78, "tactics": ["defense-evasion"]},
        {"technique_id": "T1055", "name": "Process Injection", "confidence": 0.70, "tactics": ["defense-evasion"]},
        
        # Credential Access
        {"technique_id": "T1003.001", "name": "LSASS Memory", "confidence": 0.82, "tactics": ["credential-access"]},
        {"technique_id": "T1552.001", "name": "Credentials In Files", "confidence": 0.68, "tactics": ["credential-access"]},
        
        # Discovery
        {"technique_id": "T1082", "name": "System Information Discovery", "confidence": 0.65, "tactics": ["discovery"]},
        {"technique_id": "T1083", "name": "File and Directory Discovery", "confidence": 0.68, "tactics": ["discovery"]},
        {"technique_id": "T1018", "name": "Remote System Discovery", "confidence": 0.72, "tactics": ["discovery"]},
        
        # Lateral Movement
        {"technique_id": "T1021.001", "name": "Remote Desktop Protocol", "confidence": 0.72, "tactics": ["lateral-movement"]},
        {"technique_id": "T1021.002", "name": "SMB/Windows Admin Shares", "confidence": 0.75, "tactics": ["lateral-movement"]},
        
        # Collection
        {"technique_id": "T1005", "name": "Data from Local System", "confidence": 0.70, "tactics": ["collection"]},
        {"technique_id": "T1119", "name": "Automated Collection", "confidence": 0.66, "tactics": ["collection"]},
        
        # Command and Control
        {"technique_id": "T1071.001", "name": "Web Protocols", "confidence": 0.75, "tactics": ["command-and-control"]},
        {"technique_id": "T1573.002", "name": "Asymmetric Cryptography", "confidence": 0.68, "tactics": ["command-and-control"]},
        
        # Exfiltration
        {"technique_id": "T1041", "name": "Exfiltration Over C2 Channel", "confidence": 0.77, "tactics": ["exfiltration"]},
        {"technique_id": "T1048.003", "name": "Exfiltration Over Alternative Protocol", "confidence": 0.71, "tactics": ["exfiltration"]},
        
        # Impact
        {"technique_id": "T1486", "name": "Data Encrypted for Impact", "confidence": 0.80, "tactics": ["impact"]},
        {"technique_id": "T1490", "name": "Inhibit System Recovery", "confidence": 0.74, "tactics": ["impact"]},
    ],
    "indicators": [
        # File hashes
        {"type": "file_hash", "value": "d41d8cd98f00b204e9800998ecf8427e", "algorithm": "MD5"},
        {"type": "file_hash", "value": "5d41402abc4b2a76b9719d911017c592", "algorithm": "MD5"},
        {"type": "file_hash", "value": "aec070645fe53ee3b3763059376134f058cc337247c978add178b6ccdfb0019f", "algorithm": "SHA256"},
        
        # Network indicators
        {"type": "ip_address", "value": "192.0.2.1"},
        {"type": "ip_address", "value": "198.51.100.42"},
        {"type": "ip_address", "value": "203.0.113.7"},
        {"type": "domain", "value": "malicious-domain.example"},
        {"type": "domain", "value": "c2-server.example"},
        {"type": "domain", "value": "phishing-site.example"},
        {"type": "url", "value": "http://evil.example/payload.exe"},
        {"type": "url", "value": "https://c2.example/beacon"},
        
        # File paths
        {"type": "file_path", "value": "C:\\Windows\\Temp\\malware.exe"},
        {"type": "file_path", "value": "C:\\Users\\Public\\update.dll"},
        {"type": "file_path", "value": "/tmp/backdoor.sh"},
        
        # Registry keys
        {"type": "registry_key", "value": "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Updater"},
        {"type": "registry_key", "value": "HKCU\\Software\\Classes\\CLSID\\{MALICIOUS-GUID}"},
    ],
    "metadata": {
        "generated_by": "demo_script",
        "generation_method": "synthetic",
        "note": "These are example seeds for testing. Real CTI Agent would extract from actual threat reports."
    }
}

def main():
    # Create output directory
    output_dir = Path("runs/cti")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save seeds
    output_file = output_dir / "seeds.json"
    output_file.write_text(json.dumps(demo_seeds, indent=2))
    
    print("=" * 70)
    print("✅ Demo CTI Seeds Created")
    print("=" * 70)
    print(f"\nOutput: {output_file}")
    print(f"\nStatistics:")
    print(f"  Techniques: {len(demo_seeds['techniques'])}")
    print(f"  Indicators: {len(demo_seeds['indicators'])}")
    print(f"\nTactics Coverage:")
    tactics = set()
    for tech in demo_seeds['techniques']:
        tactics.update(tech.get('tactics', []))
    for tactic in sorted(tactics):
        count = sum(1 for t in demo_seeds['techniques'] if tactic in t.get('tactics', []))
        print(f"  {tactic}: {count} techniques")
    
    print(f"\nIndicator Types:")
    from collections import Counter
    ind_types = Counter([i['type'] for i in demo_seeds['indicators']])
    for itype, count in ind_types.items():
        print(f"  {itype}: {count}")
    
    print("\n" + "=" * 70)
    print("Next steps:")
    print("  1. View seeds: cat runs/cti/seeds.json")
    print("  2. Run scenarios: bash scripts/run_experiments.sh")
    print("=" * 70)

if __name__ == "__main__":
    main()
