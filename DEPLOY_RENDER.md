**Deploying AceBuddy RAG (simple) to Render**

This file shows quick steps to deploy the `app/main_simple.py` service to Render using the included `Dockerfile` and `render.yaml`.

Steps (GUI):
1. Create a Render account (https://render.com) and connect your GitHub repository.
2. In Render dashboard choose "New" → "Web Service" → "Deploy from a repository".
3. Select this repository and the `main` branch.
4. For the environment select `Docker` (Render detects `Dockerfile`).
5. Set environment variables (in the Render UI):
   - `SALESIQ_API_BASE` = (your Zoho API base, e.g. https://www.zohoapis.com)
   - `SALESIQ_ACCESS_TOKEN` = (your Zoho OAuth access token) — leave empty for now if you only need synchronous Zobot replies.
6. Deploy. Render will build the Docker image and provide an HTTPS URL such as `https://acebuddy-rag.onrender.com`.

Steps (CLI using render.yaml):
1. Install `render` CLI (optional) and authenticate: `curl https://api.render.com/cli/install.sh | bash` (see Render docs).
2. Push your changes to `main` and then create the service from the Render dashboard by importing the repo which includes `render.yaml`, or use the Render web UI.

Testing the deployed endpoint

Health:
```powershell
Invoke-RestMethod -Uri 'https://<your-render-service>/health' -Method GET
```

Zobot synchronous test:
```powershell
#$body = @{ message = 'How do I reset my password?'; conversation_id = 'conv1' } | ConvertTo-Json -Depth 6
Invoke-RestMethod -Uri 'https://<your-render-service>/zobot/webhook?sync=true' -Method POST -ContentType 'application/json' -Body $body
```

Notes
- Do NOT commit secret tokens to this repository. Set them in Render environment variables.
- For production, wire proper OAuth refresh token flow for `SALESIQ_ACCESS_TOKEN` and add request verification for incoming webhooks.
