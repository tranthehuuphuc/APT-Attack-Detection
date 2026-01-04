# 🚀 Quick Start - APT Attack Detection

## Các Pipeline Có Thể Chạy Ngay

### ✅ 1. CTI Agent Pipeline (RECOMMENDED)

**Dependencies**: Chỉ cần MITRE ATT&CK data và OpenAI key hoặc g4f

```bash
# Mở notebook tổng quát
jupyter notebook notebooks/APT_Complete_System_Management.ipynb

# Hoặc chạy manual:

# Step 1: Setup
pip install -r requirements/agent.txt
pip install -r requirements/g4f.txt  # Nếu không có OpenAI key

# Step 2: Download MITRE data (có trong notebook)
mkdir -p data/mitre
wget https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
  -O data/mitre/enterprise-attack.json

# Step 3: Run agent
python -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --llm-backend g4f \
  --per-source-limit 5

# Step 4: Evaluate
python -m src.eval.agent_eval \
  --seeds runs/cti/seeds.json \
  --stix data/mitre/enterprise-attack.json
```

### ✅ 2. Hunting Pipeline (Mock Mode)

**Dependencies**: Sample events (có trong notebook)

```bash
# Chạy trong notebook section 5 hoặc:
python -m src.eval.hunting_eval \
  --events runs/events/events.jsonl \
  --benchmark-trials 10
```

### ❌ 3. Training & Full Hunting

**Cần**:
- GNN Engine repository
- DARPA Transparent Computing datasets
- Pretrained checkpoints

---

## 📖 Tài Liệu

| File | Mục đích |
|------|----------|
| `README.md` | Original documentation |
| `ANALYSIS_AND_GAPS.md` | ⭐ Chi tiết về pipelines và missing parts |
| `IMPROVEMENTS.md` | ⭐ Tổng hợp cải tiến đã làm |
| `notebooks/APT_Complete_System_Management.ipynb` | ⭐ Notebook toàn diện |

---

## 🎯 Các Tệp Quan Trọng

### Evaluation Code (MỚI)
- `src/eval/agent_eval.py`: Đánh giá CTI Agent (precision/recall/F1)
- `src/eval/hunting_eval.py`: Đánh giá Hunting (latency/throughput/detection)

### Notebook
- `notebooks/APT_Complete_System_Management.ipynb`: Quản lý toàn bộ từ A-Z

---

## 💡 Recommended Flow

1. **Đọc**: `ANALYSIS_AND_GAPS.md` để hiểu tổng quan
2. **Chạy**: Notebook section 1-4 (CTI Agent)
3. **Đánh giá**: `python -m src.eval.agent_eval --seeds runs/cti/seeds.json --stix data/mitre/enterprise-attack.json`
4. **Khám phá**: Notebook sections khác theo nhu cầu

---

**Xem chi tiết**: `IMPROVEMENTS.md` và `ANALYSIS_AND_GAPS.md`
