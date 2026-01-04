# 🤖 CTI Agent - LLM Backend Options

## Tình Huống Hiện Tại

g4f version mới có nhiều compatibility issues. **Khuyến nghị sử dụng OpenAI API**.

---

## ✅ Option 1: OpenAI API (RECOMMENDED)

### Setup

```bash
# Get API key from: https://platform.openai.com/api-keys
# Tạo key mới nếu chưa có

# Set environment variable
export OPENAI_API_KEY="sk-proj-xxxxxxxxxxxx"

# Run CTI Agent
python3 -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --llm-backend openai \
  --per-source-limit 10
```

### Cost Estimate

- **Model**: gpt-4o-mini (cheap & fast)
- **Per report**: ~$0.001-0.002
- **10 reports x 5 sources = 50 reports**: ~$0.05-0.10
- **Total cost**: < $0.15

### Advantages

- ✅ Reliable & stable
- ✅ High quality extraction
- ✅ Fast response
- ✅ Low cost

---

## ⚡ Option 2: Demo Mode (FREE - No LLM needed)

Dùng pre-generated CTI seeds từ example data.

### Create Demo Seeds

```bash
cd /opt/apt-detection
source .venv/bin/activate

# Create demo seeds with realistic data
python3 << 'EOF'
import json
from pathlib import Path

# Realistic CTI seeds based on common APT techniques
demo_seeds = {
    "techniques": [
        {"technique_id": "T1566.001", "name": "Spearphishing Attachment", "confidence": 0.85},
        {"technique_id": "T1059.001", "name": "PowerShell", "confidence": 0.90},
        {"technique_id": "T1071.001", "name": "Web Protocols", "confidence": 0.75},
        {"technique_id": "T1105", "name": "Ingress Tool Transfer", "confidence": 0.80},
        {"technique_id": "T1055", "name": "Process Injection", "confidence": 0.70},
        {"technique_id": "T1027", "name": "Obfuscated Files or Information", "confidence": 0.78},
        {"technique_id": "T1082", "name": "System Information Discovery", "confidence": 0.65},
        {"technique_id": "T1083", "name": "File and Directory Discovery", "confidence": 0.68},
        {"technique_id": "T1003", "name": "OS Credential Dumping", "confidence": 0.82},
        {"technique_id": "T1021.001", "name": "Remote Desktop Protocol", "confidence": 0.72},
    ],
    "indicators": [
        {"type": "file_hash", "value": "d41d8cd98f00b204e9800998ecf8427e"},
        {"type": "file_hash", "value": "5d41402abc4b2a76b9719d911017c592"},
        {"type": "ip_address", "value": "192.0.2.1"},
        {"type": "ip_address", "value": "198.51.100.42"},
        {"type": "domain", "value": "malicious-domain.example"},
        {"type": "domain", "value": "c2-server.example"},
        {"type": "url", "value": "http://evil.example/payload"},
        {"type": "file_path", "value": "C:\\Windows\\Temp\\malware.exe"},
    ]
}

# Save
Path("runs/cti").mkdir(parents=True, exist_ok=True)
Path("runs/cti/seeds.json").write_text(json.dumps(demo_seeds, indent=2))

print("✅ Demo seeds created: runs/cti/seeds.json")
print(f"   Techniques: {len(demo_seeds['techniques'])}")
print(f"   Indicators: {len(demo_seeds['indicators'])}")
EOF
```

### Verify Demo Seeds

```bash
cat runs/cti/seeds.json | python3 -m json.tool
```

---

## 🔧 Option 3: Fix g4f (Advanced - Not Recommended)

Nếu vẫn muốn dùng g4f, cần downgrade:

```bash
pip uninstall -y g4f
pip install g4f==0.3.0  # Old stable version

# Then try again
python3 -m src.pipeline.agent.main ... --llm-backend g4f
```

**Warning**: Old g4f versions may have other issues.

---

## 🎯 Recommended Workflow

### For Evaluation/Testing

**Use Demo Mode** (free, instant):
```bash
# Create demo seeds (copy script above)
python3 create_demo_seeds.py

# Skip CTI Agent, go directly to scenarios
bash scripts/run_experiments.sh
```

### For Production/Real Evaluation

**Use OpenAI** (reliable, cheap):
```bash
export OPENAI_API_KEY="your-key"
python3 -m src.pipeline.agent.main --llm-backend openai --per-source-limit 10
```

---

## 📊 Comparison

| Option | Cost | Time | Quality | Reliability |
|--------|------|------|---------|-------------|
| **OpenAI** | ~$0.10 | 5-10 min | High | ★★★★★ |
| **Demo** | Free | 1 sec | Medium | ★★★★★ |
| **g4f** | Free | Variable | Low-Med | ★☆☆☆☆ |

---

## ✅ Quick Decision Guide

**Muốn quality cao + có budget nhỏ?**
→ Dùng OpenAI ($0.10)

**Chỉ cần test system flow?**
→ Dùng Demo mode (free)

**Research paper cần reproducibility?**
→ Dùng OpenAI (document API version)

---

## 🚀 Next Steps

**Option A: OpenAI (Recommended)**
```bash
export OPENAI_API_KEY="sk-..."
python3 -m src.pipeline.agent.main --llm-backend openai --per-source-limit 10
```

**Option B: Demo mode**
```bash
# Run demo script above
# Then continue with scenarios
bash scripts/run_experiments.sh
```

---

**Recommendation**: Dùng OpenAI cho real evaluation, cost rất thấp (~$0.10) nhưng quality cao và reliable. 🎯
