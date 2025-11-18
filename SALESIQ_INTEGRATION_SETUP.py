"""
Integration instructions for adding SalesIQ routes to app/main.py

This file shows exactly what to add to enable SalesIQ integration.
"""

# ==============================================================================
# ADD THIS TO app/main.py (after FastAPI app initialization)
# ==============================================================================

# Around line 80-90, after other imports:
from app.salesiq_integration import add_salesiq_routes

# Then, after creating FastAPI app (around line 100):
app = FastAPI(title="AceBuddy RAG Chatbot", version="2.0.0")

# Add SalesIQ integration routes
add_salesiq_routes(app)

# ==============================================================================
# THAT'S IT! The following endpoints will be available:
# ==============================================================================

"""
✅ NEW ENDPOINTS ADDED:

POST /salesiq/chat
  - Main chat endpoint for SalesIQ
  - Request: {query, visitor_id, chat_id, email, name}
  - Response: {answer, confidence, should_escalate, sources, metadata}

POST /salesiq/webhook
  - Webhook endpoint for incoming SalesIQ messages
  - Receives: {visitor_id, message, chat_id, email, name, phone, department}
  - Returns: Formatted response for SalesIQ chat

GET /salesiq/status
  - Health check endpoint
  - Returns: {status, services, documents_indexed, timestamp}

GET /salesiq/analytics
  - Analytics and metrics
  - Returns: {total_messages, escalations, escalation_rate, top_topics}

POST /salesiq/test
  - Test endpoint for debugging
  - Same request format as /salesiq/chat

POST /salesiq/batch
  - Batch processing endpoint
  - Request: Array of chat requests
  - Response: Array of results

GET /salesiq/config
  - Get integration configuration
  - Returns: Thresholds, feature flags, settings

Interactive API Docs: http://localhost:8000/docs
"""

# ==============================================================================
# STEP-BY-STEP INTEGRATION
# ==============================================================================

def integrate_salesiq():
    """
    Step-by-step guide for integrating SalesIQ
    """
    
    steps = [
        {
            "step": 1,
            "title": "Add import",
            "location": "app/main.py (near top, with other imports)",
            "code": "from app.salesiq_integration import add_salesiq_routes"
        },
        {
            "step": 2,
            "title": "Register routes",
            "location": "app/main.py (after app = FastAPI(...))",
            "code": "add_salesiq_routes(app)"
        },
        {
            "step": 3,
            "title": "Update .env",
            "location": ".env file",
            "code": """
SALESIQ_ENABLED=true
SALESIQ_API_KEY=your-api-key-here
MIN_CONFIDENCE_THRESHOLD=0.7
MIN_QUALITY_THRESHOLD=0.6
"""
        },
        {
            "step": 4,
            "title": "Run setup script",
            "location": "Terminal",
            "code": "python scripts/setup_salesiq.py"
        },
        {
            "step": 5,
            "title": "Test integration",
            "location": "Terminal",
            "code": "curl http://localhost:8000/salesiq/status"
        }
    ]
    
    for step_info in steps:
        print(f"\nStep {step_info['step']}: {step_info['title']}")
        print(f"Location: {step_info['location']}")
        print(f"Code:\n{step_info['code']}")


# ==============================================================================
# COMPLETE EXAMPLE: How to add to main.py
# ==============================================================================

"""
Here's a minimal example of what your main.py should look like:

--- app/main.py ---

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# ✅ ADD THIS IMPORT:
from app.salesiq_integration import add_salesiq_routes

# Load env vars
load_dotenv()

# Create FastAPI app
app = FastAPI(title="AceBuddy RAG Chatbot", version="2.0.0")

# ✅ ADD THIS LINE:
add_salesiq_routes(app)

# ... rest of your code ...

# Routes initialization, etc.
@app.get("/")
async def root():
    return {"message": "AceBuddy RAG Chatbot API", "status": "running"}

@app.get("/health")
async def health_check():
    # ... existing health check code ...
    pass

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # ... existing chat code ...
    pass

# ... rest of your endpoints ...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

--- END ---

That's all you need to do!
"""


# ==============================================================================
# VERIFICATION: Check if integration is working
# ==============================================================================

def verify_salesiq_integration():
    """
    Verify that SalesIQ integration is properly set up
    """
    import requests
    import json
    
    print("🔍 Verifying SalesIQ Integration...\n")
    
    base_url = "http://localhost:8000"
    
    # Check 1: Status endpoint
    try:
        response = requests.get(f"{base_url}/salesiq/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status Endpoint: {data['status']}")
            print(f"   Documents indexed: {data.get('documents_indexed', 'N/A')}")
        else:
            print(f"❌ Status Endpoint: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Status Endpoint: {e}")
    
    # Check 2: Chat endpoint
    try:
        response = requests.post(
            f"{base_url}/salesiq/chat",
            json={
                "query": "Test question",
                "visitor_id": "test_user",
                "chat_id": "test_chat"
            }
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat Endpoint: Working")
            print(f"   Answer: {data['answer'][:100]}...")
            print(f"   Confidence: {data['confidence']:.2f}")
        else:
            print(f"❌ Chat Endpoint: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Chat Endpoint: {e}")
    
    # Check 3: Analytics endpoint
    try:
        response = requests.get(f"{base_url}/salesiq/analytics")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analytics Endpoint: Working")
            print(f"   Total messages: {data['total_messages']}")
            print(f"   Escalation rate: {data['escalation_rate']}")
        else:
            print(f"❌ Analytics Endpoint: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Analytics Endpoint: {e}")
    
    print("\n" + "="*50)
    print("✨ Integration verification complete!")
    print("="*50)


# ==============================================================================
# CONFIGURATION EXAMPLE
# ==============================================================================

"""
When you enable the SalesIQ integration, you get these features:

1. AUTOMATED RESPONSE GENERATION
   - Real-time chat responses powered by RAG
   - Semantic search through knowledge base
   - LLM generation (Ollama or OpenAI)

2. SMART ESCALATION
   - Automatic human handoff for uncertain answers
   - Configurable confidence thresholds
   - Quality-based escalation

3. CONVERSATION CONTINUITY
   - Remembers previous messages in same session
   - Provides context-aware responses
   - Maintains conversation history

4. ANALYTICS & MONITORING
   - Track escalation rates
   - Monitor response quality
   - Identify knowledge gaps
   - See top topics asked

5. FLEXIBLE DEPLOYMENT
   - Works with local Ollama
   - Works with OpenAI API
   - Hybrid approach possible

Configuration Example:

MIN_CONFIDENCE_THRESHOLD = 0.7
├─ Responses above 70% confidence are sent to user
└─ Below 70% are escalated to human

MIN_QUALITY_THRESHOLD = 0.6
├─ Responses scoring above 60% quality are accepted
└─ Below 60% get a disclaimer added

ESCALATION RULES:
├─ Low confidence (< 0.7) → Escalate
├─ Low quality (< 0.6) → Escalate
├─ API errors → Escalate
└─ No matching context → Escalate
"""


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify_salesiq_integration()
    else:
        integrate_salesiq()
