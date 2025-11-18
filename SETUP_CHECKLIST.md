# AceBuddy RAG Local & Production Setup Checklist

## Phase 1: Local Setup (Windows Laptop)

### Step 1.1: Verify Prerequisites
- [ ] Docker Desktop installed and running on Windows
- [ ] Ollama installed and `mistral` model available (`ollama list`)
- [ ] Python 3.12+ installed with pip
- [ ] Project folder structure exists at: `AceBuddy-RAG/`
- [ ] All files created (app/, data/, scripts/, docker-compose.yml, requirements.txt, .env)

**Verification Commands:**
```powershell
# Check Docker
docker --version
docker ps

# Check Ollama
ollama list

# Check Python
python --version
pip list | findstr "fastapi uvicorn chromadb"
```

---

### Step 1.2: Start Docker Desktop
- [ ] Open Windows Start Menu → Search "Docker Desktop"
- [ ] Click to launch Docker Desktop
- [ ] Wait for Docker daemon to initialize (watch system tray icon)
- [ ] Verify running: Open PowerShell and run `docker ps`
  - Expected: Shows "CONTAINER ID", "IMAGE", "STATUS" columns (even if no containers running yet)

---

### Step 1.3: Start Ollama Service
- [ ] Ensure Ollama is running locally
  - Option A (if installed): Ollama runs as Windows service or startup app
  - Option B (if manual): Open terminal and run `ollama serve`
- [ ] Verify Ollama endpoint is accessible: 
  ```powershell
  curl http://localhost:11434/api/tags
  ```
  Expected response: JSON list of available models including `mistral:latest`

---

### Step 1.4: Navigate to Project & Build Docker Containers
```powershell
cd "c:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"

# Start containers with build
docker-compose up --build -d

# Verify containers are running
docker ps
```

**Expected Output from `docker ps`:**
```
CONTAINER ID   IMAGE                    STATUS                   PORTS                    NAMES
<id>           acebuddy-rag:latest      Up <time> (healthy)      0.0.0.0:8000->8000/tcp  acebuddy-api
<id>           chromadb/chroma:latest   Up <time> (healthy)      0.0.0.0:8001->8001/tcp  chroma
```

- [ ] Both containers show "healthy" status (may take 30-60 seconds)
- [ ] If either shows "unhealthy" or "exited", check logs:
  ```powershell
  docker logs acebuddy-api
  docker logs chroma
  ```

---

### Step 1.5: Test Health Endpoint
```powershell
# Test API health
curl http://localhost:8000/health

# Expected response (JSON):
# {
#   "status": "healthy",
#   "chroma_connected": true,
#   "ollama_endpoint": "http://localhost:11434",
#   "model_name": "mistral",
#   "timestamp": "2024-..."
# }
```

- [ ] Received 200 status code
- [ ] `chroma_connected: true`
- [ ] `status: healthy`

---

### Step 1.6: Test Chat Endpoint (RAG Query)
```powershell
# Test RAG chat (example query)
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "query": "How do I reset my password?",
  "user_id": "test_user_001",
  "session_id": "test_session_001"
}
EOF

# Expected response (JSON):
# {
#   "answer": "To reset your password, follow these steps...",
#   "context_used": [
#     { "text": "Password Reset...", "confidence": 0.95 },
#     ...
#   ],
#   "model_used": "mistral",
#   "latency_ms": 2345,
#   "timestamp": "2024-..."
# }
```

- [ ] Received 200 status code
- [ ] `answer` field contains a meaningful response
- [ ] `context_used` array populated with retrieved knowledge base chunks
- [ ] Confidence scores present

---

### Step 1.7: (Optional) Test Data Ingestion Endpoint
```powershell
# Test custom data ingestion (uploads & processes new KB content)
curl -X POST http://localhost:8000/ingest `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "documents": [
    {
      "title": "QuickBooks Connection Error",
      "content": "If QuickBooks is not connecting to AceBuddy, try these steps: 1. Restart QuickBooks Desktop. 2. Clear AceBuddy cache...",
      "category": "troubleshooting"
    }
  ]
}
EOF

# Expected response:
# {
#   "status": "success",
#   "documents_ingested": 1,
#   "chunks_created": 3,
#   "embedding_model": "all-MiniLM-L6-v2",
#   "timestamp": "2024-..."
# }
```

- [ ] Received 200 status code
- [ ] `status: success`
- [ ] Document count reflects uploaded documents

---

### Step 1.8: View Container Logs
```powershell
# View app logs (last 50 lines, follow in real-time)
docker logs -f --tail=50 acebuddy-api

# View Chroma logs
docker logs -f --tail=50 chroma

# Stop following logs: Ctrl+C
```

- [ ] App logs show request/response activity
- [ ] No error messages or exceptions
- [ ] Logs show Ollama connection successful

---

### Step 1.9: Stop Containers (when done testing)
```powershell
# Graceful shutdown
docker-compose down

# Cleanup (removes containers, keeps volumes/data)
# Data persists in data/chroma/ and data/processed_chunks.json
```

- [ ] Both containers stopped
- [ ] Data preserved for next startup

---

## Phase 2: Production Preparation (Before Server Migration)

### Step 2.1: Backup Local Data
```powershell
# Run backup script
.\scripts\backup.bat

# Verify backup created
dir backups\
```

- [ ] Backup directory created with timestamp
- [ ] BACKUP_INFO.txt present
- [ ] KB, Chroma, app code directories present in backup

---

### Step 2.2: Update .env for Production Environment
**Current .env content (local):**
```
CHROMA_HOST=chroma
CHROMA_PORT=8001
OLLAMA_ENDPOINT=http://localhost:11434
MODEL_NAME=mistral
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
```

**For production on RDP Server, update to:**
```
# If Ollama running on same server as API:
CHROMA_HOST=chroma
CHROMA_PORT=8001
OLLAMA_ENDPOINT=http://localhost:11434
MODEL_NAME=mistral
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# OR if Ollama on separate machine:
CHROMA_HOST=chroma
CHROMA_PORT=8001
OLLAMA_ENDPOINT=http://<OLLAMA_SERVER_IP>:11434
MODEL_NAME=mistral
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
```

- [ ] Updated .env file saved
- [ ] Configuration matches target server network setup

---

### Step 2.3: Prepare Migration Package
```powershell
# Compress entire project for transfer
Compress-Archive -Path "c:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG" `
  -DestinationPath "c:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG-MIGRATION-$(Get-Date -Format 'yyyyMMdd_HHmm').zip" `
  -Force

# Verify zip file created
ls "AceBuddy-RAG-MIGRATION*.zip" | head -1
```

- [ ] Zip file created
- [ ] Size ~500MB-1GB (includes Chroma index)

---

## Phase 3: Production Server Setup (RDP VM / Windows Server 2022)

### Step 3.1: Transfer Project to Server
**Option A: Via Shared Drive**
```powershell
# On Server, map shared drive to local machine
net use z: "\\<LOCAL_MACHINE_IP>\<SHARE_PATH>"

# Copy project
copy z:\AceBuddy-RAG-MIGRATION*.zip C:\apps\
```

**Option B: Via RDP File Transfer**
- Copy zip file via RDP clipboard or file sharing
- Extract to `C:\apps\AceBuddy-RAG\`

**Option C: Via SCP (if SSH available)**
```powershell
scp -r "c:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG" admin@<SERVER_IP>:C:/apps/
```

- [ ] Project folder exists on server at: `C:\apps\AceBuddy-RAG\`
- [ ] All subdirectories present (app/, data/, scripts/)

---

### Step 3.2: Install Docker Desktop on Server
- [ ] Download Docker Desktop from docker.com
- [ ] Install on Windows Server 2022
- [ ] Enable WSL2 backend (required for Windows Server 2022)
- [ ] Restart server
- [ ] Verify: `docker --version` and `docker ps`

---

### Step 3.3: Install Ollama on Server
- [ ] Download Ollama from ollama.ai
- [ ] Install on server
- [ ] Pull mistral model: `ollama pull mistral`
  - First run: ~4.4GB download, may take 5-10 minutes
  - Subsequent runs: instant (cached)
- [ ] Verify: `ollama list` shows `mistral:latest`

---

### Step 3.4: Start Docker Containers on Server
```powershell
cd C:\apps\AceBuddy-RAG

# Verify .env is updated for server environment
cat .env

# Start containers
docker-compose up --build -d

# Verify running
docker ps
```

- [ ] Both `acebuddy-api` and `chroma` containers running
- [ ] Both show "healthy" status
- [ ] Port 8000 listening (API)
- [ ] Port 8001 listening (Chroma)

---

### Step 3.5: Verify Production Stack
```powershell
# Test health
curl http://localhost:8000/health

# Test chat
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d @- << 'EOF'
{
  "query": "How do I reset my password?",
  "user_id": "prod_test_001"
}
EOF
```

- [ ] Health endpoint returns `healthy`
- [ ] Chat endpoint returns valid response
- [ ] No error messages in logs: `docker logs acebuddy-api`

---

### Step 3.6: Configure Service Persistence (Optional)
To auto-start containers on server reboot:

```powershell
# Option A: Docker service (native)
# Containers with "restart: unless-stopped" in docker-compose.yml 
# will auto-restart on Docker daemon restart

# Option B: Windows Task Scheduler
# Create scheduled task to run "docker-compose up -d" on startup

# Option C: Windows Service (advanced)
# Use NSSM (Non-Sucking Service Manager) to wrap docker-compose as service
```

- [ ] Chosen persistence option configured
- [ ] Test by restarting server and verifying containers restart

---

## Phase 4: Integration with Zoho SalesIQ

### Step 4.1: Prepare Webhook Integration
Currently, the `/chat` endpoint accepts POST requests with format:
```json
{
  "query": "user message",
  "user_id": "user_identifier",
  "session_id": "session_identifier (optional)"
}
```

To integrate with Zoho SalesIQ:
- [ ] Obtain SalesIQ webhook documentation
- [ ] Map SalesIQ message format to our `/chat` endpoint format
- [ ] Modify `app/main.py` if needed to accept SalesIQ webhook format

**Example Zoho SalesIQ webhook (typical):**
```json
{
  "visitor_id": "...",
  "visitor_name": "...",
  "message": "...",
  "session_id": "...",
  "timestamp": "..."
}
```

Map this to:
```json
{
  "query": "<message>",
  "user_id": "<visitor_id>",
  "session_id": "<session_id>"
}
```

### Step 4.2: Configure SalesIQ Webhook URL
- [ ] In Zoho SalesIQ settings, add webhook:
  - URL: `http://<SERVER_IP_OR_DOMAIN>:8000/chat`
  - Method: POST
  - Headers: `Content-Type: application/json`
  - Trigger: Incoming visitor message

### Step 4.3: Test Integration
- [ ] Send test message via SalesIQ → Verify response received
- [ ] Check server logs: `docker logs -f acebuddy-api`
- [ ] Confirm message routed through RAG pipeline

---

## Troubleshooting Guide

### Issue: Docker containers fail to start
**Symptoms:** `docker ps` shows containers as "exited"

**Solution:**
```powershell
# View error logs
docker logs acebuddy-api
docker logs chroma

# Common causes:
# 1. Port 8000 or 8001 already in use
#    - Change ports in docker-compose.yml
# 2. Insufficient disk space in data/chroma
#    - Free up space or increase Docker disk allocation
# 3. .env file not found
#    - Ensure .env exists in project root
```

---

### Issue: Ollama connection failed
**Symptoms:** Health endpoint shows `ollama_endpoint unreachable`

**Solution:**
```powershell
# 1. Verify Ollama is running
ollama serve

# 2. Verify mistral model is loaded
ollama list

# 3. Test Ollama endpoint directly
curl http://localhost:11434/api/tags

# 4. If on separate machine, update .env:
OLLAMA_ENDPOINT=http://<OLLAMA_MACHINE_IP>:11434
```

---

### Issue: Chroma connection failed
**Symptoms:** Health endpoint shows `chroma_connected: false`

**Solution:**
```powershell
# 1. Verify Chroma container running
docker ps | findstr chroma

# 2. Check Chroma logs
docker logs chroma

# 3. Test Chroma directly (from inside app container)
docker exec acebuddy-api curl http://chroma:8001/api/v1/heartbeat

# 4. Restart Chroma
docker restart chroma
```

---

### Issue: High latency / slow responses
**Symptoms:** Chat endpoint takes >10 seconds to respond

**Solution:**
```powershell
# 1. Check server resources (CPU, RAM, disk I/O)
# 2. Review logs for slow operations
docker logs acebuddy-api | findstr "latency\|processing"

# 3. Optimize Chroma queries (reduce top_k in app/main.py)
# 4. Increase server resources or split services across machines
```

---

### Issue: Out of disk space
**Symptoms:** Chroma fails to create embeddings, Docker disk full

**Solution:**
```powershell
# 1. Check Docker disk usage
docker system df

# 2. Clean up unused images/containers
docker system prune -a --volumes

# 3. Increase Docker disk allocation:
#    - Settings → Resources → Disk image size → increase to 100GB+
```

---

## Monitoring & Maintenance (Post-Deployment)

### Daily Checks
```powershell
# Verify containers running
docker ps

# Check for errors in last hour
docker logs --since 1h acebuddy-api | findstr "ERROR\|CRITICAL"
```

### Weekly Maintenance
```powershell
# Backup data
.\scripts\backup.bat

# Update knowledge base (if needed)
docker exec acebuddy-api python scripts/ingest_data.py

# Restart containers
docker-compose down
docker-compose up -d
```

### Monthly Review
- [ ] Monitor API latency trends
- [ ] Review error logs for patterns
- [ ] Update knowledge base with new support articles
- [ ] Plan capacity increases if usage grows beyond estimates

---

## Rollback Procedure (If Issues in Production)

### Emergency Rollback to Previous Version
```powershell
# 1. Stop current containers
docker-compose down

# 2. Restore from backup
copy backups\acebuddy_backup_<TIMESTAMP>\* .

# 3. Update .env if needed
cat .env

# 4. Restart containers
docker-compose up -d

# 5. Verify health
curl http://localhost:8000/health
```

---

## Success Criteria

After completing all phases, you should have:

✓ **Local Testing Environment**
- [ ] Docker containers running locally
- [ ] Health endpoint returning healthy status
- [ ] Chat endpoint returning RAG responses
- [ ] Ollama and Chroma integrated
- [ ] No Docker or environment errors

✓ **Production-Ready Stack**
- [ ] Project containerized and portable
- [ ] Backup/restore procedures tested
- [ ] Configuration managed via .env
- [ ] Migration checklist completed
- [ ] Security considerations addressed

✓ **Integration Ready**
- [ ] API accepts expected message format
- [ ] Webhook integration tested with SalesIQ
- [ ] Response quality validated
- [ ] Latency within acceptable bounds (<5 sec)

✓ **Operational Ready**
- [ ] Monitoring procedures defined
- [ ] Backup schedule established
- [ ] Troubleshooting guide reviewed
- [ ] Team trained on deployment/maintenance
- [ ] Runbook prepared

---

## Contact & Support

For issues or questions:
1. Check "Troubleshooting Guide" above
2. Review container logs: `docker logs <container_name>`
3. Verify .env configuration
4. Check Ollama and Docker Desktop are running
5. Test endpoints manually with curl

---

**Last Updated:** 2024
**Status:** Ready for deployment
