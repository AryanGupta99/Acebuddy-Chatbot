# ⚡ Quick Reference: Data-to-LLM Pipeline

## 🚀 30-Second Start

```powershell
cd "c:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"
.\run_complete_pipeline.ps1
```

## 📋 What Gets Done

| Step | What | Duration |
|------|------|----------|
| 1️⃣ **Clean Data** | Remove PII, duplicates, score quality | ~3-5s |
| 2️⃣ **Ingest** | Store vectors in Chroma | ~5-10s |
| 3️⃣ **Test** | Query with LLM (optional) | ~20-30s |

## 📂 Output Files Created

After running, you'll have:

```
data/prepared/
├── documents_cleaned.json      ← All cleaned documents
├── chunks_for_rag.json         ← 100+ chunks ready for search
└── preparation_report.json     ← Quality metrics
```

## 🎯 Key Files for This Session

| File | Purpose | Size |
|------|---------|------|
| `scripts/data_preparation.py` | Clean & validate data | 500+ lines |
| `scripts/rag_ingestion.py` | Index into Chroma | 300+ lines |
| `scripts/full_pipeline.py` | Orchestrate everything | 400+ lines |
| `run_complete_pipeline.ps1` | Run from PowerShell | Simple |
| `RUN_PIPELINE_GUIDE.md` | Full execution guide | Detailed |

## ✅ Quality Features

- ✅ **8 PII patterns detected** (emails, phones, SSN, credit cards, IPs, DOB, passwords, API keys)
- ✅ **SHA256 duplicate detection** (prevents indexing same content twice)
- ✅ **Quality scoring** (0-1 scale, filters low quality)
- ✅ **Semantic chunking** (500 char optimal size)
- ✅ **Metadata preservation** (source, quality score, chunk index)

## 🔍 Verify It Works

### Check data was prepared:
```powershell
ls data/prepared/
Get-Content data/prepared/preparation_report.json | ConvertFrom-Json
```

### Check API is running:
```powershell
curl http://localhost:8000/health
```

### Test a query:
```powershell
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"query":"password reset","user_id":"test"}'
```

## 🛠️ Common Commands

| Need | Command |
|------|---------|
| Run pipeline | `.\run_complete_pipeline.ps1` |
| Check services | `docker-compose ps` |
| View logs | `docker-compose logs -f acebuddy-api` |
| Just prepare data | `python scripts/data_preparation.py` |
| Just ingest | `python scripts/rag_ingestion.py` |
| Stop services | `docker-compose down` |

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" | `docker-compose up -d` |
| "Python not found" | Install Python 3.10+ |
| "Module not found" | `pip install chromadb sentence-transformers requests` |
| "No chunks created" | Check `data/kb/` has files |

## 📊 Expected Results

After running pipeline:

```
✅ Total documents: 9 (from data/kb/)
✅ Chunks created: 109
✅ Chunks ingested: 105
✅ Quality filtered: 4
✅ Vectors in Chroma: 105
✅ PII patterns found: 3-5 (all redacted)
✅ Duplicates removed: 0-2
✅ Processing time: 15-45 seconds total
```

## 📖 Where to Learn More

1. **Quick execution** → `RUN_PIPELINE_GUIDE.md`
2. **Full architecture** → `RAG_NLP_ANALYSIS.md`
3. **What's missing** → `QUICK_STATUS_LLM_NLP.md`
4. **Implementation steps** → `READY_TO_CODE_SOLUTIONS.md`
5. **API endpoints** → `README.md`

## 🎯 Next After Pipeline Succeeds

1. ✅ Review quality report (`preparation_report.json`)
2. ✅ Test with your own questions
3. ✅ Check response quality
4. ⏳ Implement advanced NLP (intent classification, response grading)
5. ⏳ Add more KB documents and re-run

## 💡 Pro Tips

- Run without API test: `.\run_complete_pipeline.ps1 -SkipApiTest`
- Specify custom base dir: `.\run_complete_pipeline.ps1 -BaseDir "C:\path"`
- Check individual steps: See `full_pipeline.py` code
- Customize chunk size: Edit `data_preparation.py` line ~180
- Change quality threshold: Edit `rag_ingestion.py` line ~45

---

**You're Ready!** Just run: `.\run_complete_pipeline.ps1`
