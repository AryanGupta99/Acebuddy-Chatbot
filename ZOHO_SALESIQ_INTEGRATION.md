# Zoho SalesIQ Integration Guide

Complete guide to integrate AceBuddy RAG chatbot with Zoho SalesIQ for live support automation.

---

## 🎯 Integration Architecture

```
┌─────────────────────┐
│  Zoho SalesIQ       │
│  (Chat Interface)   │
└──────────┬──────────┘
           │
           │ Webhook → POST /chat
           │
┌──────────v──────────────────────────┐
│  AceBuddy FastAPI (Your Server)     │
│  ├─ Intent Classification            │
│  ├─ Query Enhancement               │
│  ├─ Vector Search (Chroma)          │
│  ├─ LLM Generation (Ollama/OpenAI)  │
│  └─ Response Validation             │
└──────────┬──────────────────────────┘
           │
           │ Returns: Answer + Context
           │
┌──────────v──────────┐
│ Display to User in  │
│ SalesIQ Chat Panel  │
└─────────────────────┘
```

---

## 📋 Prerequisites

- ✅ Zoho SalesIQ account (create at https://salesiq.zoho.com)
- ✅ AceBuddy API running (localhost:8000 or public URL)
- ✅ Public IP or domain name for webhook callback
- ✅ OpenAI API key (for embeddings)
- ✅ Ollama running (for response generation) or OpenAI API

---

## 🚀 Setup Steps

### **Step 1: Enable Zoho SalesIQ Webhooks**

1. Go to **Zoho SalesIQ Dashboard**
2. Click **Settings** → **Integrations** → **Webhooks**
3. Look for **Custom Integration** or **API Integration** option
4. Enable **Custom Rules/Actions**

### **Step 2: Get Your AceBuddy API Endpoint**

**Option A: Local Testing (ngrok tunnel)**
```powershell
# Install ngrok: https://ngrok.com/download

# In one terminal, start your API:
python app/main.py

# In another terminal, create tunnel:
ngrok http 8000

# Copy the HTTPS URL: https://xxxxx-xx-xx-xx.ngrok.io
```

**Option B: Production Server**
- Use your actual server IP/domain: `https://your-server.com:8000`
- Make sure port 8000 is accessible from internet
- Use HTTPS (SSL certificate required for webhooks)

### **Step 3: Create Webhook in SalesIQ**

1. In SalesIQ → **Settings** → **Webhooks/Integrations**
2. Create **Custom Webhook** or **Bot Integration**
3. Set webhook URL: `https://your-server.com:8000/chat`
4. Method: **POST**
5. Content Type: **application/json**
6. Trigger: **On User Message**

### **Step 4: Configure Payload Format**

Your webhook payload should look like:
```json
{
  "query": "How do I reset my password?",
  "user_id": "user_123",
  "session_id": "session_abc",
  "chat_context": "Previous questions...",
  "timestamp": "2025-11-18T14:30:00Z"
}
```

### **Step 5: Map Response Back to SalesIQ**

SalesIQ will receive:
```json
{
  "answer": "Follow these steps...",
  "confidence": 0.76,
  "context": ["source1", "source2"],
  "session_id": "session_abc",
  "response_quality": 0.85
}
```

You need to map this in SalesIQ's response handler to:
- Display `answer` to user
- Store `session_id` for conversation continuity
- Use `confidence` to decide if human handoff is needed

---

## 🔧 Implementation Options

### **Option 1: Using Zoho SalesIQ Bot Builder** (Recommended - No Coding)

#### Step-by-Step in SalesIQ UI:

1. **Create Bot Flow**
   - SalesIQ Dashboard → Bots → Create New Bot
   - Choose "**Custom Integration**" template

2. **Add Message Trigger**
   - Trigger: "When user sends message"
   - Conditions: Always trigger

3. **Add Webhook Action**
   - Action: "**Call Webhook**"
   - URL: `https://your-server.com:8000/chat`
   - Method: POST
   - Headers: `Content-Type: application/json`
   - Body:
   ```json
   {
     "query": "${userMessage}",
     "user_id": "${userId}",
     "session_id": "${sessionId}"
   }
   ```

4. **Map Response**
   - Store response in variable: `${botResponse}`
   - Extract fields:
     - `${botResponse.answer}` → Display to user
     - `${botResponse.confidence}` → Decision variable
     - `${botResponse.session_id}` → Store session

5. **Add Conditional Logic**
   ```
   if (confidence >= 0.7) {
       Send answer to user
   } else {
       Route to human agent
   }
   ```

6. **Test & Deploy**
   - Click "**Test**" button in bot builder
   - Preview chat interaction
   - Publish to **Live**

---

### **Option 2: Using API/Webhook Directly** (Advanced - Custom Code)

If SalesIQ doesn't have direct bot builder, use webhook integration:

#### In SalesIQ Admin:
1. Go to **Integrations** → **Custom Webhooks**
2. Add endpoint: `POST /chat`
3. Test connection

#### On Your Server - Create Handler:

The endpoint at `/chat` in `app/main.py` already handles this!

```python
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # ... existing implementation ...
    # Automatically handles Zoho requests
    return ChatResponse(...)
```

#### Configure in SalesIQ:
- **Outgoing Webhook**: Sends user message to `/chat`
- **Parse Response**: Extracts `answer` field
- **Display**: Shows answer in chat panel

---

### **Option 3: Full SalesIQ Bot with fallback** (Most Robust)

```javascript
// This goes in SalesIQ Bot Configuration (JavaScript)

async function handleUserMessage(userMessage, sessionId, userId) {
  try {
    // Call AceBuddy API
    const response = await fetch('https://your-server.com:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: userMessage,
        user_id: userId,
        session_id: sessionId,
        use_history: true
      })
    });

    const data = await response.json();

    // If high confidence, show answer
    if (data.confidence >= 0.7) {
      return {
        message: data.answer,
        type: 'answer',
        metadata: {
          confidence: data.confidence,
          sources: data.context_with_metadata
        }
      };
    }
    // If low confidence, route to human
    else {
      return {
        message: "I'm not sure about that. Let me connect you with a specialist.",
        type: 'escalate_to_human'
      };
    }

  } catch (error) {
    // Fallback to human if API fails
    return {
      message: "I'm having trouble connecting. A specialist will assist you shortly.",
      type: 'escalate_to_human'
    };
  }
}
```

---

## 📊 Response Quality & Handoff Logic

Configure when to escalate to human:

```python
# In your integration logic:

CONFIDENCE_THRESHOLD = 0.7  # 70%
QUALITY_THRESHOLD = 0.6     # 60%

if response.confidence < CONFIDENCE_THRESHOLD or response.response_quality < QUALITY_THRESHOLD:
    # Escalate to human agent
    salesiq.transfer_to_agent(
        reason="Low confidence answer",
        context=response.context_with_metadata,
        session_id=session_id
    )
else:
    # Send bot response
    salesiq.send_message(response.answer)
```

---

## 🔄 Conversation Flow

```
1. User opens chat in SalesIQ
   ↓
2. Enters question: "How to reset password?"
   ↓
3. SalesIQ webhook triggers → POST to /chat
   ↓
4. AceBuddy processes:
   - Intent: account_management
   - Retrieves context: 3 KB articles
   - Generates response: "Follow these steps..."
   - Confidence: 85%
   ↓
5. Returns response with metadata
   ↓
6. SalesIQ displays to user (or escalates if low confidence)
   ↓
7. Conversation saved for:
   - Future training
   - Analytics
   - Quality monitoring
```

---

## 🛠️ Testing the Integration

### **Test 1: Direct API Call**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I reset my password?",
    "user_id": "test_user",
    "session_id": "test_session"
  }'
```

Expected response:
```json
{
  "answer": "To reset your password: 1. Click 'Forgot Password'...",
  "confidence": 0.85,
  "response_quality": 0.8,
  "context_with_metadata": [...]
}
```

### **Test 2: From SalesIQ Chat Panel**

1. Go to SalesIQ → Your Chat Widget
2. Send test question: "How do I connect to WebDAV?"
3. Check response appears in 2-3 seconds
4. Verify it matches KB content

### **Test 3: Conversation Continuity**

1. Ask: "How to connect to server?"
2. Ask: "Can I do it on Mac?"
3. Verify second answer references first question

---

## 📈 Monitoring & Analytics

### **Track in SalesIQ:**
- User satisfaction (thumbs up/down)
- Escalation rate to humans
- Average response time
- Bot vs. human resolution

### **Track in AceBuddy:**
- Response confidence scores
- Most common queries
- Knowledge gaps (low-confidence questions)
- LLM generation latency

### **Create Dashboard:**
```bash
# View live metrics
curl http://localhost:8000/metrics

# Conversation statistics
curl http://localhost:8000/conversation/stats
```

---

## 🔐 Security Checklist

- [ ] API uses HTTPS (SSL certificate)
- [ ] Validate webhook signature from SalesIQ
- [ ] Rate limit requests (prevent abuse)
- [ ] Redact PII in logs (emails, phone numbers)
- [ ] Use API key authentication if needed
- [ ] Backup chat transcripts regularly
- [ ] Monitor for unusual patterns

### **Add Authentication (Optional)**

```python
# In app/main.py, add to chat endpoint:

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    authorization: Optional[str] = Header(None)
):
    # Validate API key
    if authorization != f"Bearer {os.getenv('SALESIQ_API_KEY')}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # ... rest of logic ...
```

Configure in SalesIQ webhook:
- Headers: `Authorization: Bearer your-api-key`

---

## 🚀 Deployment for Production

### **Option A: Docker on Your Server**

```bash
# On your server:
docker-compose up -d

# Make sure port 8000 is accessible
# Configure firewall: allow inbound on port 8000
```

### **Option B: Using Cloud Service**

- **AWS EC2**: Deploy Docker container
- **Azure**: App Service + Chroma (persistent)
- **DigitalOcean**: Docker droplet
- **Heroku**: Docker container

### **Option C: Behind Reverse Proxy (Nginx)**

```nginx
# /etc/nginx/sites-available/acebuddy

server {
    listen 443 ssl;
    server_name your-server.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📊 Expected Results

### **Before Integration:**
- Manual support: 1 agent handles ~10 queries/hour
- Customer wait time: 5-10 minutes
- Resolution rate: 60%

### **After Integration:**
- Automated support: ~100+ queries/hour
- Customer wait time: <5 seconds
- Resolution rate: 85%+ (70% without human escalation)
- Agent time freed for complex issues

---

## 🔧 Troubleshooting

### **Webhook not triggering**
- Check SalesIQ webhook settings
- Verify URL is accessible from internet
- Test with curl from your server
- Check firewall rules

### **Slow responses (>5 seconds)**
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Use faster model: `llama3.2:1b` instead of larger models
- Enable caching: `ENABLE_CACHE=true` in .env
- Use OpenAI instead: `USE_OPENAI=true`

### **Low confidence scores**
- Add more KB articles
- Improve query enhancement
- Use better embeddings (OpenAI instead of local)
- Fine-tune model with chat transcripts

### **Messages not appearing in SalesIQ**
- Verify response mapping in bot config
- Check response format matches expectations
- Enable webhook logs in SalesIQ
- Test with curl first

---

## 📚 Next Steps

1. **Enable webhook** in SalesIQ (5 min)
2. **Test with curl** (2 min)
3. **Deploy to production** (15 min)
4. **Configure handoff logic** (10 min)
5. **Monitor & optimize** (ongoing)

---

## 💡 Advanced Features

### **Conversation Context**
```json
{
  "query": "How about for Mac?",
  "session_id": "session_123",
  "use_history": true  // ← Uses previous messages for context
}
```

### **User Metadata**
```json
{
  "user_id": "user_abc",
  "user_email": "user@company.com",
  "user_name": "John Doe"
}
```

### **Custom Instructions**
```json
{
  "system_prompt": "You are AceBuddy IT support. Be professional and concise."
}
```

---

## 📞 Support Resources

- **Zoho SalesIQ Docs**: https://www.zoho.com/salesiq/help/
- **Webhook Setup**: https://www.zoho.com/salesiq/webhooks-guide/
- **AceBuddy API Docs**: http://your-server:8000/docs
- **Ollama Docs**: https://github.com/ollama/ollama

---

## 🎯 Success Metrics

Track these after going live:

| Metric | Target | Current |
|--------|--------|---------|
| Response time | <2s | - |
| Bot accuracy | >80% | - |
| Customer satisfaction | >4/5 | - |
| Human escalation | <20% | - |
| Daily conversations | 100+ | - |

---

*Last updated: November 18, 2025*
