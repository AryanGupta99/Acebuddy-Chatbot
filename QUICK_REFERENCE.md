# AceBuddy RAG - Quick Reference Guide

## Essential Commands

### Local Development (Windows PowerShell)

```powershell
# Navigate to project
cd "c:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"

# Start all services
docker-compose up --build -d

# Stop all services
docker-compose down

# View running containers
docker ps

# View logs (real-time)
docker logs -f acebuddy-api      # API logs
docker logs -f chroma             # Chroma DB logs

# View logs (last N lines)
docker logs --tail=50 acebuddy-api

# Restart a service
docker restart acebuddy-api
docker restart chroma

# Execute command inside container
docker exec acebuddy-api bash
docker exec chroma bash

# Rebuild containers (after code changes)
docker-compose up --build -d

# Create backup
.\scripts\backup.bat

# Clean up unused Docker resources
docker system prune -a
```

---

## API Endpoints (Quick Reference)

### Base URL
- **Local:** `http://localhost:8000`
- **Production:** `http://<SERVER_IP>:8000`

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "chroma_connected": true,
  "ollama_endpoint": "http://localhost:11434",
  "model_name": "mistral",
  "timestamp": "2024-01-01T12:34:56.789123"
}
```

---

### 2. Chat / RAG Query
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I reset my password?",
    "user_id": "user_123",
    "session_id": "session_456"
  }'
```

**Response:**
```json
{
  "answer": "To reset your password, visit the settings page and click 'Reset Password'...",
  "context_used": [
    {
      "text": "Password Reset: Click your username in the top-right corner...",
      "confidence": 0.95,
      "source": "kb/acebuddy_support_guide.txt"
    }
  ],
  "model_used": "mistral",
  "latency_ms": 2345,
  "timestamp": "2024-01-01T12:34:56.789123"
}
```

---

### 3. Ingest New Documents
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "title": "New Support Article",
        "content": "This is the content of the new support article...",
        "category": "troubleshooting"
      }
    ]
  }'
```

**Response:**
```json
{
  "status": "success",
  "documents_ingested": 1,
  "chunks_created": 3,
  "embedding_model": "all-MiniLM-L6-v2",
  "timestamp": "2024-01-01T12:34:56.789123"
}
```

---

### 4. Root Endpoint (Metadata)
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "service": "AceBuddy RAG Chatbot",
  "version": "1.0.0",
  "environment": "local",
  "description": "RAG-based conversational chatbot for support automation"
}
```

---

## .env Configuration Reference

```env
# Chroma Vector Database
CHROMA_HOST=chroma                              # Hostname or IP
CHROMA_PORT=8001                               # Port number
CHROMA_PERSIST_DIR=/data/chroma               # Data persistence path

# Ollama LLM Service
OLLAMA_ENDPOINT=http://localhost:11434         # Ollama API endpoint
MODEL_NAME=mistral                             # Model to use (mistral, llama2, etc.)
TEMPERATURE=0.7                                # Creativity (0=deterministic, 1=random)
TOP_K=40                                       # Top-k sampling parameter
TOP_P=0.9                                      # Nucleus sampling parameter

# FastAPI Server
FASTAPI_HOST=0.0.0.0                          # Bind to all interfaces
FASTAPI_PORT=8000                             # API port
DEBUG=false                                    # Debug mode

# Retrieval Configuration
TOP_K_RESULTS=5                                # Number of KB chunks to retrieve
MIN_CONFIDENCE=0.5                             # Minimum confidence threshold
CHUNK_SIZE=500                                 # KB chunk size (characters)
CHUNK_OVERLAP=50                               # Chunk overlap for context

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2              # HuggingFace model name
```

---

## File Structure

```
AceBuddy-RAG/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── Dockerfile              # Docker image definition
│   └── __init__.py
├── data/
│   ├── kb/                      # Knowledge base files (plain text)
│   │   └── acebuddy_support_guide.txt
│   ├── chroma/                  # Vector database (auto-created)
│   └── processed_chunks.json    # Processed KB chunks (auto-created)
├── scripts/
│   ├── ingest_data.py          # Data ingestion script
│   ├── backup.sh               # Linux/Mac backup script
│   └── backup.bat              # Windows backup script
├── tests/
│   └── test_main.py            # Unit tests
├── docker-compose.yml          # Docker orchestration
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
├── .gitignore                  # Git ignore rules
├── README.md                   # Project documentation
├── SETUP_CHECKLIST.md          # Setup instructions (this guide)
└── PACKAGE_SUMMARY.txt         # Package manifest
```

---

## Common Troubleshooting Steps

### Containers won't start
```powershell
# Check for port conflicts
netstat -ano | findstr "8000\|8001"

# View detailed error
docker-compose logs

# Clean start
docker-compose down
docker system prune -a
docker-compose up --build
```

### Ollama not responding
```powershell
# Verify Ollama running
ollama serve

# Pull model if missing
ollama pull mistral

# Test endpoint
curl http://localhost:11434/api/tags
```

### Chroma connection issues
```powershell
# Check Chroma logs
docker logs chroma

# Verify persistence directory exists
dir data\chroma

# Restart Chroma service
docker restart chroma
```

### Slow responses
```powershell
# Check server resources
tasklist /v

# Monitor Docker
docker stats

# Reduce top_k in .env or code
TOP_K_RESULTS=3  # Instead of 5
```

---

## Performance Tuning

| Parameter | Default | Fast (Low Accuracy) | Balanced | Accurate (Slow) |
|-----------|---------|-------------------|----------|-----------------|
| TOP_K_RESULTS | 5 | 2 | 5 | 10 |
| TEMPERATURE | 0.7 | 0.3 | 0.7 | 0.9 |
| CHUNK_SIZE | 500 | 300 | 500 | 800 |
| MIN_CONFIDENCE | 0.5 | 0.7 | 0.5 | 0.3 |

**Fast Configuration:**
```env
TOP_K_RESULTS=2
TEMPERATURE=0.3
CHUNK_SIZE=300
MIN_CONFIDENCE=0.7
```

**Balanced Configuration (Default):**
```env
TOP_K_RESULTS=5
TEMPERATURE=0.7
CHUNK_SIZE=500
MIN_CONFIDENCE=0.5
```

**Accurate Configuration:**
```env
TOP_K_RESULTS=10
TEMPERATURE=0.9
CHUNK_SIZE=800
MIN_CONFIDENCE=0.3
```

---

## Knowledge Base Management

### Add New Support Articles

**Method 1: Via API**
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "title": "QuickBooks Setup",
        "content": "To connect QuickBooks: 1. Go to Settings... 2. Click Integration...",
        "category": "integration"
      }
    ]
  }'
```

**Method 2: Via File**
1. Add `.txt` file to `data/kb/` directory
2. Run ingestion script:
   ```powershell
   docker exec acebuddy-api python scripts/ingest_data.py
   ```

### View Ingested Data
```powershell
# Check processed chunks
cat data\processed_chunks.json

# Check Chroma collection stats
docker exec acebuddy-api python -c "
from chromadb.config import Settings
from chromadb import HttpClient
client = HttpClient(host='chroma', port=8001)
collection = client.get_collection(name='acebuddy_kb')
print(f'Total documents: {collection.count()}')
"
```

---

## Monitoring & Health Checks

### Regular Health Verification
```bash
# Full health check (every 5 minutes)
curl -s http://localhost:8000/health | jq .

# Simple status (every minute)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health

# Expected: 200 OK
```

### Log Monitoring
```powershell
# Watch for errors (real-time)
docker logs -f --since 1m acebuddy-api | findstr "ERROR\|CRITICAL\|EXCEPTION"

# Count recent requests
docker logs --since 1h acebuddy-api | findstr "POST /chat" | measure-object -Line

# Performance analysis
docker logs --since 1h acebuddy-api | findstr "latency_ms"
```

---

## Backup & Recovery

### Automatic Backup (Weekly)
```bash
# Windows Task Scheduler: Create scheduled task
# Action: Run C:\path\to\AceBuddy-RAG\scripts\backup.bat
# Schedule: Weekly on Sunday at 2:00 AM
```

### Manual Backup
```powershell
.\scripts\backup.bat
```

### Restore from Backup
```powershell
# 1. Stop services
docker-compose down

# 2. Backup current data
.\scripts\backup.bat

# 3. Restore old data
copy backups\acebuddy_backup_<TIMESTAMP>\* .

# 4. Restart
docker-compose up -d
```

---

## Production Deployment Checklist

Before moving to production server:

- [ ] All local tests passing (health + chat endpoints)
- [ ] Knowledge base populated with real support articles
- [ ] Backup script tested and backup created
- [ ] .env configuration reviewed and production values set
- [ ] Docker images built and stored (docker save)
- [ ] Network connectivity verified (app ↔ Chroma ↔ Ollama)
- [ ] Ollama model (mistral) available on target server
- [ ] Security: API exposed only to trusted networks
- [ ] Monitoring: Logging configured and tested
- [ ] Disaster recovery: Backup/restore procedure validated

---

## Support Contacts

**For Technical Issues:**
- Check SETUP_CHECKLIST.md troubleshooting section
- Review application logs: `docker logs acebuddy-api`
- Verify Docker and Ollama services running

**For Integration Help:**
- Review API documentation in app/main.py docstrings
- Test endpoints with provided curl examples
- Check SalesIQ webhook configuration

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-01 | Initial release - Local deployment ready |
| TBD | TBD | Production deployment validation |
| TBD | TBD | Zoho SalesIQ integration complete |

---

**Generated:** 2024
**Last Updated:** 2024
**Status:** Ready for Local Testing
