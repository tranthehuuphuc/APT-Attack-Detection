# APT Attack Detection - Phân Tích Hiện Trạng & Đánh Giá

## ✅ **CÓ THỂ CHẠY ĐƯỢC**

### 1. **CTI Agent Pipeline** ✅
**Trạng thái**: CÓ THỂ CHẠY NGAY (với điều kiện)

**Điều kiện**:
- ✅ Code hoàn chỉnh trong `src/pipeline/agent/`
- ❌ Thiếu dữ liệu:
  - `data/mitre/enterprise-attack.json` (MITRE ATT&CK STIX)
  - `data/cti_reports/rss_seeds.txt` (RSS feeds)
- ⚠️ Cần OpenAI API key hoặc cài đặt g4f

**Cách chạy**:
```bash
# Tải MITRE ATT&CK STIX
mkdir -p data/mitre
wget https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
  -O data/mitre/enterprise-attack.json

# Tạo RSS seeds
mkdir -p data/cti_reports
cat > data/cti_reports/rss_seeds.txt << 'EOF'
https://www.cisa.gov/cybersecurity-advisories/all.xml
https://www.bleepingcomputer.com/feed/
https://thehackernews.com/feeds/posts/default
EOF

# Chạy agent
export OPENAI_API_KEY="sk-..."
python -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json
```

---

### 2. **Hunting Pipeline** ⚠️
**Trạng thái**: CÓ CODE NHƯNG THIẾU NHIỀU THỨ

**Thiếu**:
1. ❌ **GNN Engine** (`src/engine/graph_matcher/engine_repo/`) - QUAN TRỌNG NHẤT
2. ❌ **DARPA TC datasets** (cadets, theia, trace)
3. ❌ **Trained checkpoint** (`.pt` files)
4. ❌ **Audit events** (`runs/events/events.jsonl`)

**Lý do không chạy được ngay**:
- Engine repo cần clone từ repo riêng (URL không có trong code)
- Dataset DARPA TC cần download/mount riêng
- Checkpoint cần train trước hoặc download pretrained

---

### 3. **Training Pipeline** ❌
**Trạng thái**: CÓ CODE NHƯNG KHÔNG THỂ CHẠY

**Thiếu**:
1. ❌ GNN Engine code
2. ❌ DARPA TC datasets với cấu trúc đúng
3. ❌ Data preprocessing scripts

---

## 🔍 **ĐÁNH GIÁ EVALUATION CODE**

### Files Evaluation Hiện Tại
```python
# src/eval/agent_eval.py
# ❌ CHỈ LÀ SCAFFOLD - CHƯA CÓ CODE THỰC TẾ
# Simple evaluation scaffold (optional): compute validity and counts.

# src/eval/hunting_eval.py  
# ❌ CHỈ LÀ SCAFFOLD - CHƯA CÓ CODE THỰC TẾ
# Simple evaluation scaffold (optional): record latency, graph size, alerts.
```

**KẾT LUẬN**: **KHÔNG CÓ** mã nguồn đánh giá LLM Agent và hunting thực tế.

---

## 📋 **DANH SÁCH CẦN BỔ SUNG**

### 🔴 **Priority 1 - Bắt Buộc để Chạy**

1. **GNN Engine Repository**
   - Clone/download engine code vào `src/engine/graph_matcher/engine_repo/`
   - Cần biết URL của MEGR-APT engine

2. **MITRE ATT&CK Data**
   ```bash
   mkdir -p data/mitre
   wget https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
     -O data/mitre/enterprise-attack.json
   ```

3. **CTI RSS Feeds**
   ```bash
   mkdir -p data/cti_reports
   # Tạo file rss_seeds.txt với các RSS feeds
   ```

4. **Sample Events Data**
   - Tạo sample events cho testing hunting pipeline
   - Hoặc setup auditd trên Ubuntu để thu thập real events

### 🟡 **Priority 2 - Cần cho Production**

5. **DARPA TC Datasets**
   - Download DARPA Transparent Computing datasets
   - Cấu trúc theo `configs/datasets.yaml`:
     ```
     data/datasets/
       darpa_cadets/experiments/DEMO/
       darpa_theia/experiments/DEMO/
       darpa_trace/experiments/DEMO/
     ```

6. **Pretrained Checkpoints**
   - Train hoặc download pretrained GNN models
   - Lưu vào `runs/checkpoints/`

7. **Evaluation Code**
   - Implement `src/eval/agent_eval.py`:
     - Precision/Recall của technique extraction
     - IoC extraction accuracy
   - Implement `src/eval/hunting_eval.py`:
     - Detection rate
     - False positive rate
     - Latency metrics

### 🟢 **Priority 3 - Nice to Have**

8. **Demo Data**
   - Synthetic attack scenarios
   - Sample CTI reports
   - Pre-generated query graphs

9. **Documentation**
   - API documentation
   - Architecture diagrams
   - Deployment guide

10. **CI/CD**
    - Unit tests
    - Integration tests
    - Docker containers

---

## 💻 **SOLUTION: Notebook Quản Lý Toàn Bộ**

Cần tạo một **Jupyter Notebook** với các tính năng:

### Features:
1. ✅ **Environment Setup**
   - Check Python version
   - Install dependencies (hunting, agent, g4f)
   - Verify installations

2. ✅ **Data Download & Preparation**
   - Download MITRE ATT&CK STIX
   - Setup RSS feeds
   - Create sample events (nếu không có auditd)

3. ✅ **Engine Bootstrap**
   - Guide để clone engine repo (với placeholder URL)
   - Link datasets (nếu có)

4. ✅ **Pipeline Execution**
   - **CTI Agent**: Chạy với configurable params
   - **Hunting**: Mock/demo mode nếu không có engine
   - **Training**: Guide để train khi có đủ data

5. ✅ **Evaluation & Visualization**
   - Load results
   - Visualize techniques
   - Show provenance graphs
   - Metrics dashboard

6. ✅ **Troubleshooting**
   - Common errors & fixes
   - Environment checks
   - Dependency verification

---

## 🎯 **ROADMAP ĐỂ HOÀN CHỈNH**

### Phase 1: Demo Mode (1-2 ngày)
- [ ] Tạo comprehensive notebook
- [ ] Download MITRE data
- [ ] Setup sample CTI feeds
- [ ] Mock hunting với synthetic events
- [ ] Chạy CTI Agent end-to-end

### Phase 2: Evaluation (3-5 ngày)
- [ ] Implement agent_eval.py (precision/recall)
- [ ] Implement hunting_eval.py (detection metrics)
- [ ] Create test dataset cho evaluation
- [ ] Benchmark LLM backends (OpenAI vs g4f)

### Phase 3: Full System (1-2 tuần)
- [ ] Integrate GNN engine (cần access repo)
- [ ] Setup DARPA TC datasets
- [ ] Train models
- [ ] Deploy real-time hunting
- [ ] End-to-end testing

---

## ⚡ **QUICK START (Chỉ CTI Agent)**

```bash
# 1. Setup environment
python3.8 -m venv .venv
source .venv/bin/activate
pip install -r requirements/agent.txt

# 2. Download MITRE data
mkdir -p data/mitre
wget https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
  -O data/mitre/enterprise-attack.json

# 3. Create RSS feeds
mkdir -p data/cti_reports
cat > data/cti_reports/rss_seeds.txt << 'EOF'
https://www.cisa.gov/cybersecurity-advisories/all.xml
https://www.bleepingcomputer.com/feed/
EOF

# 4. Run agent (with g4f - no API key needed)
pip install -r requirements/g4f.txt
python -m src.pipeline.agent.main \
  --rss-file data/cti_reports/rss_seeds.txt \
  --stix data/mitre/enterprise-attack.json \
  --out-seeds runs/cti/seeds.json \
  --llm-backend g4f

# 5. Check results
cat runs/cti/seeds.json | python -m json.tool
ls -lh runs/cti/
ls -lh data/query_graphs/
```

---

## 📊 **ĐÁNH GIÁ TỔNG THỂ**

| Component | Status | Can Run? | Missing |
|-----------|--------|----------|---------|
| CTI Agent | ✅ Complete | ✅ Yes | MITRE data, RSS feeds |
| Hunting Pipeline | ⚠️ Partial | ❌ No | Engine, datasets, checkpoint |
| Training Pipeline | ⚠️ Partial | ❌ No | Engine, datasets |
| Evaluation | ❌ Scaffold only | ❌ No | Implementation code |
| Notebook | ⚠️ Basic | ⚠️ Limited | Comprehensive version |

**OVERALL**: Repository có **framework tốt** nhưng thiếu **data**, **engine**, và **evaluation code** để chạy full system.
