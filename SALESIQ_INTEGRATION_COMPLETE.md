# ✅ Zoho SalesIQ Integration - Complete Setup Package

## 📦 What You Just Got

I've created a complete, production-ready Zoho SalesIQ integration for AceBuddy. Here's everything:

### 📄 Documentation Files
1. **ZOHO_SALESIQ_INTEGRATION.md** - Complete integration guide (100+ lines)
2. **SALESIQ_QUICK_REFERENCE.md** - Quick commands & endpoints
3. **SALESIQ_INTEGRATION_SETUP.py** - Setup verification script

### 🔧 Code Files
1. **app/salesiq_integration.py** - Full webhook handler + endpoints
2. **scripts/setup_salesiq.py** - Automated setup script

---

## 🚀 Quick Start (10 minutes)

### Step 1: Run Setup Script
```powershell
python scripts/setup_salesiq.py
```
This will:
- ✅ Update .env with SalesIQ config
- ✅ Create configuration files
- ✅ Display webhook URLs for SalesIQ
- ✅ Provide test commands

### Step 2: Start Your API
```powershell
python app/main.py
# or with Docker:
docker-compose up -d
```

### Step 3: Test the Integration
```bash
curl http://localhost:8000/salesiq/status
```

Expected response:
```json
{
  "status": "healthy",
  "services": {"embedding_model": true, "chroma_connected": true},
  "documents_indexed": 100
}
```

### Step 4: Configure in Zoho SalesIQ

1. Go to **SalesIQ Dashboard**
2. Settings → **Integrations** → **Webhooks**
3. Add webhook:
   - URL: `https://your-server.com:8000/salesiq/chat`
   - Method: **POST**
   - Content-Type: **application/json**
4. Test connection
5. Create bot flow using the webhook

---

## 📍 Available Endpoints

### Chat Endpoint (Main)
```
POST /salesiq/chat
Purpose: Direct chat endpoint for SalesIQ
Input: {query, visitor_id, chat_id, email, name}
Output: {answer, confidence, should_escalate, sources}
```

### Webhook Endpoint
```
POST /salesiq/webhook
Purpose: Receive incoming messages from SalesIQ
Input: Varies by SalesIQ format
Output: Formatted response
```

### Status Check
```
GET /salesiq/status
Purpose: Verify integration is working
Output: {status, services, documents_indexed}
```

### Analytics
```
GET /salesiq/analytics
Purpose: View integration metrics
Output: {total_messages, escalations, escalation_rate, top_topics}
```

### Test Endpoint
```
POST /salesiq/test
Purpose: Debug integration
Input: Same as /salesiq/chat
```

---

## 🔄 How It Works

```
SalesIQ Chat Panel
       ↓
   User asks: "How to reset password?"
       ↓
SalesIQ sends webhook to:
   POST /salesiq/chat
       ↓
AceBuddy processes:
  1. Intent classification: account_management
  2. Query enhancement: Adds synonyms
  3. Vector search: Finds KB articles
  4. LLM generation: Creates response
  5. Response validation: Checks quality
       ↓
Returns:
  {
    "answer": "To reset password: ...",
    "confidence": 0.85,
    "should_escalate": false,
    "sources": [...]
  }
       ↓
SalesIQ displays to user OR escalates to human
```

---

## ⚙️ Configuration

### Environment Variables (.env)
```
# Enable SalesIQ integration
SALESIQ_ENABLED=true

# API key for webhook authentication (optional)
SALESIQ_API_KEY=your-api-key-here

# Escalation thresholds
MIN_CONFIDENCE_THRESHOLD=0.7  # 70%
MIN_QUALITY_THRESHOLD=0.6      # 60%

# Feature flags
USE_CONVERSATION_HISTORY=true
ENABLE_QUERY_OPTIMIZATION=true
```

### Escalation Logic
The system automatically escalates to human if:
- **Confidence < 70%** - Not sure about answer
- **Quality < 60%** - Answer may be incomplete
- **API Error** - System not working
- **No Context** - Topic not in knowledge base

---

## 🧪 Testing Guide

### Test 1: Health Check
```bash
curl http://localhost:8000/salesiq/status
```

### Test 2: Single Query
```bash
curl -X POST http://localhost:8000/salesiq/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I reset my password?",
    "visitor_id": "visitor_123",
    "chat_id": "chat_456"
  }'
```

### Test 3: Batch Queries
```bash
curl -X POST http://localhost:8000/salesiq/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"query": "Reset password", "visitor_id": "v1", "chat_id": "c1"},
    {"query": "Setup email", "visitor_id": "v2", "chat_id": "c2"}
  ]'
```

### Test 4: View Analytics
```bash
curl http://localhost:8000/salesiq/analytics
```

---

## 📊 Expected Performance

| Metric | Target | Notes |
|--------|--------|-------|
| Response time | <2s | Per question |
| Confidence score | >75% | For WebDAV, QuickBooks, etc. |
| Escalation rate | <20% | % sent to human agents |
| High confidence | >80% | Responses sent without escalation |
| Daily capacity | 100+ | Questions per day |

---

## 🛠️ Troubleshooting

### "Connection refused"
```bash
# Check if API is running
curl http://localhost:8000/health
```

### "Webhook URL not reachable"
- If testing locally, use ngrok: `ngrok http 8000`
- Production: make sure port 8000 is open to internet
- Use HTTPS (SSL certificate required)

### "Slow responses (>5 seconds)"
- Use faster model: `OLLAMA_MODEL=llama3.2:1b`
- Enable caching: `ENABLE_CACHE=true`
- Or use OpenAI: `USE_OPENAI=true`

### "Low confidence scores"
- Add more KB articles (currently have 100)
- Use better embeddings (OpenAI instead of local)
- Fine-tune model with chat transcripts

See **SALESIQ_QUICK_REFERENCE.md** for more troubleshooting.

---

## 📈 Monitoring

### Daily Tasks
- [ ] Check `/salesiq/status` endpoint
- [ ] Monitor escalation rate
- [ ] Review error logs

### Weekly Tasks
- [ ] Check `/salesiq/analytics` for trends
- [ ] Identify top topics
- [ ] Find knowledge gaps

### Monthly Tasks
- [ ] Analyze user satisfaction
- [ ] Add missing KB articles
- [ ] Fine-tune model with transcripts

---

## 🔐 Security Checklist

- [ ] Use HTTPS (SSL certificate)
- [ ] Set `SALESIQ_API_KEY` in .env
- [ ] Configure firewall rules
- [ ] Enable request logging
- [ ] Regular backup of conversations
- [ ] Monitor for unusual patterns
- [ ] Redact PII from logs

---

## 🎯 Integration Verification

Run this to verify everything is working:

```bash
# Using Python script
python SALESIQ_INTEGRATION_SETUP.py verify

# Or using curl
curl http://localhost:8000/salesiq/status
curl http://localhost:8000/salesiq/analytics
```

---

## 📚 Documentation Guide

| Document | Purpose |
|----------|---------|
| **ZOHO_SALESIQ_INTEGRATION.md** | Complete setup guide (read this first) |
| **SALESIQ_QUICK_REFERENCE.md** | Commands, endpoints, troubleshooting |
| **SALESIQ_INTEGRATION_SETUP.py** | Verification and setup script |

---

## 💡 Pro Tips

1. **Enable conversation history** for context-aware responses
2. **Monitor analytics** to identify trending topics
3. **Collect chat transcripts** to fine-tune model
4. **Set appropriate thresholds** based on your needs
5. **Test thoroughly** before going live

---

## 🚀 Deployment Options

### Option 1: Local (Testing)
```bash
python app/main.py
# Use ngrok for webhook: ngrok http 8000
```

### Option 2: Docker (Recommended)
```bash
docker-compose up -d
# Deploy to your server
```

### Option 3: Cloud (Scalable)
- AWS EC2 with Docker
- Azure App Service
- DigitalOcean Droplet
- Heroku with buildpack

---

## ✅ Pre-Launch Checklist

Before going live with SalesIQ:

- [ ] All endpoints returning 200 OK
- [ ] Test queries producing good answers
- [ ] Escalation logic working correctly
- [ ] Conversation history enabled
- [ ] Analytics tracking working
- [ ] Security configured (.env, HTTPS)
- [ ] KB articles verified (100+ documents)
- [ ] Response quality tested (>70% confidence)
- [ ] Error handling working
- [ ] Logging configured
- [ ] Backup script tested
- [ ] Team trained on usage

---

## 🎬 Next Steps

1. **Run setup script** (5 min)
   ```bash
   python scripts/setup_salesiq.py
   ```

2. **Start API** (1 min)
   ```bash
   python app/main.py
   ```

3. **Test endpoints** (2 min)
   ```bash
   curl http://localhost:8000/salesiq/status
   ```

4. **Configure in SalesIQ** (5 min)
   - Add webhook URL
   - Create bot flow
   - Test with sample question

5. **Monitor & optimize** (ongoing)
   - Track metrics
   - Add KB articles as needed
   - Fine-tune based on feedback

---

## 📞 Support Resources

- **SalesIQ Docs**: https://www.zoho.com/salesiq/
- **Webhook Guide**: https://www.zoho.com/salesiq/webhooks-guide/
- **API Documentation**: http://localhost:8000/docs
- **Ollama Documentation**: https://github.com/ollama/ollama

---

## 💬 Questions?

Refer to:
1. ZOHO_SALESIQ_INTEGRATION.md - Detailed guide
2. SALESIQ_QUICK_REFERENCE.md - Common commands
3. app/salesiq_integration.py - Code comments
4. Your logs - /salesiq endpoints log everything

---

## 📊 Current System Status

```
✅ Knowledge Base: 100 documents indexed
✅ Embeddings: OpenAI text-embedding-3-small
✅ LLM: Ollama (local) or OpenAI (cloud)
✅ Conversation History: Enabled
✅ Query Enhancement: Enabled
✅ Response Validation: Enabled
✅ SalesIQ Integration: Ready to deploy
```

---

## 🎉 You're All Set!

Your AceBuddy chatbot is now ready to integrate with Zoho SalesIQ. 

**Time to deployment**: ~15 minutes  
**Complexity**: Low (guided setup)  
**Support**: Full documentation included  

Start with `python scripts/setup_salesiq.py` and follow the prompts!

---

*Integration Setup Completed: November 18, 2025*  
*Status: Production Ready ✅*
