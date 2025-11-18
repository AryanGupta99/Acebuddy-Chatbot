# HOW TO TEST YOUR SYSTEM RIGHT NOW

## Current State
✅ Server: **Running on http://127.0.0.1:8000**  
✅ Documents: **525 loaded**  
✅ Features: **All 7 initialized**  
✅ Status: **Ready for testing**

---

## TEST METHOD 1: Browser (Easiest)

### Step 1: Open API Documentation
```
http://127.0.0.1:8000/docs
```

### Step 2: Find the `/chat` Endpoint
- Scroll down to see all endpoints
- Find **POST /chat**

### Step 3: Click "Try it out"
- Red button appears on the right side

### Step 4: Enter Your Question
In the **Request body** box, replace the example with:
```json
{
  "query": "How do I reset my password?",
  "session_id": "test1"
}
```

### Step 5: Click "Execute"
- Blue button below the request body
- Watch the response appear below

### Step 6: See the Response
You should see:
```json
{
  "answer": "Long detailed response from Ollama about password reset...",
  "confidence": 85.5,
  "source": "ollama_mistral_7b",
  "intent": "password_reset",
  "response_quality": 0.87,
  "documents_used": 3
}
```

---

## TEST METHOD 2: Command Line (Windows PowerShell)

### Quick One-Liner Test
```powershell
$body = @{ query = "How do I reset my password?"; session_id = "test1" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json | Write-Host
```

### Step-by-Step
```powershell
# 1. Create the request
$query = "How do I reset my password?"
$body = @{ 
    query = $query
    session_id = "test1" 
} | ConvertTo-Json

# 2. Send it
$response = Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/chat" `
    -Method POST `
    -Body $body `
    -ContentType "application/json"

# 3. See the answer
Write-Host "ANSWER:"
Write-Host $response.answer
Write-Host ""
Write-Host "CONFIDENCE: $($response.confidence)%"
Write-Host "SOURCE: $($response.source)"
```

---

## TEST METHOD 3: Python Script

### Create a Test Script
```python
# File: test_it.py
import requests
import json
import time

print("\n" + "="*80)
print("TESTING ACEBUDDY RAG SYSTEM")
print("="*80 + "\n")

# Test 1
print("[TEST 1] Password Reset")
start = time.time()
response = requests.post(
    "http://127.0.0.1:8000/chat",
    json={"query": "How do I reset my password?", "session_id": "test1"},
    timeout=120
)
elapsed = time.time() - start

data = response.json()
print(f"Response Time: {elapsed:.1f}s")
print(f"Confidence: {data['confidence']}%\n")
print(data['answer'][:500] + "...\n")

# Test 2
print("[TEST 2] RDP Issues")
start = time.time()
response = requests.post(
    "http://127.0.0.1:8000/chat",
    json={"query": "How do I troubleshoot RDP?", "session_id": "test2"},
    timeout=120
)
elapsed = time.time() - start

data = response.json()
print(f"Response Time: {elapsed:.1f}s")
print(f"Confidence: {data['confidence']}%\n")
print(data['answer'][:500] + "...\n")

print("="*80)
print("TEST COMPLETE")
print("="*80)
```

### Run It
```powershell
cd "c:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"
python test_it.py
```

---

## TEST METHOD 4: cURL Command

```powershell
# Using curl (if installed)
curl -X POST "http://127.0.0.1:8000/chat" `
  -H "Content-Type: application/json" `
  -d '{"query":"How do I reset my password?","session_id":"test1"}'
```

---

## EXPECTED RESULTS

### What You Should See:

✅ **Response Code:** 200 (Success)
✅ **Answer:** Full detailed response from Ollama
✅ **Confidence:** 70-95%
✅ **Source:** "ollama_mistral_7b"
✅ **Response Time:** 4-12 seconds

### Example Good Response:
```
"answer": "To reset your password in AceBuddy, follow these steps: 
1. Click on your account icon in the top right corner
2. Select 'Account Settings'
3. Click 'Change Password'
4. Enter your current password
5. Enter your new password (must be at least 8 characters)
6. Confirm the new password
7. Click 'Save Changes'

If you've forgotten your current password, you'll need to contact your administrator 
for a password reset. Security questions or two-factor authentication recovery codes 
can also be used if you've set them up previously."

"confidence": 88.5
```

### What NOT to Worry About:
- ⚠️ SSL warnings (PostHog telemetry, harmless)
- ⚠️ First query slower (Ollama warming up)
- ⚠️ Response time varies (depends on query complexity)

---

## TROUBLESHOOTING

### Server Not Responding

**Error:** Cannot connect to http://127.0.0.1:8000

**Solution:**
```powershell
# 1. Check if server is running
Get-Process python | Where-Object { $_.CommandLine -like "*uvicorn*" }

# 2. If not running, start it
cd "c:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 3. Wait 10 seconds, then test again
```

### Ollama Not Found

**Error:** "Ollama not responding" or "connection refused"

**Solution:**
```powershell
# 1. Check if Ollama is running
curl http://127.0.0.1:11434/api/tags

# 2. If not running, start it (in new terminal)
ollama serve

# 3. Verify it started
curl http://127.0.0.1:11434/api/tags
# Should show: {"models": [{"name": "mistral:latest"...}]}
```

### Port 8000 Already in Use

**Error:** "Address already in use"

**Solution:**
```powershell
# 1. Find what's using port 8000
Get-NetTCPConnection -LocalPort 8000

# 2. Kill the process
Get-Process -Id <PID> | Stop-Process -Force

# 3. Or use a different port
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### Slow Responses (>15 seconds)

**Reasons:** First query, heavy system load, or complex query

**Solution:**
```powershell
# 1. Try a simple question first
# "How do I reset my password?"

# 2. Check system resources
Get-Process | Where-Object { $_.WorkingSet -gt 1GB } | Sort-Object WorkingSet

# 3. Use Phi 3B (faster) instead
ollama run phi
# Then update: MODEL = "phi" in app/main.py
```

---

## QUICK TEST CHECKLIST

- [ ] Server running: `Get-Process python | grep uvicorn`
- [ ] Ollama running: `curl http://127.0.0.1:11434/api/tags`
- [ ] Can access docs: `http://127.0.0.1:8000/docs` in browser
- [ ] Health check passes: `curl http://127.0.0.1:8000/health`
- [ ] Test query returns: Response with > 0% confidence
- [ ] Response time < 15s: (normal for first query)
- [ ] Confidence > 70%: (good match with KB)
- [ ] Answer is relevant: (answers the question asked)

---

## SAMPLE TEST QUESTIONS

Try these to see the system in action:

1. **"How do I reset my password?"**
   - Expected: Account/password information
   - Difficulty: Easy (covered in KB)

2. **"How do I troubleshoot RDP connection issues?"**
   - Expected: RDP troubleshooting steps
   - Difficulty: Medium (good KB match)

3. **"How do I add a new user to the system?"**
   - Expected: User management steps
   - Difficulty: Easy (covered in KB)

4. **"What's the best way to improve server performance?"**
   - Expected: Performance optimization tips
   - Difficulty: Medium (in server performance doc)

5. **"How do I set up a new printer?"**
   - Expected: Printer setup instructions
   - Difficulty: Easy (covered in KB)

---

## SUCCESS INDICATORS

✅ All good if:
- Server starts without errors
- Ollama is running
- API docs load
- Chat endpoint works
- Responses contain relevant information
- Confidence > 70%

🟡 Something to check if:
- Confidence < 50%: Question might be outside KB scope
- Response time > 20s: Check system resources or Ollama status
- Empty response: Ollama might not be running

❌ Error if:
- Cannot connect to server
- HTTP 500 error
- "Ollama not responding"
- Timeout after 2 minutes

---

## NEXT STEPS AFTER TESTING

1. **If working well:**
   - Keep server running
   - Add more documents to `/data/kb/`
   - Monitor performance metrics

2. **If having issues:**
   - Check troubleshooting above
   - Verify Ollama is fully running
   - Check server logs for errors

3. **For production:**
   - Set up auto-restart on server
   - Configure monitoring
   - Plan knowledge base updates
   - Train users on how to use it

---

## SUPPORT

If tests pass: ✅ **Your system is ready for use!**

If tests fail: 
1. Follow troubleshooting section
2. Check server logs: `Get-Content server.log -Tail 50`
3. Verify both services running (FastAPI + Ollama)
4. Try a simple question first

---

**Your system is ready. Test it now!** 🚀
