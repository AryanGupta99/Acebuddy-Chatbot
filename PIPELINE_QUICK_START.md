# 🚀 Complete Data-to-LLM Pipeline Quick Start

## ⚡ 30-Second Start

Ensure Docker is running, then execute:

```powershell
cd C:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG
.\run_complete_pipeline.ps1
```

That's it! The pipeline will:
1. ✅ Clean your KB data (PII redacted, duplicates removed)
2. ✅ Generate embeddings
3. ✅ Index into ChromaDB
4. ✅ Test with LLM queries
5. ✅ Report quality metrics

---

## 📋 What the Pipeline Does

### Step 1: Data Preparation
- **Input:** KB files from `data/kb/` (.txt, .md, .json)
- **Processing:**
  - Cleans text (UTF-8, whitespace, punctuation)
  - Detects & redacts 8 PII types (emails, phones, SSN, credit cards, IPs, DOB, passwords, API keys)
  - Removes duplicates (SHA256 hashing)
  - Scores quality (0-1 scale)
  - Chunks semantically (500 chars per chunk)
- **Output:** 3 files in `data/prepared/`
  - `documents_cleaned.json` - Clean documents
  - `chunks_for_rag.json` - RAG-ready chunks (100+)
  - `preparation_report.json` - Quality metrics

### Step 2: RAG Ingestion
- **Input:** `data/prepared/chunks_for_rag.json`
- **Processing:**
  - Generate embeddings (SentenceTransformer)
  - Filter by quality (0.3+ threshold)
  - Batch process for efficiency
  - Store in ChromaDB with metadata
- **Output:** `acebuddy_kb` collection with 100+ vectors

### Step 3: LLM Testing (Optional)
- **Input:** 5 sample test queries
- **Processing:**
  - Retrieve context from ChromaDB
  - Generate Ollama responses
  - Score confidence
- **Output:** Test results summary

---

## 🎯 Execution Options

### Option 1: Complete Pipeline (Recommended)
```powershell
.\run_complete_pipeline.ps1
```
Runs all steps end-to-end with verification.

### Option 2: Skip API Testing (Faster)
```powershell
.\run_complete_pipeline.ps1 -SkipApiTest
```
Faster execution, skips LLM query testing.

### Option 3: Python Direct
```powershell
python scripts/full_pipeline.py
python scripts/full_pipeline.py --skip-api-test
```

### Option 4: Individual Steps
```powershell
# Just prepare data
python scripts/data_preparation.py

# Just ingest
python scripts/rag_ingestion.py

# Both with testing
python scripts/full_pipeline.py
```

---

## ✅ Pre-Execution Checklist

- [ ] Docker Desktop is running
- [ ] Services are up: `docker-compose up -d`
- [ ] Python 3.10+ installed: `python --version`
- [ ] Packages installed: `pip install chromadb sentence-transformers requests`
- [ ] KB files exist in `data/kb/`

---

## 📊 Expected Results

**After successful execution:**

✅ `data/prepared/documents_cleaned.json` created (9 documents)  
✅ `data/prepared/chunks_for_rag.json` created (105+ chunks)  
✅ `data/prepared/preparation_report.json` created (quality metrics)  
✅ ChromaDB `acebuddy_kb` collection populated (100+ vectors)  
✅ Quality report shows PII redaction count  
✅ Duplicates removed  
✅ All quality scores assigned  

**Example metrics:**
```json
{
  "documents_processed": 9,
  "chunks_created": 109,
  "chunks_ingested": 105,
  "quality_filtered": 4,
  "pii_detected": 3,
  "processing_time": "5.2s"
}
```

---

## 🔍 Verify Results

### Check Data Preparation
```powershell
# List output files
ls data/prepared/

# View quality report
Get-Content data/prepared/preparation_report.json | ConvertFrom-Json | Format-Table

# Count chunks
(Get-Content data/prepared/chunks_for_rag.json | ConvertFrom-Json).Count
```

### Check ChromaDB
```powershell
# Health check
curl http://localhost:8001/api/v1/heartbeat

# Get collection stats
curl "http://localhost:8001/api/v1/collections/acebuddy_kb"
```

### Test API
```powershell
# Health check
curl http://localhost:8000/health

# Test a query
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"query":"How do I reset my password?","user_id":"test"}'
```

---

## ⚙️ Customization

### Change Chunk Size
Edit `scripts/data_preparation.py` line ~350:
```python
DataChunker(chunk_size=750, overlap=50)  # Default: 500
```

### Increase Quality Threshold
Edit `scripts/full_pipeline.py`:
```python
ingester.ingest_chunks(..., min_quality_score=0.6)  # Default: 0.3
```

### Use GPU for Embeddings
```powershell
$env:EMBEDDING_OFFLINE = "false"  # Default: true for dev
```

### Change Batch Size
Edit `scripts/rag_ingestion.py`:
```python
ingester.ingest_chunks(..., batch_size=100)  # Default: 50
```

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| Docker not running | `docker-compose up -d` |
| Python not found | Install Python 3.10+ |
| Modules missing | `pip install chromadb sentence-transformers requests` |
| Chroma connection error | `docker-compose restart acebuddy-chroma` |
| No chunks created | Check `data/kb/` has files |
| API not responding | Check `docker-compose logs acebuddy-api` |

---

## 📈 Performance Metrics

| Phase | Duration | Throughput |
|-------|----------|-----------|
| Data Preparation | 2-5s | 50+ docs/sec |
| Embedding Gen | 3-10s | 20+ chunks/sec |
| Ingestion | 5-15s | 10+ chunks/sec |
| LLM Testing | 20-30s | Per query |
| **Total** | **30-60s** | Complete pipeline |

---

## 📚 Additional Documentation

- `README.md` - Full project documentation
- `RUN_PIPELINE_GUIDE.md` - Complete execution guide (if in parent folder)
- `SESSION_DELIVERY_SUMMARY.md` - Delivery overview (if in parent folder)

---

## 🎓 File Locations

All pipeline files are in the AceBuddy-RAG folder:

```
C:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG\

├── scripts/
│   ├── data_preparation.py      ← Data cleaning (500+ lines)
│   ├── rag_ingestion.py         ← Vector indexing (300+ lines)
│   └── full_pipeline.py         ← Orchestrator (400+ lines)
├── run_complete_pipeline.ps1    ← Entry point
├── data/
│   ├── kb/                      ← Your KB files (input)
│   └── prepared/                ← Output (created by pipeline)
└── README.md                    ← This file
```

---

## 🚀 Ready?

Execute the pipeline:

```powershell
.\run_complete_pipeline.ps1
```

Your RAG system will be production-ready in under a minute! 🎉

---

**Status:** ✅ Complete & Ready  
**Location:** AceBuddy-RAG folder  
**Execution Time:** 30-60 seconds  
**Documentation:** Comprehensive  

Let's go! 🚀
