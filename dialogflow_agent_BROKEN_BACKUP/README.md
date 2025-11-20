# AceBuddy Dialogflow ES Agent - Complete Package

## 📦 Contents

- **`agent.json`** — Agent metadata (language, timezone, settings)
- **`package.json`** — Package descriptor for Dialogflow import
- **`intents/`** — 13 production-ready intent JSON files with rich training phrases
- **`entities/`** — 3 custom entity files (StoragePlan, Application, IssueType)
- **`README.md`** — This file

## 🎯 Agent Capabilities

This Dialogflow agent handles:

1. **Password Reset** — Collects username, CID, email and creates ticket
2. **Disk Space Upgrade** — Presents storage plans, captures selection, sends to POC
3. **RDP Connection Issues** — Troubleshooting steps for remote desktop
4. **RDP Setup Guide** — Platform-specific connection instructions
5. **User Management** — Add/remove/replace users with full details
6. **QuickBooks Issues** — Troubleshooting for startup, bank feed, performance issues
7. **Server Performance** — Diagnose CPU/RAM/Disk issues with Task Manager guidance
8. **Email Issues** — Outlook and email configuration troubleshooting
9. **Printer Troubleshooting** — Offline, jam, UniPrint setup
10. **Monitor Setup** — Single and multi-monitor configuration for RDP
11. **Application Upgrade** — Process upgrade requests for QB, ProSeries, Drake, etc.
12. **Escalate to Agent** — Human handoff with issue description
13. **Welcome & Fallback** — Greeting and unknown query handling

## 📥 How to Import into Dialogflow ES

### Step 1: Prepare the zip file

1. Navigate to the `dialogflow_agent` folder
2. **Zip the entire contents** (agent.json, package.json, intents/, entities/)
   - On Windows: Right-click folder → Send to → Compressed (zipped) folder
   - Name it: `acebuddy_agent.zip`

### Step 2: Create a new Dialogflow ES agent

1. Go to [Dialogflow Console](https://dialogflow.cloud.google.com/)
2. Click **Create Agent**
3. Name: **AceBuddy**
4. Default language: **English**
5. Default time zone: **Asia/Kolkata** (or your timezone)
6. Click **CREATE**

### Step 3: Import the agent

1. Click the **Settings** gear icon ⚙️ (next to agent name)
2. Go to the **Export and Import** tab
3. Click **IMPORT FROM ZIP**
4. Choose `acebuddy_agent.zip`
5. Type **IMPORT** to confirm
6. Wait for import to complete (30-60 seconds)

### Step 4: Verify the import

1. Go to **Intents** in the left sidebar
2. You should see 13 intents listed
3. Click on **Password Reset** to verify training phrases and parameters
4. Go to **Entities** and confirm StoragePlan, Application, IssueType are present

### Step 5: Test the agent

1. Click on **Try it now** panel (right side)
2. Test queries:
   - "I forgot my password"
   - "My disk is full"
   - "QuickBooks not working"
   - "Talk to an agent"
3. Verify the agent responds correctly and collects required parameters

## 🔧 Optional: Configure Webhook Fulfillment

If you want dynamic responses or backend integration:

1. Deploy `app/dialogflow_fulfillment.py` to Render/Azure/Cloud Run
2. Get your public URL (e.g., `https://your-app.onrender.com/dialogflow/fulfillment`)
3. In Dialogflow Console → **Fulfillment** → Enable **Webhook**
4. Enter webhook URL
5. In each intent, enable **Fulfillment** → **Enable webhook call for this intent**
6. Save and test

## 🌐 Integrate with Zoho SalesIQ

### Option 1: Direct Integration (if supported)

1. Go to Zoho SalesIQ dashboard → **Settings** → **Bots**
2. Click **Add Bot** → **Dialogflow**
3. Enter your Dialogflow project ID and service account JSON
4. Map bot to specific departments/triggers
5. Test in the chat widget

### Option 2: Via Middleware (recommended for custom logic)

1. Deploy a middleware webhook that receives SalesIQ messages
2. Call Dialogflow's `detectIntent` API with the user message
3. Return the bot response to SalesIQ via Zoho API
4. See `app/salesiq_push.py` for helper functions

## 📝 Customization Tips

### Adding More Training Phrases

1. Go to the intent in Dialogflow Console
2. Scroll to **Training phrases**
3. Click **Add training phrases**
4. Type variations of how users might ask
5. Save and retrain

### Modifying Responses

1. Open the intent
2. Scroll to **Responses**
3. Edit the text response
4. Use parameters like `$username` to personalize
5. Add multiple response variations for natural conversation

### Adding New Intents

1. Click **Create Intent**
2. Name it (e.g., "Server Reboot")
3. Add training phrases
4. Add parameters if needed (e.g., server name)
5. Add response text
6. Save

### Entity Management

Entities are in `entities/` folder:
- **StoragePlan**: Disk upgrade options (40GB, 60GB, 80GB, 100GB, 200GB)
- **Application**: Software names (QuickBooks, ProSeries, Drake, Sage, etc.)
- **IssueType**: Common problem categories

To add/modify:
1. Go to **Entities** in Dialogflow
2. Click the entity name
3. Add entries or synonyms
4. Save

## 🚀 Production Readiness

This agent is production-ready with:

✅ Comprehensive training phrases (10+ per intent)
✅ Parameter extraction with prompts
✅ Context handling for multi-turn conversations
✅ Fallback intent for unknown queries
✅ Escalation path to human agents
✅ Rich, formatted responses with emojis
✅ Real-world troubleshooting steps from KB and ticket data

## 📊 Testing Checklist

Before going live:

- [ ] Test all 13 intents with various phrasings
- [ ] Verify parameter collection works (try skipping parameters)
- [ ] Test fallback intent with random queries
- [ ] Test escalation to agent flow
- [ ] Verify responses are clear and helpful
- [ ] Test on actual SalesIQ widget (if integrated)
- [ ] Monitor conversations and add training phrases for missed queries

## 🔍 Troubleshooting

**Import fails:**
- Ensure zip contains agent.json and package.json at root level
- Check that JSON files are valid (no syntax errors)
- Try creating a new agent first, then importing

**Intents not triggering:**
- Add more training phrase variations
- Check for typos in training phrases
- Ensure entities are properly annotated in training phrases

**Parameters not collecting:**
- Verify parameter dataType is correct (@sys.email, @sys.person, etc.)
- Add prompt messages for required parameters
- Test parameter extraction in Test Console

## 📞 Support

For questions or issues with this Dialogflow agent:
- Email: support@acecloudhosting.com
- Phone: +1 (888) 415-5240

## 📄 Version

**Version:** 1.0
**Last Updated:** November 19, 2025
**Built from:** Ace Cloud Hosting KB documents, Zobot flows, and real ticket data
