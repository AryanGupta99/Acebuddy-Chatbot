# 🚀 Complete RAG Pipeline Execution Guide

This guide walks you through running your complete data-to-LLM pipeline.

## 📋 Prerequisites

Before running the pipeline, ensure:

1. **Docker Services Running**
   ```powershell
   cd "c:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"
   docker-compose up -d
   ```

2. **Verify Services**
   ```powershell
   docker-compose ps
   ```
   You should see:
   - ✅ `acebuddy-api` (FastAPI) - PORT 8000
   - ✅ `acebuddy-chroma` (ChromaDB) - PORT 8001
   - ✅ `ollama` (LLM) - PORT 11434

3. **Python Environment**
   - Python 3.10+ installed
   - Required packages:
     ```powershell
     pip install requests chromadb sentence-transformers
     ```

## 🏃 Quick Start: Run Complete Pipeline

### Option 1: PowerShell Script (Recommended)

```powershell
cd "c:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"
.\run_complete_pipeline.ps1
```

**Expected Output:**
- ✅ Setup verification
- ✅ Step 1: Data Preparation (cleaning, PII redaction)
- ✅ Step 2: RAG Ingestion (vector database)
- ✅ Step 3: LLM Testing (sample queries)
- ✅ Pipeline complete

### Option 2: Python Direct Execution

```powershell
cd "c:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"
python scripts/full_pipeline.py
```

### Option 3: Run Individual Steps

#### Step 1: Data Preparation Only
```powershell
python scripts/data_preparation.py
```
**Output Files:**
- `data/prepared/documents_cleaned.json` - Cleaned documents
- `data/prepared/chunks_for_rag.json` - RAG-ready chunks  
- `data/prepared/preparation_report.json` - Quality metrics

#### Step 2: Ingestion Only
```powershell
python scripts/rag_ingestion.py
```
**Expected:** Imports cleaned chunks into Chroma

#### Step 3: Test RAG with LLM
```powershell
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"query":"How do I reset my password?","user_id":"test"}'
```

## 📊 What the Pipeline Does

### Step 1: Data Preparation
✅ **Input:** Files from `data/kb/`

**Processing:**
- Cleans text (UTF-8 encoding, whitespace normalization)
- Redacts PII (emails, phone numbers, SSN, credit cards, IPs, DOB, passwords, API keys)
- Detects and removes duplicates
- Scores document quality (0-1 scale)
- Chunks text into RAG-appropriate sizes (500 chars default)

**Output:** 
- `documents_cleaned.json` - All cleaned documents with metadata
- `chunks_for_rag.json` - Chunks optimized for vector search
- `preparation_report.json` - Quality metrics and statistics

**Quality Metrics Example:**
```json
{
  "total_documents": 9,
  "documents_cleaned": 9,
  "documents_with_pii": 0,
  "duplicate_documents": 0,
  "total_chunks": 109,
  "chunks_valid": 105,
  "chunks_filtered_by_quality": 4,
  "avg_chunk_length": 487,
  "total_characters": 51000,
  "pii_patterns_found": {
    "emails": 3,
    "phone_numbers": 2,
    "ssn_patterns": 0,
    "credit_card_patterns": 0
  }
}
```

### Step 2: RAG Ingestion
✅ **Input:** `data/prepared/chunks_for_rag.json`

**Processing:**
- Loads cleaned chunks
- Generates embeddings using SentenceTransformer (`all-MiniLM-L6-v2`)
- Stores vectors in ChromaDB
- Preserves metadata (source, chunk_index, quality_score)
- Batches for efficient processing

**Output:** 
- ChromaDB collection: `acebuddy_kb`
- 100+ vectors ready for semantic search

**Ingestion Statistics:**
```
Total chunks processed: 109
Successfully ingested: 105
Failed: 0
Quality filtered: 4
Processing duration: 5.2 seconds
Throughput: 20.2 chunks/second
```

### Step 3: LLM Testing
✅ **Input:** Sample queries

**Processing:**
- Retrieves relevant context from Chroma
- Sends to Ollama phi model
- Generates context-aware responses
- Returns confidence scores

**Test Queries:**
- "How do I reset my password?"
- "I can't connect to RDP"
- "My disk is full"
- "How do I add a new user?"
- "My monitor isn't working"

## 🔍 Verification Steps

### Check Data Preparation
```powershell
# View cleaned documents
Get-Content data/prepared/documents_cleaned.json | ConvertFrom-Json | Select-Object -First 1 | ConvertTo-Json

# View quality report
Get-Content data/prepared/preparation_report.json | ConvertFrom-Json
```

### Check Chroma Ingestion
```powershell
# Query Chroma API
curl -X GET http://localhost:8001/api/v1/heartbeat

# List collections
curl -X GET http://localhost:8001/api/v1/collections

# Get collection stats
curl -X GET "http://localhost:8001/api/v1/collections/acebuddy_kb"
```

### Test API Health
```powershell
# Check FastAPI
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"query":"Help","user_id":"test"}'
```

## 🛠️ Troubleshooting

### Issue: "Docker containers not running"
```powershell
docker-compose up -d
docker-compose logs -f acebuddy-api
```

### Issue: "Chroma connection refused"
```powershell
# Check Chroma is running
curl http://localhost:8001/api/v1/heartbeat

# If not, restart
docker-compose restart acebuddy-chroma
```

### Issue: "Python packages missing"
```powershell
pip install --upgrade chromadb sentence-transformers requests
```

### Issue: "API returns no context"
```powershell
# Verify data was ingested
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"query":"password","user_id":"test"}'

# Check logs
docker-compose logs acebuddy-api | tail -20
```

## 📈 Performance Expectations

| Phase | Duration | Notes |
|-------|----------|-------|
| Data Preparation | 2-5 seconds | Depends on KB size |
| Embedding Gen | 3-10 seconds | 100+ chunks → vectors |
| Ingestion | 5-15 seconds | Batch processing |
| LLM Response | 5-30 seconds | Ollama model loading |

## 🎯 Next Steps After Pipeline Success

1. **Review Quality Report**
   - Open `data/prepared/preparation_report.json`
   - Verify PII was redacted
   - Check quality scores

2. **Test Custom Queries**
   ```powershell
   curl -X POST http://localhost:8000/chat `
     -H "Content-Type: application/json" `
     -d '{"query":"Your custom question","user_id":"test"}'
   ```

3. **Implement Advanced NLP** (From Phase 1 Analysis)
   - Intent Classification
   - Response Quality Grading
   - Escalation Logic
   - See `RAG_NLP_ANALYSIS.md` for details

4. **Monitor & Optimize**
   - Check response quality
   - Analyze query patterns
   - Refine chunks if needed
   - Add more KB documents as needed

## 📚 Related Documentation

- **`RAG_NLP_ANALYSIS.md`** - Complete technical analysis
- **`QUICK_STATUS_LLM_NLP.md`** - Current status and gaps
- **`READY_TO_CODE_SOLUTIONS.md`** - Implementation roadmap
- **`README.md`** - API documentation

## ✅ Success Indicators

Pipeline is **complete and successful** when:

✅ Data preparation creates `data/prepared/` directory  
✅ `documents_cleaned.json` contains cleaned documents  
✅ `chunks_for_rag.json` contains 100+ chunks  
✅ `preparation_report.json` shows quality metrics  
✅ Chroma ingestion completes without errors  
✅ LLM test queries return context-aware responses  
✅ API endpoints respond with 200 status  

---

**Ready to run? Execute:** `.\run_complete_pipeline.ps1`

**Questions? Check:** `RUN_PIPELINE_GUIDE.md` (this file)
