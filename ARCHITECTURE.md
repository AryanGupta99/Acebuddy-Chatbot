# AceBuddy RAG System - Architecture & Integration Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User / Support Team                       │
│                                                                  │
│   Web Browser / Chat Interface / API Client                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP Requests
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                        │
│                    (Port 8000 - acebuddy-api)                   │
│                                                                  │
│  Endpoints:                                                     │
│  ┌─ GET  /health      → Check system status                   │
│  ├─ POST /ingest      → Index KB files into Chroma            │
│  ├─ POST /chat        → Query with RAG retrieval              │
│  └─ POST /            → Health check                           │
│                                                                  │
│  Components:                                                    │
│  ├─ FastAPI Framework                                          │
│  ├─ DummyEmbedding (Dev) / SentenceTransformer (Prod)         │
│  ├─ Chroma Client Connection                                   │
│  └─ LLM Integration (Ollama or hosted model)                   │
└────────────┬────────────────────────────────────┬──────────────┘
             │                                    │
             │ ChromaDB Protocol                  │
             ▼                                    ▼
┌────────────────────────────────────┐  ┌─────────────────────────┐
│     ChromaDB Vector Database       │  │   Ollama (Optional)     │
│  (Port 8000 in container)          │  │  (Port 11434)          │
│  (Port 8001 host-mapped)           │  │                        │
│                                    │  │  LLM Generation:       │
│ Collections:                       │  │  ├─ mistral            │
│ ├─ acebuddy_kb                     │  │  ├─ llama2             │
│ │  ├─ Documents: 47 chunks         │  │  └─ phi                │
│ │  ├─ Embeddings: 47 vectors       │  │                        │
│ │  └─ Metadata: source, intent     │  │  Used for:             │
│ │                                  │  │  - Generating answers  │
│ │ Storage:                         │  │  - Re-ranking results  │
│ │ ├─ Named Volume: chroma_data     │  │  - Summarizing context │
│ │ └─ Persists across restarts      │  │                        │
│ │                                  │  │                        │
│ │ Data Inside:                     │  │                        │
│ │ ├─ 01_password_reset.md chunks   │  │                        │
│ │ ├─ 02_disk_storage_upgrade chunks│  │                        │
│ │ ├─ 03_rdp_connection_issues      │  │                        │
│ │ ├─ ... (6 more KB files)         │  │                        │
│ │ └─ Total: ~41 KB of content      │  │                        │
│ │                                  │  │                        │
│ └─ Available at:                   │  │                        │
│    http://localhost:8001 (host)    │  └─────────────────────────┘
│    http://chroma:8000 (container)  │
└────────────────────────────────────┘
             ▲
             │
             │ Mounts
             │
      ┌──────┴─────────┐
      │                │
      ▼                ▼
  Docker        File System
  Volume        (Optional)
  chroma_data
  
  ├─ Persisted across
  │  container restarts
  ├─ Backed up via
  │  scripts/backup_chroma.ps1
  └─ Restored via
     scripts/restore_chroma.ps1
```

---

## Data Flow: User Query to RAG Response

```
1. USER QUERY
   "I forgot my password and can't log in"
            │
            ▼
2. API RECEIVES REQUEST
   POST /chat
   {
     "query": "I forgot my password...",
     "user_id": "user123"
   }
            │
            ▼
3. EMBEDDINGS GENERATED
   Query text → DummyEmbedding (dev) / SentenceTransformer (prod)
   → Vector representation [0.25, 0.31, -0.15, ..., 0.42]
            │
            ▼
4. SEMANTIC SEARCH IN CHROMA
   Similar search across 47 indexed KB chunks:
   ├─ 01_password_reset.md (distance: 0.05) ✓ HIGH MATCH
   ├─ 04_user_addition.md (distance: 0.42)
   └─ 09_email_issues.md (distance: 0.58)
            │
            ▼
5. RETRIEVE TOP CONTEXT
   Top 3-5 most relevant chunks:
   [
     "To reset password: 1) Chatbot collects user details...",
     "Verify in CRM lookup. Send password reset request...",
     "Support team receives email with timestamp and ETA..."
   ]
            │
            ▼
6. PROMPT CONSTRUCTION
   System Prompt:
   "You are AceBuddy support chatbot. Answer using provided context."
   
   User Query:
   "I forgot my password and can't log in"
   
   Context:
   "To reset password: [KB chunks above]"
            │
            ▼
7. LLM GENERATION (Ollama or hosted)
   Input: [System prompt + context + query]
   Output: "I can help with password reset. Please provide..."
            │
            ▼
8. RESPONSE CONSTRUCTION
   {
     "answer": "I can help with password reset...",
     "context": [
       {
         "document": "To reset password: 1) Chatbot collects...",
         "distance": 0.05,
         "metadata": { "source": "01_password_reset.md" }
       }
     ],
     "confidence": 0.92,
     "user_id": "user123",
     "timestamp": "2025-11-11T14:32:00Z"
   }
            │
            ▼
9. USER RECEIVES RESPONSE
   Display answer + relevant KB snippets + confidence score
```

---

## KB Integration Points

### During Ingest Phase
```
POST /ingest Request
        │
        ▼
Load all .md files from data/kb/
├─ 01_password_reset.md
├─ 02_disk_storage_upgrade.md
├─ 03_rdp_connection_issues.md
├─ 04_user_addition_deletion.md
├─ 05_monitor_setup.md
├─ 06_printer_troubleshooting.md
├─ 07_server_performance.md
├─ 08_quickbooks_issues.md
└─ 09_email_issues.md
        │
        ▼
Parse and Chunk Content
(Split by sections, paragraphs, headings)
        │
        ▼
Generate Embeddings for Each Chunk
(DummyEmbedding or SentenceTransformer)
        │
        ▼
Store in Chroma Collection
├─ Document text
├─ Embedding vector
├─ Metadata (source KB file, intent)
└─ ID for retrieval
        │
        ▼
Response: "Ingested 47 chunks into collection acebuddy_kb"
```

### During Chat Phase
```
POST /chat Request
  └─ query: "I can't connect to RDP"
  └─ user_id: "user456"
        │
        ▼
Embed Query
Query → Embedding Model → Vector
        │
        ▼
Search Chroma Collection
Similar vectors → Top 5 chunks
        │
        ▼
Retrieve Matching KB Sections
1. "RDP connection problem... (distance: 0.12)"
2. "Remote Desktop troubleshooting... (distance: 0.18)"
3. "Network connectivity issues... (distance: 0.25)"
        │
        ▼
Construct RAG Prompt
[System instructions] + [Context from KB] + [User query]
        │
        ▼
Generate Response (LLM)
        │
        ▼
Return Structured Response
├─ Answer (AI-generated using context)
├─ Context (KB snippets that were relevant)
├─ Confidence (how well query matched KB)
└─ Metadata (source files, intent detected)
```

---

## Testing Integration

### Smoke Test Workflow
```
Start Docker Compose
    │
    ├─ acebuddy-api (FastAPI)
    └─ acebuddy-chroma (Chroma DB)
    │
    ▼
Check /health Endpoint
    │
    └─ Should return: "status": "healthy"
    │
    ▼
POST /ingest
    │
    └─ Indexes all 9 KB files (47 chunks total)
    │
    ▼
Run Sample Queries (10 queries)
    │
    ├─ Query 1: "I forgot my password"
    │   └─ Expected: Return KB from password_reset.md
    │
    ├─ Query 2: "My disk is full"
    │   └─ Expected: Return KB from disk_storage_upgrade.md
    │
    ├─ Query 3: "RDP not connecting"
    │   └─ Expected: Return KB from rdp_connection_issues.md
    │
    └─ ... (7 more queries)
    │
    ▼
Report Results
├─ Success Rate: X/10 queries successful
├─ Context Coverage: Y/10 queries returned relevant KB
├─ Response Time: Average Z seconds
└─ Final Status: PASSED / WARNING / FAILED
```

---

## File Organization

```
AceBuddy-RAG/
│
├─── Knowledge Base Content
│    ├─ data/kb/
│    │  ├─ 01_password_reset.md
│    │  ├─ 02_disk_storage_upgrade.md
│    │  ├─ 03_rdp_connection_issues.md
│    │  ├─ 04_user_addition_deletion.md
│    │  ├─ 05_monitor_setup.md
│    │  ├─ 06_printer_troubleshooting.md
│    │  ├─ 07_server_performance.md
│    │  ├─ 08_quickbooks_issues.md
│    │  └─ 09_email_issues.md
│    │
│    └─ data/ (other data)
│       ├─ processed_chunks.json
│       └─ raw_transcripts_salesiq/ (optional)
│
├─── Application Code
│    ├─ app/
│    │  ├─ main.py (FastAPI + RAG logic)
│    │  └─ Dockerfile
│    │
│    └─ scripts/
│       ├─ ingest_data.py (ingestion pipeline)
│       ├─ fetch_salesiq_transcripts.py
│       ├─ backup_chroma.ps1
│       └─ restore_chroma.ps1
│
├─── Testing & Configuration
│    ├─ tests/
│    │  └─ sample_queries.json (47 test queries)
│    │
│    ├─ docker-compose.yml
│    ├─ test_chatbot_smoke.ps1
│    └─ .env
│
├─── Documentation
│    ├─ README.md
│    ├─ KB_SETUP_COMPLETE.md
│    ├─ KB_FILE_MANIFEST.md
│    ├─ ARCHITECTURE.md (this file)
│    └─ docs/
│       └─ production-migration.md (todo)
│
└─── Docker Volumes
     └─ chroma_data/
        └─ (Persisted Chroma database)
```

---

## Integration Sequence

### Deploy Timeline
```
Week 1: Local Testing
├─ Day 1: Run smoke test (10 queries)
├─ Day 2-3: Test all 47 sample queries
├─ Day 4-5: Gather support team feedback
└─ Day 6-7: Refine KB based on feedback

Week 2: Staging Deployment
├─ Deploy to staging environment
├─ Real support team testing
├─ Measure resolution rates
└─ Identify gaps/improvements

Week 3: Production Readiness
├─ Deploy to production (gradual rollout)
├─ Monitor performance metrics
├─ Adjust KB content
└─ Train support team on new workflow

Week 4+: Continuous Improvement
├─ Monitor daily metrics
├─ Collect real user interactions
├─ Expand KB based on patterns
└─ Scale to more automation scenarios
```

---

## Success Criteria by Component

### KB Component
- ✓ 9 comprehensive KB files
- ✓ 47 well-distributed sample queries
- ✓ Each KB file covers: symptoms, solutions, prevention, troubleshooting
- ✓ Time savings documented per automation

### API Component
- ✓ /health endpoint always healthy
- ✓ /ingest successfully indexes all 47 chunks
- ✓ /chat responds within 2 seconds
- ✓ Returns both answer and context

### Chroma Component
- ✓ Persists across container restarts
- ✓ Backup script creates .tar.gz files
- ✓ Restore script recovers data into new volume
- ✓ Queries return relevant semantic matches

### Testing Component
- ✓ Automated smoke test runs end-to-end
- ✓ Tests 10+ sample queries
- ✓ Reports success rate and context coverage
- ✓ Provides clear next steps

---

## Production Considerations

### Scaling
- Current: Single Chroma container, single API instance
- Medium load: Add API replicas, keep single Chroma (with RWO volume)
- High load: Managed Chroma service (Chroma Cloud) + multiple API replicas

### Embedding Model
- Dev: DummyEmbedding (fast, for testing)
- Prod: SentenceTransformer (accurate semantic matching)
- Alt: Larger models (BERT, MPNet) for better quality
- Alt: Managed embedding service (OpenAI, Cohere)

### LLM Model
- Dev/Staging: Ollama (local, free)
- Prod: OpenAI, Anthropic, or larger Ollama model
- Fallback: Template-based responses when LLM unavailable

### Monitoring
- Track: Query volume, response time, user satisfaction
- Alert: If /health unhealthy, if errors spike
- Feedback: Collect user ratings for each response
- Analytics: Track which KB files are most used

---

## Migration Path to Production

1. **Local Testing** (Done ✓)
   - KB created, indexed, tested
   - Smoke test validates infrastructure

2. **Staging** (Next)
   - Deploy with real Chroma + better embeddings
   - Real support team feedback
   - Production-like load testing

3. **Production** (After validation)
   - Deploy with monitoring
   - Gradual rollout (% of traffic)
   - Collect metrics and user feedback
   - Iterate and improve KB

---

That's the complete architecture and integration overview!

**Ready to test? Run: `.\test_chatbot_smoke.ps1`**
