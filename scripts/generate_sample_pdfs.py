#!/usr/bin/env python3
"""
Generate sample CTI PDF reports using fpdf2 (no OpenSSL issues)
"""

from pathlib import Path

def create_sample_pdfs():
    """Create sample CTI reports as PDFs using fpdf2."""
    try:
        from fpdf import FPDF
    except ImportError:
        print("❌ fpdf2 not installed")
        print("Run: pip install fpdf2")
        return False
    
    # Create output directory
    output_dir = Path("data/cti_reports/pdfs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Report 1: APT29
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "APT29 (Cozy Bear) Threat Analysis Report", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(5)
    
    content_apt29 = """
THREAT INTELLIGENCE REPORT
APT29 - Advanced Persistent Threat

Executive Summary:
APT29, also known as Cozy Bear, is a sophisticated threat actor associated with
Russian intelligence services. This report analyzes recent campaigns.

Initial Access (MITRE ATT&CK):
- T1566.001: Spearphishing Attachment
  Attackers send targeted emails with malicious Office documents
- T1190: Exploit Public-Facing Application
  Exploitation of web servers and VPN gateways

Execution Techniques:
- T1059.001: PowerShell
  Heavy use of PowerShell for payload execution
- T1059.003: Windows Command Shell
  Batch scripts for lateral movement

Persistence:
- T1053.005: Scheduled Task/Job
  Created scheduled tasks for persistence
- T1543.003: Windows Service
  Malicious service installation

Indicators of Compromise (IOCs):
File Hashes:
  MD5: a1b2c3d4e5f6789012345678901234ab
  SHA256: 7a8b9c0d1e2f3456789abcdef0123456789abcdef0123456789abcdef012345

Network Indicators:
  IP: 192.0.2.45
  Domain: malicious-update.example
  URL: http://c2-server.example/beacon.php

Recommendations:
- Implement email filtering for suspicious attachments
- Monitor PowerShell execution logs
- Regular security updates for public-facing applications
"""
    
    for line in content_apt29.strip().split('\n'):
        pdf.cell(0, 5, line, ln=True)
    
    pdf.output(str(output_dir / "apt29_analysis.pdf"))
    print("✅ Created: apt29_analysis.pdf")
    
    # Report 2: Lazarus
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Lazarus Group Financial Sector Campaign", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(5)
    
    content_lazarus = """
CYBER THREAT REPORT
Lazarus Group - Financial Sector Targeting

Overview:
Lazarus Group continues targeting financial institutions worldwide.
This report covers recent activity observed in Q4 2024.

Attack Chain:

1. Initial Compromise:
   T1566.002: Spearphishing Link
   Employees received LinkedIn messages with malicious links

2. Execution:
   T1204.002: User Execution (Malicious File)
   T1106: Native API
   Direct system calls to avoid detection

3. Credential Access:
   T1003.001: LSASS Memory
   Mimikatz-like credential dumping
   T1555: Credentials from Password Stores

4. Lateral Movement:
   T1021.001: Remote Desktop Protocol
   T1021.002: SMB/Windows Admin Shares

5. Command and Control:
   T1071.001: Web Protocols
   HTTPS C2 communication
   T1573.002: Asymmetric Cryptography

Technical Indicators:
Malware Hashes:
  MD5: f1e2d3c4b5a6978012345678901234cd
  SHA1: abc123def456789012345678901234567890abcd

Infrastructure:
  C2 IP: 198.51.100.23
  Staging: download.legitimate-cdn.example
  Exfil: storage.cloud-backup.example

Registry Keys:
  HKLM Software Microsoft Windows CurrentVersion Run SystemUpdate

Mitigation:
- Network segmentation
- MFA for all accounts
- EDR deployment
"""
    
    for line in content_lazarus.strip().split('\n'):
        pdf.cell(0, 5, line, ln=True)
    
    pdf.output(str(output_dir / "lazarus_campaign.pdf"))
    print("✅ Created: lazarus_campaign.pdf")
    
    # Report 3: REvil Ransomware
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "REvil Ransomware Technical Analysis", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.ln(5)
    
    content_revil = """
MALWARE ANALYSIS REPORT
REvil (Sodinokibi) Ransomware

Sample Information:
MD5: 5d41402abc4b2a76b9719d911017c592
SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

MITRE ATT&CK Mapping:

Defense Evasion:
T1027: Obfuscated Files or Information
  String encryption and API hashing
T1055: Process Injection
  Code injection into legitimate processes
T1562.001: Disable or Modify Tools
  Terminates security software

Discovery:
T1082: System Information Discovery
T1083: File and Directory Discovery
T1018: Remote System Discovery
  Network scanning for lateral spread

Collection:
T1005: Data from Local System
T1039: Data from Network Shared Drive

Impact:
T1486: Data Encrypted for Impact
  AES-256 encryption of files
T1490: Inhibit System Recovery
  Deletes shadow copies and backups

Network IOCs:
Payment Portal: pay4decryption.onion
Leak Site: revil-leaks.onion

File Indicators:
Ransom Note: readme-decrypt.txt
Extension: .revil

Recovery:
- Isolate affected systems immediately
- Do not pay ransom
- Restore from offline backups
- Contact law enforcement
"""
    
    for line in content_revil.strip().split('\n'):
        pdf.cell(0, 5, line, ln=True)
    
    pdf.output(str(output_dir / "ransomware_analysis.pdf"))
    print("✅ Created: ransomware_analysis.pdf")
    
    return True

if __name__ == "__main__":
    print("=" * 70)
    print("Generating Sample CTI PDF Reports")
    print("=" * 70)
    print()
    
    if create_sample_pdfs():
        print()
        print("=" * 70)
        print("✅ Success! PDFs created in: data/cti_reports/pdfs/")
        print("=" * 70)
        print()
        print("Files created:")
        print("  1. apt29_analysis.pdf")
        print("  2. lazarus_campaign.pdf")
        print("  3. ransomware_analysis.pdf")
        print()
        print("Next: Run CTI Agent")
        print("  python3 -m src.pipeline.agent.main --pdf-dir data/cti_reports/pdfs --llm-backend g4f")
        print()
