# AceBuddy Smoke Test - Quick Start Guide

## ⚡ Quick Run

### Option 1: Run Directly (Recommended)
```powershell
cd "c:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG"
powershell -ExecutionPolicy Bypass -File .\test_chatbot_smoke.ps1
```

### Option 2: Run with Custom Wait Time
```powershell
powershell -ExecutionPolicy Bypass -File .\test_chatbot_smoke.ps1 -MaxWaitSeconds 60
```

### Option 3: Run in New Window (Non-blocking)
```powershell
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File .\test_chatbot_smoke.ps1"
```

---

## 🔍 What the Script Does

1. **Starts Docker Compose** - Launches FastAPI (port 8000) and Chroma (port 8001)
2. **Waits for Services** - Polls `/health` endpoint up to 60 seconds
3. **Tests Health Endpoint** - Verifies API and Chroma are ready
4. **Ingests KB Files** - Indexes all 9 KB files (47 chunks) into Chroma
5. **Runs 10 Sample Queries** - Tests RAG retrieval with real queries
6. **Reports Results** - Shows success rate and context coverage

---

## ✅ Expected Output

```
[HH:MM:SS] [INFO] Step 1: Starting Docker Compose services...
[HH:MM:SS] [SUCCESS] Docker Compose started
[HH:MM:SS] [INFO] Step 2: Waiting for services to be ready...
[HH:MM:SS] [SUCCESS] Service is healthy!
[HH:MM:SS] [INFO] Step 3: Testing /health endpoint...
[HH:MM:SS] [SUCCESS] Health Status: healthy
[HH:MM:SS] [INFO] Step 4: Ingesting KB files...
[HH:MM:SS] [SUCCESS] Ingest Response: Successfully ingested X documents
[HH:MM:SS] [INFO] Step 5: Running sample queries...
[HH:MM:SS] [SUCCESS] [1/10] Query: 'I forgot my password...' - Intent: password_reset - Context: True
...
[HH:MM:SS] [INFO] === SMOKE TEST SUMMARY ===
[HH:MM:SS] [SUCCESS] Successful: 10
[HH:MM:SS] [SUCCESS] With Context: 9
[HH:MM:SS] [SUCCESS] Context Coverage: 90%
[HH:MM:SS] [SUCCESS] PASS - System ready for testing!
```

---

## 🎯 Success Criteria

✅ **PASS** when:
- At least 8/10 queries succeed
- At least 6/10 queries return context from KB
- Context coverage >= 80%

⚠️ **WARNING** when:
- Some queries fail
- Context coverage < 80%
- Check logs for issues (see troubleshooting below)

---

## 🔧 Troubleshooting

### Issue: "time out" while waiting for service
**Solution:** Increase wait time
```powershell
.\test_chatbot_smoke.ps1 -MaxWaitSeconds 120
```

### Issue: Docker Compose failed to start
**Solution:** Check logs
```powershell
docker-compose logs --tail 50
```

### Issue: Service is not healthy
**Solution:** Check if ports are in use
```powershell
netstat -ano | findstr "8000\|8001"
# If in use, stop other services or change ports in docker-compose.yml
```

### Issue: Ingestion failed
**Solution:** Verify KB files exist
```powershell
ls .\data\kb\*.md
# Should show 9 files: 01_password_reset.md through 09_email_issues.md
```

### Issue: Query returns no context
**Solution:** Check API logs
```powershell
docker logs acebuddy-api --tail 50
```

### Issue: No context despite ingestion success
**Solution:** Verify Chroma is persisting data
```powershell
docker logs acebuddy-chroma --tail 50
```

---

## 📊 Test Variations

### Test All 47 Queries (Full Test)
Edit the script and change line:
```powershell
$queriesToTest = @($queries | Select-Object -First 47)
```
Then run. Takes ~5-10 minutes.

### Test Specific Topic
Edit the script to filter by intent:
```powershell
$queriesToTest = @($queries | Where-Object { $_.expected_intent -eq "password_reset" })
```

### Test With Different Wait Time
```powershell
# Quick test (30 seconds)
.\test_chatbot_smoke.ps1 -MaxWaitSeconds 30

# Long wait (120 seconds)
.\test_chatbot_smoke.ps1 -MaxWaitSeconds 120
```

---

## 🛑 Stop Services

After testing, stop Docker Compose:
```powershell
docker-compose down
```

Or keep running for manual testing:
```powershell
# Test with curl/PowerShell directly
$body = @{ query = "I forgot my password"; user_id = "test" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post -Body $body -ContentType "application/json"
```

---

## 📈 Next Steps

**If PASS:**
1. Run full test with all 47 queries
2. Test with real support team queries
3. Measure performance and accuracy
4. Adjust KB content based on feedback
5. Plan production deployment

**If WARNING:**
1. Check logs for errors
2. Verify KB file content: `ls .\data\kb\`
3. Check Chroma data: `docker exec acebuddy-chroma ls /chroma/chroma`
4. Restart services: `docker-compose down; docker-compose up -d`
5. Re-run smoke test

---

## 📝 Notes

- Script requires execution policy bypass for security policy
- Takes 2-5 minutes total (mostly waiting for Docker to start)
- Services remain running after test completes
- Use `docker-compose down` to stop
- Use `docker-compose logs` to debug issues
- Use `docker-compose ps` to check service status

---

**Created:** 2025-11-11  
**Last Updated:** 2025-11-11  
**Status:** Ready for Testing ✅
