# 🚀 AceBuddy RAG Chatbot - Now with OLLAMA! ✅

Your chatbot is now fully configured to use **Ollama** for AI-powered responses!

## ✅ What's Ready

- **✅ Ollama Integration** - Using Mistral 7B model for responses
- **✅ 525 Documents Ingested** - Password reset, RDP, user management, printer setup, etc.
- **✅ Real Responses** - No more dummy embeddings, actual AI-generated answers
- **✅ Advanced RAG Features** - Caching, streaming, analytics, fallbacks all enabled

## 🔧 Setup (One-Time)

Make sure you have Ollama installed and running:

```bash
# Download from https://ollama.ai

# Start Ollama service (required!)
ollama serve

# In another terminal, pull mistral model (if not already downloaded)
ollama pull mistral
```

## 🚀 Quick Start

### Option 1: Use the Batch File (Easiest for Windows)
```bash
# Double-click this file:
RUN_WITH_OLLAMA.bat
```

This will:
1. Check Ollama is running
2. Start the FastAPI server
3. Wait 15 seconds for initialization
4. Run a test query
5. Show the AI response

### Option 2: Manual Start

**Terminal 1 - Start Server:**
```bash
cd "C:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 - Test It:**
```bash
python simple_test.py
```

Or use the interactive API docs:
```
http://127.0.0.1:8000/docs
```

## 📊 What the Chatbot Can Answer

The knowledge base covers:
- 🔐 **Password Reset** - Account access recovery
- 🌐 **RDP Connection Issues** - Remote desktop troubleshooting
- 👥 **User Management** - Adding/removing users
- 📊 **Server Performance** - Performance optimization
- 🖨️ **Printer Setup** - Printer configuration & troubleshooting
- 📧 **Email Issues** - Email client troubleshooting
- 💾 **Disk Storage** - Disk space and storage management
- 📚 **QuickBooks** - Accounting software issues

## 🧪 Test Queries

Try these to see it in action:

```bash
# Query 1: Password Reset
"How do I reset my password?"

# Query 2: RDP Connection
"How do I troubleshoot RDP connection issues?"

# Query 3: User Management
"How do I add a new user to my system?"

# Query 4: Server Performance
"What should I do if my server is running slow?"

# Query 5: Printer Setup
"How do I set up a printer on my network?"
```

## 📋 Configuration

The system automatically uses:
- **Model:** Mistral 7B (can switch to Phi 3B if needed)
- **Host:** http://localhost:11434 (Ollama)
- **Port:** 8000 (FastAPI)
- **Response Timeout:** 120 seconds (Ollama response generation)
- **Documents:** 525 (from KB files + Zobot data)

### Change Model (Optional)

Edit before starting server:
```bash
# Use Phi 3B (faster, but less capable)
set OLLAMA_MODEL=phi

# Or pass as env var
$env:OLLAMA_MODEL="phi"; uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 🔍 Checking Server Status

### Health Check
```bash
curl http://127.0.0.1:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "services": {
    "embedding_model": true,
    "chroma_client": true,
    "collection": true
  }
}
```

### Ollama Status
```bash
curl http://localhost:11434/api/tags
```

Shows installed models and versions.

## 📝 API Endpoints

- `POST /chat` - Send a query and get a response
- `GET /health` - Server health check
- `GET /docs` - Interactive API documentation (Swagger UI)

### Example Query
```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/chat",
    json={"query": "How do I reset my password?"},
    timeout=120
)

print(response.json())
```

## ⚡ Performance Expectations

- **First Query:** 8-15 seconds (Ollama model initialization)
- **Subsequent Queries:** 4-8 seconds (depending on query complexity)
- **Cached Queries:** <100ms (if cached by semantic cache)

## 🐛 Troubleshooting

### "Cannot connect to server"
- Make sure server is running: `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Check port 8000 is not in use

### "Ollama not responding"
- Start Ollama: `ollama serve`
- Make sure it's running on http://localhost:11434

### "Model not found: mistral"
- Pull the model: `ollama pull mistral`
- Check with: `ollama list`

### Very slow responses
- Ollama is CPU-intensive; make sure you have decent CPU
- Try the faster Phi model: `set OLLAMA_MODEL=phi`

### Port already in use
- Kill existing server: `Get-Process python | Stop-Process`
- Or use different port: `--port 8001`

## 📊 Expected Responses

When you ask "How do I reset my password?" you should get something like:

> To reset your password in the AceBuddy system:
>
> 1. Navigate to the login page
> 2. Click on "Forgot Password" link
> 3. Enter your registered email address
> 4. Check your email for a password reset link
> 5. Click the link and create a new password
> 6. Your account will be updated immediately
>
> If you don't receive the email within 5 minutes, check your spam folder. For additional help, contact our support team at support@acecloudhosting.com

(Actual response generated by Ollama/Mistral based on your KB)

## 🎯 Next Steps

1. ✅ Start the server
2. ✅ Test a few queries
3. ✅ Monitor response quality
4. ✅ Deploy to production when ready

## 📞 Support

If something goes wrong:
1. Check logs in the server window
2. Verify Ollama is running
3. Check the knowledge base files in `data/kb/`
4. Review `app/main.py` for integration details

---

**Status:** ✅ READY FOR TESTING WITH OLLAMA

Enjoy your AI-powered support chatbot!
