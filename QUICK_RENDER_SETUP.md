# Deploy AceBuddy RAG Webhook to Render.com

## What You Need
- GitHub account (free)
- Render account (free, no credit card for first month)
- This repository pushed to GitHub

## Deploy in 5 Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "AceBuddy RAG SalesIQ webhook integration"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/AceBuddy-RAG.git
git push -u origin main
```

### 2. Go to Render
- Visit https://render.com
- Sign up (GitHub recommended)

### 3. Create New Web Service
- Click **"New +"** → **"Web Service"**
- Select your GitHub repo
- Click **"Connect"**

### 4. Configure
```
Name:              acebuddy-rag-webhook
Runtime:           Docker
Region:            Oregon (or nearest)
Plan:              Free
```

### 5. Add Environment Variables
In Render dashboard **Environment** section:
```
SALESIQ_ACCESS_TOKEN = (leave empty for now)
SALESIQ_API_BASE = https://www.zohoapis.com
```

Click **"Create Web Service"** and wait 3-5 minutes.

---

## Your Public URL
Once deployed, Render gives you a URL like:
```
https://acebuddy-rag-webhook-xxxxx.onrender.com
```

## Your SalesIQ Webhook URL
```
https://acebuddy-rag-webhook-xxxxx.onrender.com/salesiq/chat
```

Use this in **Zoho SalesIQ** → **Settings** → **Webhooks** → **Add Webhook**

---

**Status**: Ready to deploy. Need help? Reply with your GitHub username and I'll help with the git setup.
