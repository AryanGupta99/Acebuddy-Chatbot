# AceBuddy RAG Chatbot - Complete Deployment Guide

**Status:** Production-Ready Local Build | Ready for Migration  
**Last Updated:** 2024  
**Version:** 1.0.0

---

## 📋 Quick Start (5 Minutes)

### Prerequisites
- Windows laptop with:
  - Docker Desktop installed and running
  - Ollama installed with `mistral` model
  - 16GB RAM (4GB+ free), 50GB disk space
  - PowerShell or Command Prompt

### Quick Start Commands
```powershell
# Navigate to project
cd "C:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"

# Start everything
docker-compose up --build -d

# Wait 30 seconds for services to initialize...

# Test it works
curl http://localhost:8000/health
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{"query":"How do I reset my password?","user_id":"test"}'

# View logs
docker logs -f acebuddy-api
```

**Expected:** Health check returns `{"status":"healthy"}` and chat returns an answer from the knowledge base.

---

## 📁 What's Included

### Documentation (Start Here!)
1. **[SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md)** ← **Read this first!**
   - Complete step-by-step setup guide
   - Local development & testing procedures
   - Production server deployment instructions
   - Troubleshooting guide
   - 4 phases: Local Setup → Build → Functional Tests → Production

2. **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)**
   - Essential commands (Docker, API, file management)
   - API endpoint documentation with examples
   - Performance tuning parameters
   - Common troubleshooting commands
   - Knowledge base management procedures

3. **[README.md](./README.md)**
   - High-level project overview
   - Technology stack
   - Architecture explanation
   - Basic usage instructions

### Application Code
```
app/
├── main.py          # FastAPI application with RAG endpoints
└── Dockerfile       # Containerization specification

scripts/
├── ingest_data.py   # Data ingestion & embedding pipeline
├── backup.sh        # Linux/Mac backup script
└── backup.bat       # Windows backup script

data/
├── kb/              # Knowledge base (plain text files)
├── chroma/          # Vector database (auto-created)
└── processed_chunks.json  # Processed KB chunks (auto-created)
```

### Configuration Files
```
docker-compose.yml   # Docker orchestration (app + Chroma)
requirements.txt     # Python dependencies (pinned versions)
.env                 # Environment variables (local config)
.gitignore          # Git ignore patterns
validate_deployment.py  # Automated validation script
```

---

## 🎯 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client / SalesIQ                         │
│              (sends user messages via webhook)              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    HTTP POST /chat
                           │
┌──────────────────────────▼──────────────────────────────────┐
│          FastAPI Application (Port 8000)                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. Accept user query                                │   │
│  │ 2. Generate query embedding (sentence-transformers)│   │
│  │ 3. Retrieve context from vector DB                 │   │
│  │ 4. Build RAG prompt with context                   │   │
│  │ 5. Send to LLM (Ollama)                            │   │
│  │ 6. Return answer + confidence + context            │   │
│  └──────┬──────────────────────────┬──────────────────┘   │
└─────────┼──────────────────────────┼────────────────────────┘
          │                          │
    ┌─────▼────────┐         ┌──────▼──────────┐
    │   Ollama     │         │  Chroma Vector  │
    │   (Mistral)  │         │      DB         │
    │ Port: 11434  │         │  Port: 8001     │
    │ LLM Model    │         │ Stores: KB      │
    │ Generation   │         │ Embeddings      │
    └──────────────┘         └─────────────────┘
```

### Key Components

| Component | Role | Technology | Port |
|-----------|------|-----------|------|
| **FastAPI App** | API server, RAG orchestration | FastAPI + uvicorn | 8000 |
| **Chroma DB** | Vector database for KB | Chroma (Docker) | 8001 |
| **Ollama** | LLM for text generation | Ollama (mistral model) | 11434 |
| **Embeddings** | Converts text to vectors | sentence-transformers | (local) |

### Data Flow

```
User Query
    ↓
FastAPI /chat endpoint
    ↓
Generate embedding (sentence-transformers)
    ↓
Query Chroma for similar KB chunks
    ↓
Retrieve top-5 matching results
    ↓
Build RAG prompt: [Context] + [Query]
    ↓
Send to Ollama (mistral)
    ↓
LLM generates answer
    ↓
Return: {answer, context, confidence, latency}
```

---

## 🚀 Getting Started (Three Paths)

### Path 1: Quick Local Test (Right Now)
**Time:** 5-10 minutes | **Goal:** Verify system works

1. Start Docker Desktop (Windows Start Menu → Docker)
2. Open PowerShell, navigate to project
3. Run: `docker-compose up --build -d`
4. Wait 30 seconds
5. Run: `curl http://localhost:8000/health`
6. Expected: `{"status":"healthy"}`
7. Run: `docker logs -f acebuddy-api` to see real-time logs

**Next:** Read [SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md) Phase 1 for detailed validation.

---

### Path 2: Complete Local Setup & Testing (30 Minutes)
**Time:** 30 minutes | **Goal:** Full validation before production

Follow **[SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md):**
- Phase 1: Local Setup (all 9 steps)
- Phase 2: Production Preparation
- Phase 3: Run automated validation script

```powershell
# Run validation script (automates all checks)
python validate_deployment.py
```

**Next:** Once all checks pass, proceed to production deployment.

---

### Path 3: Production Server Migration (Depends on Path 2)
**Time:** 2-4 hours | **Goal:** Deploy to Windows Server 2022

1. Complete Path 2 (local testing)
2. Create backup: `.\scripts\backup.bat`
3. Transfer project to production server
4. Follow **[SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md) Phase 3**
   - Install Docker Desktop on server
   - Install Ollama on server
   - Pull mistral model
   - Start docker-compose
   - Validate with health check

---

## 📊 Knowledge Base Management

### Add Support Articles

**Method 1: Add text files to `data/kb/`**
```
data/kb/
├── acebuddy_support_guide.txt (existing)
├── password_reset.txt (new)
├── quickbooks_integration.txt (new)
└── rdp_connection.txt (new)
```

Then re-ingest:
```powershell
docker exec acebuddy-api python scripts/ingest_data.py
```

**Method 2: Use API endpoint**
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "title": "New Article",
        "content": "Full content here...",
        "category": "troubleshooting"
      }
    ]
  }'
```

### Current KB Content
- Password Reset (5 topics)
- RDP Connection (3 topics)
- QuickBooks Integration (4 topics)
- **Total:** ~15 sample articles, ~3,000 tokens

**Recommended:** Add real support articles from existing SalesIQ transcripts.

---

## 🔧 Configuration Reference

### Environment Variables (.env)

```env
# Chroma Vector Database
CHROMA_HOST=chroma                    # Docker service name (or IP)
CHROMA_PORT=8001                      # Database port

# Ollama LLM Service
OLLAMA_HOST=http://localhost:11434    # Ollama API endpoint
OLLAMA_MODEL=mistral                  # Model name (mistral, llama2, neural-chat)

# FastAPI Server
FASTAPI_HOST=0.0.0.0                 # Bind to all interfaces
FASTAPI_PORT=8000                    # API port (8000, 8080, 5000, etc.)

# RAG Configuration
TOP_K_RESULTS=5                       # Number of KB chunks to retrieve (2-10)
MIN_CONFIDENCE=0.5                    # Confidence threshold (0-1)
TEMPERATURE=0.7                       # LLM creativity (0=deterministic, 1=random)
```

### Production .env Changes

For **Windows Server 2022** deployment, typically only one change:

```env
# If Ollama on separate machine:
OLLAMA_HOST=http://<OLLAMA_SERVER_IP>:11434

# If Ollama on same machine:
OLLAMA_HOST=http://localhost:11434  # (no change needed)

# If using cloud VM:
OLLAMA_HOST=http://<CLOUD_VM_IP>:11434
```

---

## 📈 Performance & Capacity

### Monthly Chat Volume Estimates
Based on analysis of your existing data:

| Month | Expected Chats | Peak Days | Notes |
|-------|----------------|-----------|-------|
| January | 449 | Tax season start |  |
| August | 798 | Peak season | Busy |
| September | 759 | Post-August | Busy |
| October | 826 | Peak tax | **Highest** |
| May | 367 | Low | Slowest |
| **Annual Total** | **~6,089** | | |

### Cost Analysis
| Item | Cost | Notes |
|------|------|-------|
| **LLM Generation** | $37–$183/year | Depends on answer length |
| **Vector DB** (self-hosted) | $0 | On-premise server |
| **Vector DB** (cloud) | $5–$50/month | Managed Pinecone/Weaviate |
| **Server** (self-hosted) | $0 | Existing Server 2022 |
| **Server** (cloud VM) | $20–$100/month | AWS/Azure/GCP t2.medium |

### Scalability
- **Current setup:** ~10K chats/month (easily handles your 6K/year)
- **Bottleneck:** LLM response generation (~2-5 sec per query)
- **Scale-up:** Add GPU or use faster model (neural-chat, mistral-7b-q5)

---

## ✅ Pre-Production Checklist

Before going live with Zoho SalesIQ integration:

- [ ] Local tests pass (health + chat endpoints)
- [ ] Docker containers running smoothly
- [ ] Knowledge base populated with real articles
- [ ] Backup script tested and working
- [ ] Production server ready (Docker + Ollama installed)
- [ ] .env updated for production environment
- [ ] Network connectivity verified (app ↔ Chroma ↔ Ollama)
- [ ] API latency acceptable (<5 seconds)
- [ ] Error logs reviewed and clean
- [ ] SalesIQ webhook endpoint configured
- [ ] Response quality validated (sample queries tested)
- [ ] Monitoring/logging configured
- [ ] Team trained on deployment/troubleshooting
- [ ] Disaster recovery (backup/restore) tested

---

## 🛠️ Essential Commands

### Docker Operations
```powershell
# Start everything
docker-compose up --build -d

# Stop everything
docker-compose down

# View status
docker ps

# View logs
docker logs -f acebuddy-api
docker logs -f chroma

# Rebuild after code changes
docker-compose up --build -d

# Clean up (removes containers, keeps data)
docker system prune -a
```

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Chat query
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"How do I reset my password?","user_id":"test"}'

# List endpoints
curl http://localhost:8000/docs  # Interactive API docs (Swagger UI)
curl http://localhost:8000/openapi.json  # OpenAPI specification
```

### Data Management
```powershell
# Create backup
.\scripts\backup.bat

# Re-ingest knowledge base
docker exec acebuddy-api python scripts/ingest_data.py

# Check KB data
cat data\processed_chunks.json | head -100
```

---

## 🐛 Troubleshooting

### "Docker is not running"
```powershell
# Start Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Or manually: Windows Start Menu → Search "Docker" → Click Docker Desktop
```

### "Ollama not responding"
```powershell
# Check if Ollama is running
ollama serve

# Check model availability
ollama list

# Test endpoint
curl http://localhost:11434/api/tags
```

### "Chat endpoint timeout"
- Normal if response >10 seconds (first request loads model)
- Check server resources (CPU, RAM, disk)
- Reduce `TOP_K_RESULTS` in .env (3-4 instead of 5)
- Or upgrade to faster model

### "Out of disk space"
```powershell
# Check Docker disk usage
docker system df

# Clean up old images
docker system prune -a --volumes

# Or increase Docker disk allocation (Settings → Resources → 100GB)
```

**For detailed troubleshooting:** See [SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md) → Troubleshooting Guide

---

## 📚 Documentation Guide

| Document | Purpose | Read When |
|----------|---------|-----------|
| **[SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md)** | Complete setup & deployment | Setting up for the first time |
| **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** | Commands & configurations | Day-to-day operations |
| **[README.md](./README.md)** | Project overview | Understanding the architecture |
| **[validate_deployment.py](./validate_deployment.py)** | Automated validation | Before production migration |
| **[this file - DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** | High-level overview | Quick orientation |

---

## 🎯 Next Steps

### Immediate (Next 2 Hours)
1. [ ] Read [SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md) Phase 1
2. [ ] Run `docker-compose up --build -d`
3. [ ] Test endpoints with curl
4. [ ] Review logs

### Short-term (Next 1 Week)
1. [ ] Complete full local validation (Phase 1-2 of checklist)
2. [ ] Run `python validate_deployment.py`
3. [ ] Add real KB articles from your SalesIQ tickets
4. [ ] Test with actual support queries

### Medium-term (Before Tax Season)
1. [ ] Deploy to Windows Server 2022
2. [ ] Integrate Zoho SalesIQ webhook
3. [ ] Run pilot with team (internal testing)
4. [ ] Monitor response quality & latency
5. [ ] Optimize based on real usage

### Long-term (Post-MVP)
1. [ ] Monitor chat success rate & customer satisfaction
2. [ ] Add feedback mechanism to improve answers
3. [ ] Consider fine-tuning model on your specific support domain
4. [ ] Scale to cloud if needed
5. [ ] Expand to other Zoho products

---

## 💡 Key Features

✅ **RAG (Retrieval-Augmented Generation)**
- Searches knowledge base for relevant articles
- Grounds responses in actual support documentation
- Improves accuracy vs. pure LLM

✅ **Self-Hosted & Portable**
- Runs entirely on your server
- No vendor lock-in or recurring API costs
- Easy to migrate between servers

✅ **Docker-Based Deployment**
- Consistent local & production environment
- Single command startup: `docker-compose up`
- Backup & restore in minutes

✅ **Configurable LLM**
- Default: Mistral 7B (fast, open-source)
- Optional: Swap for Llama2, Neural-Chat, etc.
- Adjustable parameters (temperature, top-k)

✅ **Production-Ready**
- Health checks, logging, error handling
- Graceful shutdown, auto-restart
- Backup & disaster recovery scripts

---

## 📞 Support & Getting Help

1. **Check documentation first**
   - [SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md) Troubleshooting section
   - [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) Common commands

2. **Review logs**
   ```powershell
   docker logs acebuddy-api
   docker logs chroma
   ```

3. **Test components individually**
   ```bash
   # Test Docker
   docker ps
   
   # Test Ollama
   ollama list
   curl http://localhost:11434/api/tags
   
   # Test API
   curl http://localhost:8000/health
   ```

4. **Check port availability**
   ```powershell
   netstat -ano | findstr "8000\|8001\|11434"
   ```

---

## 📄 License & Attribution

This project uses:
- **FastAPI** (MIT License)
- **Chroma** (Apache 2.0)
- **Ollama** (MIT License)
- **sentence-transformers** (Apache 2.0)
- **Mistral AI** model (Mistral License)

---

## 🎓 Learning Resources

- **FastAPI:** https://fastapi.tiangolo.com/
- **Docker:** https://docs.docker.com/
- **Ollama:** https://ollama.ai/
- **Chroma:** https://www.trychroma.com/
- **RAG Patterns:** https://github.com/run-llm/

---

## ✨ Success Indicators

You'll know the system is working when:

1. ✅ Health endpoint returns `{"status":"healthy"}`
2. ✅ Chat endpoint returns relevant answers to support questions
3. ✅ API responds within 2-5 seconds
4. ✅ No error messages in logs
5. ✅ Docker containers show "healthy" status
6. ✅ Knowledge base is populated with real articles
7. ✅ Backup/restore works smoothly
8. ✅ Production server deployment succeeds

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| **Total Lines of Code** | ~800 |
| **Dependencies** | 15+ (pinned versions) |
| **Container Images** | 2 (FastAPI app + Chroma) |
| **API Endpoints** | 5 (health, chat, ingest, root, docs) |
| **Knowledge Base Capacity** | ~50K tokens (scalable) |
| **Monthly Cost** | $37–$233 (depends on volume & choices) |
| **MVP Timeline** | 2-3 hours local setup + testing |
| **Production Migration** | 2-4 hours (copy + docker-compose + .env update) |

---

## 🎉 You're Ready!

Everything is set up and ready to go. Start with:

1. **Quick Test (5 min):** `docker-compose up --build -d`
2. **Full Setup (30 min):** Follow [SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md) Phase 1
3. **Production (2-4 hrs):** Follow Phase 3 when ready

**Questions?** Check the documentation links above, or review the logs with `docker logs -f acebuddy-api`.

Good luck! 🚀

---

**Last Updated:** 2024  
**Status:** Production-Ready  
**Next Review:** After first 100 production queries
