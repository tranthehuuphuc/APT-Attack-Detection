# 📄 PDF-Based CTI Agent with g4f

## Workflow LLM Processing từ PDF Files

Demonstrate được quá trình LLM xử lý CTI reports cho research.

---

## 🎯 Quy Trình

```
PDF Files → Extract Text → Chunk Text → g4f Process → Extract Techniques/IOCs → Seeds
```

---

## 🚀 Quick Start (On VM)

```bash
cd ~/apt-detection
git pull
source .venv/bin/activate

# Install PDF support
pip install PyPDF2

# Create PDF directory  
mkdir -p data/cti_reports/pdfs

# Add your PDF CTI reports to data/cti_reports/pdfs/
# Then run:
python3 scripts/process_pdf_cti.py --max-pdfs 5
```

---

## 📊 What It Does

1. Reads PDF files
2. Extracts text
3. Chunks text (~3500 chars each)
4. Processes each chunk with g4f LLM
5. Extracts MITRE techniques & IOCs
6. Merges results → `runs/cti/seeds.json`

---

## ✅ For Research

**Demonstrates LLM workflow**:
- Input: Static PDF CTI reports
- Processing: g4f-based extraction
- Output: Structured threat intelligence

**Document in thesis**: "X PDF reports processed with LLM, extracting Y MITRE techniques"

---

See full guide: `PDF_CTI_GUIDE.md`

**Quick**: `python3 scripts/process_pdf_cti.py` 🚀
