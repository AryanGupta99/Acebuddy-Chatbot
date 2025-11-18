# AceBuddy RAG - Render Deployment Guide

## Quick Deploy to Render (5 minutes)

### Step 1: Create a Render Account
1. Go to https://render.com
2. Sign up with GitHub or email (free account, no credit card)

### Step 2: Connect Your GitHub Repo
1. In Render dashboard, click **"New +"** → **"Web Service"**
2. Select **"Build and deploy from a Git repository"**
3. Connect your GitHub account (or upload this repo as a new repo)
4. Select the AceBuddy-RAG repository

### Step 3: Configure Deployment
Render will auto-detect the Dockerfile. Set these values:

| Field | Value |
|-------|-------|
| **Name** | `acebuddy-rag-webhook` |
| **Runtime** | `Docker` |
| **Region** | `Oregon` (or closest to you) |
| **Plan** | `Free` |
| **Build Command** | *(leave blank, uses Dockerfile)* |
| **Start Command** | *(leave blank, uses Dockerfile CMD)* |

### Step 4: Add Environment Variables
In the **Environment** section, add:

```
SALESIQ_ACCESS_TOKEN = <your-zoho-oauth-token>
SALESIQ_API_BASE = https://www.zohoapis.com
```

*(If you don't have `SALESIQ_ACCESS_TOKEN` yet, leave it empty — the webhook will still work in dry-run mode.)*

### Step 5: Deploy
Click **"Create Web Service"** — Render will:
1. Clone your repo
2. Build the Docker image
3. Deploy to a public URL

**⏳ Takes 3-5 minutes.** Once done, you'll see a URL like:
```
https://acebuddy-rag-webhook-xxxx.onrender.com
```

### Your Public Webhook URL
Once deployed, your SalesIQ webhook URL is:

```
https://acebuddy-rag-webhook-xxxx.onrender.com/salesiq/chat
```

## Test the Webhook (from SalesIQ Dashboard)

1. Go to **Zoho SalesIQ** → **Settings** → **Webhooks**
2. Click **"Add Webhook"**
3. Paste the public URL: `https://acebuddy-rag-webhook-xxxx.onrender.com/salesiq/chat`
4. Method: `POST`
5. Headers: `Content-Type: application/json`
6. Event: `Message Received` (or equivalent)
7. Click **"Test Connection"** — should see **200 OK** with response

## Logs & Debugging

In Render dashboard:
1. Go to your service
2. Click **"Logs"** tab
3. You'll see real-time logs from the API

If you see errors, check:
- Dependencies in `requirements.txt`
- Environment variables set correctly
- Dockerfile is valid (Python version, CMD syntax)

## Scaling & Upgrade

Once you validate the webhook works:
1. Upgrade to **Paid** plan for better uptime and performance
2. Set up your Zoho OAuth token (get from Zoho account settings)
3. Enable real Zoho API push (currently in dry-run mode without token)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| **Build fails** | Check Dockerfile syntax, ensure all files exist |
| **Deploy takes >10min** | Cancel and redeploy (usually just slow first build) |
| **Webhook returns 500** | Check **Logs** tab in Render for Python errors |
| **Webhook returns 404** | Verify exact URL: `/salesiq/chat` not `/salesiq/chatt` |

---

**Need help?** Reply with the Render deployment URL after Step 5 and I'll test the webhook with you.
