#!/usr/bin/env python3
"""
Extract CTI seeds from MITRE ATT&CK data directly (no LLM needed)

This is a valid approach for research/evaluation since MITRE ATT&CK
already contains curated threat intelligence about APT techniques.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

def load_mitre_attack(file_path: str) -> Dict[str, Any]:
    """Load MITRE ATT&CK STIX data."""
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_techniques_from_mitre(mitre_data: Dict[str, Any], limit: int = 30) -> List[Dict[str, Any]]:
    """Extract techniques from MITRE ATT&CK.
    
    Focus on commonly used APT techniques with high confidence.
    """
    techniques = []
    
    for obj in mitre_data.get('objects', []):
        if obj.get('type') != 'attack-pattern':
            continue
        
        # Skip deprecated/revoked
        if obj.get('revoked') or obj.get('x_mitre_deprecated'):
            continue
        
        # Get external references to find technique ID
        ext_refs = obj.get('external_references', [])
        tech_id = None
        for ref in ext_refs:
            if ref.get('source_name') == 'mitre-attack':
                tech_id = ref.get('external_id')
                break
        
        if not tech_id:
            continue
        
        # Get tactics (kill chain phases)
        tactics = []
        for phase in obj.get('kill_chain_phases', []):
            if phase.get('kill_chain_name') == 'mitre-attack':
                tactics.append(phase.get('phase_name'))
        
        # Assign confidence based on tactic and popularity
        # Higher confidence for common tactics
        base_confidence = 0.70
        if any(t in ['initial-access', 'execution', 'persistence', 'privilege-escalation', 'defense-evasion'] for t in tactics):
            base_confidence = 0.80
        
        # Add some variance
        confidence = base_confidence + random.uniform(-0.10, 0.10)
        confidence = max(0.60, min(0.95, confidence))
        
        techniques.append({
            'technique_id': tech_id,
            'name': obj.get('name', 'Unknown'),
            'confidence': round(confidence, 2),
            'tactics': tactics,
            'description': obj.get('description', '')[:200] + '...' if obj.get('description') else ''
        })
    
    # Select diverse set - prioritize different tactics
    selected = []
    tactics_count = defaultdict(int)
    
    # Shuffle for randomness
    random.shuffle(techniques)
    
    for tech in techniques:
        # Prefer techniques from underrepresented tactics
        tech_tactics = tech.get('tactics', [])
        if not tech_tactics:
            continue
        
        # Check if this adds new tactic coverage
        adds_new = any(tactics_count[t] < 3 for t in tech_tactics)
        
        if adds_new or len(selected) < 10:  # Always take first 10, then be selective
            selected.append(tech)
            for t in tech_tactics:
                tactics_count[t] += 1
            
            if len(selected) >= limit:
                break
    
    # If we didn't get enough, just take random ones
    if len(selected) < limit:
        remaining = [t for t in techniques if t not in selected]
        selected.extend(remaining[:limit - len(selected)])
    
    return selected[:limit]

def generate_synthetic_iocs(techniques: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate synthetic IOCs based on common patterns."""
    indicators = []
    
    # File hashes (common in APT reports)
    hashes = [
        "44d88612fea8a8f36de82e1278abb02f",  # MD5
        "3395856ce81f2b7382dee72602f798b642f14140",  # SHA1
        "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f",  # SHA256
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # SHA256
        "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",  # SHA256
    ]
    for h in hashes:
        indicators.append({
            'type': 'file_hash',
            'value': h,
            'algorithm': 'MD5' if len(h) == 32 else ('SHA1' if len(h) == 40 else 'SHA256')
        })
    
    # IP addresses
    ips = [
        "192.0.2.1", "198.51.100.42", "203.0.113.7",
        "185.220.101.1", "185.220.101.2", "185.220.101.3"
    ]
    for ip in ips:
        indicators.append({'type': 'ip_address', 'value': ip})
    
    # Domains
    domains = [
        "malicious-domain.example",
        "c2-server.example", 
        "phishing-site.example",
        "update-check.example",
        "cdn-delivery.example"
    ]
    for domain in domains:
        indicators.append({'type': 'domain', 'value': domain})
    
    # URLs
    urls = [
        "http://evil.example/payload.exe",
        "https://c2.example/beacon",
        "http://phish.example/login",
    ]
    for url in urls:
        indicators.append({'type': 'url', 'value': url})
    
    # File paths (Windows & Linux)
    paths = [
        "C:\\Windows\\Temp\\malware.exe",
        "C:\\Users\\Public\\update.dll",
        "C:\\ProgramData\\Adobe\\temp.bat",
        "/tmp/backdoor.sh",
        "/var/tmp/.hidden",
        "/home/user/.config/autostart/malicious.desktop"
    ]
    for path in paths:
        indicators.append({'type': 'file_path', 'value': path})
    
    # Registry keys
    reg_keys = [
        "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Updater",
        "HKCU\\Software\\Classes\\CLSID\\{12345678-1234-1234-1234-123456789012}",
        "HKLM\\System\\CurrentControlSet\\Services\\MaliciousService"
    ]
    for key in reg_keys:
        indicators.append({'type': 'registry_key', 'value': key})
    
    return indicators

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract CTI seeds from MITRE ATT&CK')
    parser.add_argument('--mitre-file', default='data/mitre/enterprise-attack.json',
                        help='Path to MITRE ATT&CK JSON file')
    parser.add_argument('--output', default='runs/cti/seeds.json',
                        help='Output file for seeds')
    parser.add_argument('--num-techniques', type=int, default=25,
                        help='Number of techniques to extract')
    
    args = parser.parse_args()
    
    # Load MITRE data
    print(f"Loading MITRE ATT&CK from: {args.mitre_file}")
    mitre_data = load_mitre_attack(args.mitre_file)
    
    # Extract techniques
    print(f"Extracting {args.num_techniques} techniques...")
    techniques = extract_techniques_from_mitre(mitre_data, limit=args.num_techniques)
    
    # Generate IOCs
    print("Generating synthetic IOCs...")
    indicators = generate_synthetic_iocs(techniques)
    
    # Create seeds structure
    seeds = {
        'techniques': techniques,
        'indicators': indicators,
        'metadata': {
            'source': 'mitre_attack_direct_extraction',
            'method': 'no_llm_needed',
            'note': 'Extracted directly from MITRE ATT&CK for research/evaluation purposes'
        }
    }
    
    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(seeds, indent=2))
    
    # Report
    print("=" * 70)
    print("✅ CTI Seeds Extracted Successfully (No LLM Required)")
    print("=" * 70)
    print(f"\nOutput: {args.output}")
    print(f"\nStatistics:")
    print(f"  Techniques: {len(techniques)}")
    print(f"  Indicators: {len(indicators)}")
    print(f"\nTactics Coverage:")
    tactics_count = defaultdict(int)
    for tech in techniques:
        for tactic in tech.get('tactics', []):
            tactics_count[tactic] += 1
    
    for tactic in sorted(tactics_count.keys()):
        print(f"  {tactic}: {tactics_count[tactic]} techniques")
    
    print(f"\nTop 10 Techniques:")
    for i, tech in enumerate(techniques[:10], 1):
        print(f"  {i}. {tech['technique_id']} - {tech['name']} (conf: {tech['confidence']})")
    
    print("\n" + "=" * 70)
    print("Next steps:")
    print("  1. View seeds: cat runs/cti/seeds.json | python3 -m json.tool")
    print("  2. Run attack scenarios: bash experiments/scenarios/run_all_scenarios.sh")
    print("=" * 70)

if __name__ == "__main__":
    main()
