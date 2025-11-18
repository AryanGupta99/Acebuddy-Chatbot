# 🔗 GET PUBLIC WEBHOOK URL - 3 OPTIONS

## **Option 1: Using ngrok (Easiest - Free)**

### Step 1: Download ngrok
https://ngrok.com/download

### Step 2: Install & Add to PATH
- Extract the file
- Copy `ngrok.exe` to your project folder

### Step 3: Create Tunnel (Terminal 1)
```powershell
# Make sure API is running first:
python app/main.py

# In another terminal, run ngrok:
.\ngrok http 8000
```

### Step 4: Copy the Public URL
You'll see:
```
Session Status: online
Forwarding: https://xxxxx-xx-xx-xx.ngrok.io -> http://localhost:8000
```

**Copy this**: `https://xxxxx-xx-xx-xx.ngrok.io`

### Step 5: Use in SalesIQ
In SalesIQ webhook settings:
```
URL: https://xxxxx-xx-xx-xx.ngrok.io/salesiq/chat
Method: POST
Content-Type: application/json
```

✅ Done!

---

## **Option 2: Using Cloudflare Tunnel (Better - Free)**

### Step 1: Download Cloudflare Tunnel
https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/

### Step 2: Install
```powershell
# Download and install
# Then login
cloudflared login
```

### Step 3: Create Tunnel
```powershell
cloudflared tunnel --url http://localhost:8000
```

You'll get a public URL like:
```
https://xxxxx.trycloudflare.com
```

### Step 4: Use in SalesIQ
```
URL: https://xxxxx.trycloudflare.com/salesiq/chat
```

✅ Done!

---

## **Option 3: Deploy to Real Server (Production)**

### For Testing Only - Not Needed Yet

But when you're ready for production:
- AWS EC2
- DigitalOcean
- Azure
- Heroku
- etc.

---

## **QUICK START (ngrok)**

### Step 1: Terminal 1
```powershell
python app/main.py
```
Wait for: `Uvicorn running on http://0.0.0.0:8000`

### Step 2: Terminal 2
```powershell
.\ngrok http 8000
```

### Step 3: Copy URL
You'll see: `https://xxxxx-xx-xx-xx.ngrok.io`

### Step 4: Use in SalesIQ
```
https://xxxxx-xx-xx-xx.ngrok.io/salesiq/chat
```

### Step 5: Test
```bash
curl https://xxxxx-xx-xx-xx.ngrok.io/salesiq/status
```

---

## **Then in SalesIQ Webhook Settings:**

```
URL: https://your-ngrok-url/salesiq/chat
Method: POST
Content-Type: application/json

Example:
https://a1b2c3d4-xx-xx-xx.ngrok.io/salesiq/chat
```

✅ Click **Test** - should work!

---

## **That's It!**

- **Local testing**: Use ngrok
- **Production**: Deploy to real server
- Both use same API code, just different URL

**ngrok is temporary** (changes each time you restart), but perfect for testing!
