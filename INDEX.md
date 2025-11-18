# AceBuddy RAG Chatbot - Master Index & Navigation Guide

**Welcome!** 👋 This file helps you navigate all the documentation and get started quickly.

---

## 🎯 What Is This Project?

**AceBuddy RAG Chatbot** is a production-ready conversational AI system that:
- Answers support questions using your knowledge base (RAG - Retrieval-Augmented Generation)
- Runs locally on your Windows laptop using Docker
- Scales to production in a few hours
- Integrates with Zoho SalesIQ
- **Goal:** Automate 30-40% of support tickets before tax season

**Status:** ✅ Ready for local testing → ✅ Ready for production deployment

---

## 📚 Documentation Map

### For Quick Start (5-30 minutes)
| If you want to... | Read this | Time |
|---|---|---|
| Understand the big picture | **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** (this folder) | 5 min |
| Run the system immediately | **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** → Quick Start section | 5 min |
| Do a complete local test | **[SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md)** → Phase 1 | 30 min |

### For Production Deployment (2-4 hours)
| If you want to... | Read this | Time |
|---|---|---|
| Prepare for server migration | **[SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md)** → Phase 2 | 30 min |
| Deploy to RDP server | **[SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md)** → Phase 3 | 2-4 hrs |
| Validate system before going live | Run `python validate_deployment.py` | 10 min |
| Set up monitoring & backups | **[SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md)** → Monitoring section | 15 min |

### For Daily Operations (Ongoing)
| If you want to... | Read this | Time |
|---|---|---|
| Common Docker commands | **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** → Essential Commands | 2 min |
| API endpoints & examples | **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** → API Endpoints | 5 min |
| Add support articles to KB | **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** → Knowledge Base Management | 5 min |
| Troubleshoot issues | **[SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md)** → Troubleshooting | 10 min |
| Monitor system health | **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** → Monitoring | 5 min |

### For Understanding Architecture
| If you want to... | Read this | Time |
|---|---|---|
| Learn how it works | **[README.md](./README.md)** | 10 min |
| Understand data flow | **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** → System Architecture | 5 min |
| See performance specs | **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** → Performance & Capacity | 5 min |

---

## 🚀 Getting Started (Choose Your Path)

### Path 1: I Just Want to Test It (15 Minutes)
```
1. Make sure Docker Desktop is running
   → Windows Start Menu → search "Docker" → click Docker Desktop

2. Navigate to project folder:
   → cd "C:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"

3. Start the system:
   → docker-compose up --build -d

4. Wait 30 seconds, then test:
   → curl http://localhost:8000/health
   → curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"query":"How do I reset my password?","user_id":"test"}'

5. View logs:
   → docker logs -f acebuddy-api
```

**✅ Done!** If you see responses, it's working!

---

### Path 2: I Want Full Setup & Validation (45 Minutes)
```
1. Read: SETUP_CHECKLIST.md → Phase 1 (complete section)
   → Covers: Prerequisites, Docker setup, testing endpoints, logs

2. Run validation:
   → python validate_deployment.py
   → This automates all checks and generates a report

3. Review: QUICK_REFERENCE.md
   → Bookmark for daily operations

✅ Done! System validated and ready for production.
```

---

### Path 3: I Want to Deploy to Production Server (2-4 Hours)
```
1. Complete Path 2 first (local validation)

2. Read: SETUP_CHECKLIST.md → Phase 2
   → Prepare backup, update config, package project

3. Read: SETUP_CHECKLIST.md → Phase 3
   → Transfer to server, install Docker/Ollama, start containers

4. Test on production server:
   → Same tests as Phase 1, but from server IP

✅ Done! Live in production.
```

---

## 📁 File Structure & What Each File Does

```
AceBuddy-RAG/
│
├── 📄 DEPLOYMENT_GUIDE.md ← YOU ARE HERE
│   └─ High-level overview, architecture, setup paths
│
├── 📄 SETUP_CHECKLIST.md ← READ THIS NEXT
│   └─ Detailed step-by-step setup with troubleshooting
│
├── 📄 QUICK_REFERENCE.md
│   └─ Common commands, API docs, performance tuning
│
├── 📄 README.md
│   └─ Project description, technology stack
│
├── 📄 START_HERE.txt (in parent folder)
│   └─ Original project overview
│
├── 🐍 validate_deployment.py
│   └─ Automated validation script (checks all prerequisites)
│
├── app/
│   ├── main.py ← FastAPI application with RAG logic
│   └── Dockerfile ← Docker container specification
│
├── scripts/
│   ├── ingest_data.py ← Loads KB and creates embeddings
│   ├── backup.sh ← Linux/Mac backup script
│   └── backup.bat ← Windows backup script
│
├── data/
│   ├── kb/ ← Knowledge base files (add your support articles here)
│   ├── chroma/ ← Vector database (auto-created)
│   └── processed_chunks.json ← Processed KB chunks (auto-created)
│
├── docker-compose.yml ← Orchestrates app + Chroma
├── requirements.txt ← Python dependencies
├── .env ← Configuration (edit for production)
└── .gitignore
```

---

## ⚡ Quick Commands

```powershell
# Start everything
docker-compose up --build -d

# Stop everything
docker-compose down

# View status
docker ps

# View logs
docker logs -f acebuddy-api

# Test health
curl http://localhost:8000/health

# Run validation
python validate_deployment.py

# Create backup
.\scripts\backup.bat

# Add new KB articles
# 1. Add .txt files to data/kb/
# 2. Run: docker exec acebuddy-api python scripts/ingest_data.py
```

---

## 🎓 Understanding the System

### In 30 Seconds
You have a Docker-based chatbot that:
1. Takes user questions as input
2. Searches a knowledge base for relevant articles
3. Uses an AI model (Mistral) to generate helpful answers
4. Returns the answer + source material + confidence score

### Data Flow
```
User Question
    ↓
API (/chat endpoint)
    ↓
Search Knowledge Base (Chroma)
    ↓
Find Top 5 Matching Articles
    ↓
Build AI Prompt with Context
    ↓
Generate Answer (Mistral LLM)
    ↓
Return Answer + Confidence
```

### Key Technologies
- **FastAPI:** Web server that handles requests
- **Chroma:** Database that stores knowledge base articles as vectors
- **Ollama:** Runs AI model (Mistral) locally
- **sentence-transformers:** Converts text to vectors for searching
- **Docker:** Packages everything into portable containers

---

## ✅ Verification Checklist

**Before moving to production, verify:**

- [ ] Docker Desktop installed and running
- [ ] Ollama installed with mistral model
- [ ] Project folder exists with all files
- [ ] `docker-compose up --build -d` completes without errors
- [ ] Health endpoint returns `{"status":"healthy"}`
- [ ] Chat endpoint returns valid responses
- [ ] Logs show no error messages
- [ ] All 5 items in "Essential Commands" work

**If any fail:** See [SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md) Troubleshooting section.

---

## 🆘 Troubleshooting Quick Guide

| Problem | Solution | See Also |
|---------|----------|----------|
| "Docker not running" | Start Docker Desktop (Windows Start Menu) | SETUP_CHECKLIST.md § Step 1.2 |
| "Containers won't start" | `docker-compose logs` to see errors | SETUP_CHECKLIST.md § Troubleshooting |
| "Ollama not responding" | Run `ollama serve` in terminal | QUICK_REFERENCE.md § Troubleshooting |
| "API timeout" | Check server resources, reduce TOP_K_RESULTS | QUICK_REFERENCE.md § Performance Tuning |
| "Out of disk space" | Run `docker system prune -a --volumes` | SETUP_CHECKLIST.md § Troubleshooting |

**Still stuck?** Search [SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md) for your error message.

---

## 📞 Getting Help

1. **Check the docs:**
   - [SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md) - Most detailed
   - [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Daily operations
   - [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - This overview

2. **Run validation:**
   ```powershell
   python validate_deployment.py
   ```
   This catches 90% of common issues.

3. **Check logs:**
   ```powershell
   docker logs acebuddy-api
   docker logs chroma
   ```

4. **Test components individually:**
   ```powershell
   docker ps              # Docker running?
   ollama list           # Ollama working?
   netstat -ano | findstr "8000"  # Port available?
   ```

---

## 🎯 Common Tasks

### Add New Support Articles
1. Create `.txt` file in `data/kb/`
2. Write article content
3. Run: `docker exec acebuddy-api python scripts/ingest_data.py`
4. Done! New articles now searchable

### Test the API
```bash
# Health check
curl http://localhost:8000/health

# Ask a question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"What is your support hours?","user_id":"test_user"}'

# See all endpoints
curl http://localhost:8000/docs  # Opens in browser at localhost:8000/docs
```

### Create Backup Before Migration
```powershell
.\scripts\backup.bat
# Creates: backups/acebuddy_backup_YYYYMMDD_HHMM/
# Contains: KB, embeddings, app code, config
```

### Restart Services
```powershell
docker-compose down
docker-compose up -d
```

### View Real-Time Logs
```powershell
docker logs -f acebuddy-api  # Live logs from API
docker logs -f chroma         # Live logs from database
# Press Ctrl+C to stop
```

---

## 📊 System Requirements

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **Laptop** | Windows 10/11 or Server 2022 | 64-bit |
| **CPU** | 2+ cores | 4+ cores recommended |
| **RAM** | 16GB total | 8GB+ free while running |
| **Disk** | 50GB free | For Docker + model + KB |
| **Docker Desktop** | Required | https://docker.com/products/docker-desktop |
| **Ollama** | Required | https://ollama.ai/ |

---

## 🗺️ Documentation Reading Order

### For First-Time Setup
1. **This file** (DEPLOYMENT_GUIDE.md) - 5 min overview
2. **[SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md) Phase 1** - Detailed setup
3. **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Bookmark for later

### For Production Deployment
1. **[SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md) Phase 2-3** - Detailed steps
2. **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - API & monitoring

### For Architecture Understanding
1. **[README.md](./README.md)** - Project overview
2. **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) § System Architecture** - Data flow
3. **app/main.py** - Read actual code (well-commented)

---

## ✨ Success Indicators

You'll know everything is working when you see:

✅ `docker ps` shows both containers "healthy"  
✅ `curl http://localhost:8000/health` returns `{"status":"healthy"}`  
✅ Chat endpoint returns actual answers  
✅ No ERROR messages in `docker logs acebuddy-api`  
✅ Responses arrive within 5 seconds  

---

## 🚦 Next Steps (Pick One)

| Next Step | When | How Long |
|-----------|------|----------|
| **Quick test** | "I just want to see if it works" | 5 min → Run Quick Start above |
| **Full setup** | "I want to validate everything" | 45 min → Follow SETUP_CHECKLIST.md Phase 1 |
| **Production** | "I'm ready to deploy" | 2-4 hrs → Complete Phase 1, then Phase 3 |
| **Learn more** | "I want to understand the code" | 30 min → Read README.md + app/main.py |

---

## 📞 Support Resources

**In This Repository:**
- SETUP_CHECKLIST.md (most detailed guide)
- QUICK_REFERENCE.md (daily operations)
- README.md (architecture & overview)
- validate_deployment.py (automated checks)

**Online Resources:**
- FastAPI: https://fastapi.tiangolo.com/
- Docker: https://docs.docker.com/
- Ollama: https://ollama.ai/
- Chroma: https://docs.trychroma.com/

**Your Team:**
- Check Slack/Teams history for similar issues
- Ask team for production server details

---

## 🎉 You're Ready!

Everything is set up. Pick your next step from the "Quick Commands" or "Next Steps" sections above.

**First-time setup?** → Read SETUP_CHECKLIST.md Phase 1  
**Ready for production?** → Read SETUP_CHECKLIST.md Phase 3  
**Need a command?** → Check QUICK_REFERENCE.md  

Good luck! 🚀

---

## Document Legend

| Symbol | Meaning |
|--------|---------|
| 📄 | Documentation file |
| 🐍 | Python script |
| 📁 | Folder/directory |
| ✅ | Complete & ready |
| ⚠️ | Warning/caution |
| 🆘 | Help/troubleshooting |
| 🚀 | Get started |
| 💡 | Pro tip |

---

**Last Updated:** 2024  
**Version:** 1.0.0  
**Status:** Production-Ready ✅

---

## Quick Links
- [📄 SETUP_CHECKLIST.md](./SETUP_CHECKLIST.md) - Complete setup guide
- [📄 QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - Daily operations
- [📄 DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Big picture overview
- [📄 README.md](./README.md) - Project details
- [🐍 validate_deployment.py](./validate_deployment.py) - Run validation

