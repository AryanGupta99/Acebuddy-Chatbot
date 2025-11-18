# 🧪 LOCAL SALESIQ WEBHOOK TEST - SIMPLE GUIDE

## **How to Test Locally**

### **Step 1: Start Your API** (Terminal 1)
```powershell
python app/main.py
```
Wait for: `Uvicorn running on http://0.0.0.0:8000`

### **Step 2: Run Test Script** (Terminal 2)
```powershell
python test_salesiq_local.py
```

### **What It Does**
✅ Checks if API is running  
✅ Tests 5 sample questions  
✅ Shows confidence scores  
✅ Shows if response should escalate  
✅ Displays sources found  
✅ Tests batch processing  
✅ Shows analytics  

### **Expected Output**
```
✅ API is running!
✅ SalesIQ integration ready!
✅ Response received
   Confidence: 85.00%
   Escalate: No ✓
   Answer: To reset your password...
   Sources: 3 found
```

---

## **Sample Test Queries Included**

1. **"How do I reset my password?"**
   - Should have high confidence ✅

2. **"How to connect WebDAV on Windows?"**
   - Should find PDF chunks (76%+ confidence) ✅

3. **"How to setup email in QuickBooks?"**
   - Should have high confidence ✅

4. **"How to export reports from QuickBooks?"**
   - Should have good confidence ✅

5. **"Unknown topic that should escalate"**
   - Should escalate to human ⚠️

---

## **What Each Test Shows**

| Test | What It Checks |
|------|----------------|
| Health Check | API is running |
| SalesIQ Status | 100 documents indexed |
| Single Queries | Answer quality & confidence |
| Batch | Multiple queries at once |
| Analytics | Message tracking |

---

## **If Tests Pass ✅**

Then you're ready to:
1. Configure webhook in actual SalesIQ
2. Create bot flow
3. Go live!

---

## **If Tests Fail ❌**

Check:
1. Is API running? `python app/main.py`
2. Is port 8000 accessible?
3. Check logs for errors
4. Verify .env has OPENAI_API_KEY

---

## **Quick Test Commands** (Manual)

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

### Test 2: SalesIQ Status
```bash
curl http://localhost:8000/salesiq/status
```

### Test 3: Single Chat Query
```bash
curl -X POST http://localhost:8000/salesiq/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"How to reset password?\",\"visitor_id\":\"test\",\"chat_id\":\"test\"}"
```

---

## **That's It!**

Run the test script and see if it works. All green = ready for production!
