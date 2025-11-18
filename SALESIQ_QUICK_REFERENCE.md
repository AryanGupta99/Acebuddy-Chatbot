# Zoho SalesIQ Integration - Quick Reference

## 🚀 3-Step Quick Start

### Step 1: Setup (5 minutes)
```powershell
cd scripts
python setup_salesiq.py
```

### Step 2: Run API
```powershell
python app/main.py
# Or with Docker:
docker-compose up -d
```

### Step 3: Configure in SalesIQ
1. Go to SalesIQ Settings → Integrations
2. Add webhook: `POST https://your-server.com:8000/salesiq/chat`
3. Test with sample question

---

## 📍 Endpoint Reference

### Direct Chat Endpoint
```
POST /salesiq/chat

Request:
{
  "query": "How do I reset password?",
  "visitor_id": "visitor_123",
  "chat_id": "chat_456",
  "email": "user@example.com",
  "name": "John Doe"
}

Response:
{
  "answer": "To reset your password: ...",
  "confidence": 0.85,
  "should_escalate": false,
  "sources": [
    {"title": "password_reset.md", "confidence": 0.92}
  ],
  "metadata": {
    "response_quality": 0.8,
    "session_id": "chat_456"
  }
}
```

### Webhook Endpoint
```
POST /salesiq/webhook

Receives messages from SalesIQ and returns formatted response
```

### Health Check
```
GET /salesiq/status

Returns:
{
  "status": "healthy",
  "services": {...},
  "documents_indexed": 100
}
```

### Analytics
```
GET /salesiq/analytics

Returns:
{
  "total_messages": 1250,
  "escalations": 150,
  "escalation_rate": "12.0%",
  "high_confidence_responses": 900,
  "top_topics": {...}
}
```

---

## 🔧 Configuration

### Environment Variables (.env)
```
SALESIQ_ENABLED=true
SALESIQ_API_KEY=your-api-key
MIN_CONFIDENCE_THRESHOLD=0.7
MIN_QUALITY_THRESHOLD=0.6
USE_CONVERSATION_HISTORY=true
```

### Escalation Rules
- **Confidence < 0.7**: Escalate to human
- **Quality < 0.6**: Escalate to human
- **API Error**: Escalate to human
- **No Context**: Escalate to human

---

## 🧪 Testing

### Test 1: Check Status
```bash
curl http://localhost:8000/salesiq/status
```

### Test 2: Send Chat Message
```bash
curl -X POST http://localhost:8000/salesiq/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I connect to WebDAV?",
    "visitor_id": "test_visitor",
    "chat_id": "test_chat"
  }'
```

### Test 3: Batch Messages
```bash
curl -X POST http://localhost:8000/salesiq/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"query": "Reset password", "visitor_id": "v1", "chat_id": "c1"},
    {"query": "Setup email", "visitor_id": "v2", "chat_id": "c2"}
  ]'
```

---

## 📊 Expected Response Quality

| Question Type | Expected Confidence | Escalation? |
|---------------|-------------------|-------------|
| WebDAV setup | 0.85+ | No |
| QuickBooks | 0.80+ | No |
| General IT | 0.70+ | No |
| Uncommon topics | 0.50-0.65 | Yes |
| Off-topic | 0.30 | Yes |

---

## 🛠️ Common Issues

### Issue: Webhook not triggering
**Solution:**
- Verify URL is accessible from internet
- Check SalesIQ webhook configuration
- Test with curl: `curl -X POST https://your-server/salesiq/chat ...`

### Issue: Slow responses (>5 seconds)
**Solution:**
- Use faster model: `OLLAMA_MODEL=llama3.2:1b`
- Enable caching: `ENABLE_CACHE=true`
- Use OpenAI: `USE_OPENAI=true`

### Issue: Low confidence scores
**Solution:**
- Add more KB articles
- Improve embeddings with OpenAI API
- Fine-tune model with chat transcripts

### Issue: Messages not appearing in SalesIQ
**Solution:**
- Verify response format matches expectations
- Check webhook logs in SalesIQ
- Enable debug mode in bot

---

## 📈 Monitoring Checklist

Daily:
- [ ] Check `/salesiq/status` returns healthy
- [ ] Monitor error logs
- [ ] Track escalation rate (should be <20%)

Weekly:
- [ ] Review top topics from `/salesiq/analytics`
- [ ] Check response quality trends
- [ ] Verify all KB articles are accessible

Monthly:
- [ ] Analyze conversation trends
- [ ] Add missing KB articles
- [ ] Fine-tune model with new transcripts

---

## 💡 Pro Tips

1. **Conversation Context**: Enable `use_history=true` to remember previous messages
2. **User Metadata**: Send email/name for better tracking
3. **Batch Processing**: Use `/salesiq/batch` for testing multiple queries
4. **Analytics**: Check `/salesiq/analytics` to identify gaps
5. **API Keys**: Use environment variables, never hardcode

---

## 🔗 Useful Links

- **SalesIQ Dashboard**: https://salesiq.zoho.com
- **Webhook Docs**: https://www.zoho.com/salesiq/webhooks-guide/
- **API Docs**: http://your-server:8000/docs
- **Integration Guide**: See `ZOHO_SALESIQ_INTEGRATION.md`

---

## 📞 Troubleshooting Commands

```bash
# Check API is running
curl http://localhost:8000/health

# Test SalesIQ integration
curl http://localhost:8000/salesiq/status

# View recent logs
docker logs -f acebuddy-api

# Check Chroma collection
curl http://localhost:8000/health | jq .services.collection

# Verify embeddings
python -c "import chromadb; c = chromadb.PersistentClient('data/chroma'); print(c.get_collection('acebuddy_kb').count())"
```

---

**Last Updated**: November 18, 2025  
**Status**: Production Ready ✅
