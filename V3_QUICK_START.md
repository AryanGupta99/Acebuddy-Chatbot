# 🚀 AceBuddy RAG v3.0 - Quick Start Guide

## Get Started in 5 Minutes

### 1. Start Services
```powershell
cd "c:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"
docker-compose up -d
```

### 2. Check Health (Wait 5 seconds for startup)
```powershell
timeout /t 5
curl http://localhost:8000/health | ConvertFrom-Json
```

**Expected Output** (all services should be `true`):
```json
{
  "status": "healthy",
  "services": {
    "embedding_model": true,
    "chroma_client": true,
    "collection": true,
    "conversation_manager": true,
    "query_enhancer": true,
    "response_validator": true
  },
  "version": "2.0.0"
}
```

### 3. Ingest Knowledge Base
```powershell
curl -Method POST http://localhost:8000/ingest
```

### 4. Test Chat (Simple)
```powershell
$body = @{
    query = "How do I reset my password?"
    user_id = "test_user"
} | ConvertTo-Json

curl -Method POST -Uri http://localhost:8000/chat `
     -Body $body -ContentType "application/json" | ConvertFrom-Json
```

---

## 🎯 v3.0 New Features

### Feature 1: Conversation History

**First Message** (creates session):
```powershell
$body = @{
    query = "How do I reset my password?"
    user_id = "alice"
} | ConvertTo-Json

$response = curl -Method POST -Uri http://localhost:8000/chat `
     -Body $body -ContentType "application/json" | ConvertFrom-Json

$sessionId = $response.session_id
Write-Host "Session ID: $sessionId"
```

**Follow-up Message** (uses history):
```powershell
$body = @{
    query = "How long does it take?"
    user_id = "alice"
    session_id = $sessionId
    use_history = $true
} | ConvertTo-Json

curl -Method POST -Uri http://localhost:8000/chat `
     -Body $body -ContentType "application/json" | ConvertFrom-Json
```

**Get Conversation History**:
```powershell
curl http://localhost:8000/conversation/$sessionId | ConvertFrom-Json
```

---

### Feature 2: Query Enhancement

**With Enhancement** (synonyms + rewrites):
```powershell
$body = @{
    query = "rdp problems"  # Will expand to "remote desktop", "RDP connection", etc.
    user_id = "bob"
    enhance_query = $true
} | ConvertTo-Json

curl -Method POST -Uri http://localhost:8000/chat `
     -Body $body -ContentType "application/json" | ConvertFrom-Json
```

**Without Enhancement** (exact query only):
```powershell
$body = @{
    query = "rdp problems"
    user_id = "bob"
    enhance_query = $false
} | ConvertTo-Json

curl -Method POST -Uri http://localhost:8000/chat `
     -Body $body -ContentType "application/json" | ConvertFrom-Json
```

---

### Feature 3: Response Quality Scores

Every response includes a quality score (0-1):

```powershell
$response = curl -Method POST -Uri http://localhost:8000/chat `
     -Body $body -ContentType "application/json" | ConvertFrom-Json

Write-Host "Quality Score: $($response.response_quality)"
Write-Host "Confidence: $($response.confidence)"
Write-Host "Intent: $($response.intent) ($($response.intent_confidence))"
Write-Host "Query Enhanced: $($response.query_enhanced)"
```

**Quality Score Ranges**:
- `0.8 - 1.0`: Excellent response with strong context
- `0.6 - 0.8`: Good response, some confidence
- `0.3 - 0.6`: Acceptable but may lack detail
- `0.0 - 0.3`: Low quality, likely missing context (includes disclaimer)

---

### Feature 4: Conversation Analytics

**Get Statistics**:
```powershell
curl http://localhost:8000/conversation/stats | ConvertFrom-Json
```

**Output**:
```json
{
  "total_sessions": 15,
  "total_users": 8,
  "total_messages": 60,
  "avg_messages_per_session": 4.0,
  "active_sessions": 3
}
```

---

## 📊 Response Structure (v3.0)

```json
{
  // V2.0 FIELDS (backward compatible)
  "answer": "To reset your password...",
  "intent": "password_reset",
  "intent_confidence": 0.67,
  "context": ["chunk1", "chunk2"],  // Simple list
  "context_with_metadata": [  // Rich metadata
    {
      "content": "chunk1",
      "source": "01_password_reset.md",
      "chunk_id": "01_password_reset.md_0",
      "rank": 1,
      "confidence": 0.92
    }
  ],
  "confidence": 0.85,  // Average context confidence
  
  // V3.0 NEW FIELDS
  "session_id": "abc123...",  // For follow-up questions
  "response_quality": 0.78,  // Quality score 0-1
  "query_enhanced": true  // Whether query was expanded
}
```

---

## 🧪 Testing v3.0

### Run Full Test Suite
```powershell
# Make sure API is running
docker-compose up -d

# Run tests
pytest tests/test_v3_features.py -v

# Run specific test
pytest tests/test_v3_features.py::TestConversationHistory::test_chat_creates_session -v
```

### Manual Test Scenarios

**Scenario 1: Multi-Turn Password Reset**
```powershell
# Turn 1
$body = @{query="How do I reset my password?"; user_id="test1"} | ConvertTo-Json
$r1 = curl -Method POST -Uri http://localhost:8000/chat -Body $body -ContentType "application/json" | ConvertFrom-Json
$session = $r1.session_id

# Turn 2 (follow-up)
$body = @{query="What if I forgot my email?"; user_id="test1"; session_id=$session} | ConvertTo-Json
$r2 = curl -Method POST -Uri http://localhost:8000/chat -Body $body -ContentType "application/json" | ConvertFrom-Json

# Check history
curl http://localhost:8000/conversation/$session | ConvertFrom-Json
```

**Scenario 2: Query Enhancement Comparison**
```powershell
# Without enhancement
$body1 = @{query="pwd reset"; user_id="test2"; enhance_query=$false} | ConvertTo-Json
$r1 = curl -Method POST -Uri http://localhost:8000/chat -Body $body1 -ContentType "application/json" | ConvertFrom-Json

# With enhancement
$body2 = @{query="pwd reset"; user_id="test2"; enhance_query=$true} | ConvertTo-Json
$r2 = curl -Method POST -Uri http://localhost:8000/chat -Body $body2 -ContentType "application/json" | ConvertFrom-Json

# Compare context counts
Write-Host "Without Enhancement: $($r1.context_with_metadata.Count) contexts"
Write-Host "With Enhancement: $($r2.context_with_metadata.Count) contexts"
```

---

## 🔍 Debugging

### Check Docker Logs
```powershell
# API logs
docker logs acebuddy-api

# Last 50 lines
docker logs acebuddy-api | Select-Object -Last 50

# Follow logs
docker logs -f acebuddy-api
```

### Check Module Loading
```powershell
# Verify scripts folder in container
docker exec acebuddy-api ls -la /scripts

# Should show:
# conversation_manager.py
# query_enhancement.py
# intent.py
# rag_ingestion.py
# data_preparation.py
```

### Common Issues

**Issue**: `conversation_manager: false` in health check
- **Solution**: Rebuild Docker with `docker-compose up --build -d`
- **Check**: `docker exec acebuddy-api ls /scripts/conversation_manager.py`

**Issue**: `session_id` is `null`
- **Cause**: Conversation manager not loaded
- **Solution**: Check Docker logs for import errors, rebuild container

**Issue**: Query not enhanced (`query_enhanced: false`)
- **Cause**: Query enhancer module not loaded
- **Solution**: Verify `/scripts/query_enhancement.py` in container

---

## 📚 API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Service health check |
| `/chat` | POST | Main chat endpoint (v3.0) |
| `/ingest` | POST | Ingest knowledge base |
| `/conversation/{session_id}` | GET | Get conversation history |
| `/conversation/stats` | GET | Get conversation statistics |

### Request Parameters

**`/chat` POST Body**:
```json
{
  "query": "string (required)",
  "user_id": "string (default: 'default')",
  "session_id": "string (optional, creates new if not provided)",
  "use_history": "boolean (default: true)",
  "enhance_query": "boolean (default: true)"
}
```

### Environment Variables

```bash
# API Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# LLM Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral

# Vector DB
VECTOR_DB_COLLECTION=acebuddy_kb
CHROMA_HOST=http://chroma:8001

# Embedding Mode
EMBEDDING_OFFLINE=false  # Set to 'true' for testing
```

---

## 🎓 Examples

### Example 1: IT Support Conversation
```powershell
# User asks about RDP issues
$body = @{query="I can't connect via RDP"; user_id="john"} | ConvertTo-Json
$r1 = curl -Method POST -Uri http://localhost:8000/chat -Body $body -ContentType "application/json" | ConvertFrom-Json
Write-Host "Bot: $($r1.answer)"
Write-Host "Intent: $($r1.intent), Quality: $($r1.response_quality)"

# Follow-up about firewall
$body = @{query="Could it be a firewall issue?"; user_id="john"; session_id=$r1.session_id} | ConvertTo-Json
$r2 = curl -Method POST -Uri http://localhost:8000/chat -Body $body -ContentType "application/json" | ConvertFrom-Json
Write-Host "Bot: $($r2.answer)"

# Get full conversation
curl http://localhost:8000/conversation/$($r1.session_id) | ConvertFrom-Json
```

### Example 2: Query Enhancement Demo
```powershell
# Test various abbreviations
$queries = @(
    "pwd reset",
    "rdp error",
    "disk full",
    "email not working"
)

foreach ($q in $queries) {
    $body = @{query=$q; user_id="demo"; enhance_query=$true} | ConvertTo-Json
    $r = curl -Method POST -Uri http://localhost:8000/chat -Body $body -ContentType "application/json" | ConvertFrom-Json
    Write-Host "`nQuery: $q"
    Write-Host "Enhanced: $($r.query_enhanced)"
    Write-Host "Intent: $($r.intent)"
    Write-Host "Contexts: $($r.context_with_metadata.Count)"
}
```

---

## 🚀 Production Deployment Checklist

- [ ] Ollama service running and accessible
- [ ] ChromaDB service running
- [ ] Knowledge base ingested (`/ingest` called successfully)
- [ ] Health check returns "healthy"
- [ ] All 6 services enabled
- [ ] Test multi-turn conversation
- [ ] Test query enhancement
- [ ] Test response quality scores
- [ ] Monitor conversation statistics
- [ ] Set up logging/monitoring
- [ ] Configure backups (ChromaDB data)

---

## 📖 Additional Documentation

- **Full Implementation Guide**: `V3_IMPLEMENTATION_SUMMARY.md`
- **v2.0 Features**: `FEATURES.md`, `IMPLEMENTATION_SUMMARY.md`
- **Architecture**: `ARCHITECTURE.md`
- **Deployment**: `DEPLOYMENT_GUIDE.md`
- **Test Suite**: `tests/test_v3_features.py`

---

## 💡 Tips & Best Practices

1. **Always use session_id for follow-ups**: Enables context-aware responses
2. **Enable query enhancement by default**: Improves retrieval quality
3. **Monitor response_quality scores**: Identify knowledge gaps
4. **Check conversation/stats periodically**: Track system usage
5. **Use conversation history for debugging**: See full user journey
6. **Set appropriate session timeouts**: Balance memory vs. user experience

---

## 🎉 You're Ready!

Your AceBuddy RAG v3.0 chatbot is now fully operational with:
- ✅ Multi-turn conversations
- ✅ Query enhancement
- ✅ Response quality validation
- ✅ Conversation analytics
- ✅ Full backward compatibility

**Start chatting and enjoy the enhanced conversational AI experience!** 🚀
