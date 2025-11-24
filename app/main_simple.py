"""
Simplified FastAPI server for webhook testing.
This version avoids problematic imports and provides basic functionality.
"""

from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
from datetime import datetime
import threading
import logging
import json
import requests

app = FastAPI(title="AceBuddy RAG Chatbot (Simple Mode)", version="2.0.0-simple-fixed")

# In-memory last event storage for live debugging (not persisted)
LAST_EVENT = {"inbound": None, "outbound": None}
# Simple request/response models
class ChatRequest(BaseModel):
    query: str
    visitor_id: Optional[str] = None
    chat_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    confidence: float
    should_escalate: bool
    escalation_reason: Optional[str] = None
    sources: list = []
    metadata: dict = {}

class SalesIQChatRequest(BaseModel):
    query: str
    visitor_id: Optional[str] = None
    chat_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None

class SalesIQChatResponse(BaseModel):
    answer: str
    confidence: float
    should_escalate: bool
    escalation_reason: Optional[str] = None
    sources: list = []
    metadata: dict = {}

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "mode": "simple", "timestamp": datetime.now().isoformat()}

# Main chat endpoint
@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint"""
    
    # Simple hardcoded responses for testing
    from fastapi import FastAPI, HTTPException, Request, Body
    from fastapi.responses import JSONResponse
    responses = {
        "greeting": {
            "answer": "Hi! I'm AceBuddy — I can help with password resets, WebDAV access, QuickBooks, and other IT issues. What can I help you with today?",
            "confidence": 0.9,
            "sources": []
        },
        "webdav": {
            "answer": "WebDAV is a protocol for web-based file sharing. You can access shared files through File Explorer by mapping a network drive to the WebDAV server URL. Contact IT support if you need the server address.",
            "confidence": 0.95,
            "sources": ["knowledge_base/webdav_setup.md"]
        },
        "reset": {
            "answer": "To reset your password: 1) Go to the login page and click 'Forgot Password' 2) Enter your email address 3) Check your email for the reset link 4) Follow the link and create a new password.",
            "confidence": 0.98,
            "sources": ["knowledge_base/password_reset.md"]
        },
        "quickbooks": {
            "answer": "QuickBooks is accounting software. For issues, check your connection settings and ensure you have the latest version installed. Common fixes: restart QuickBooks, clear cache, or reinstall if needed.",
            "confidence": 0.85,
            "sources": ["knowledge_base/quickbooks.md"]
        },
        "default": {
            "answer": "I'm here to help! You can ask me about password resets, WebDAV access, QuickBooks, remote apps, and other technical issues. What would you like help with?",
            "confidence": 0.7,
            "sources": []
        }
    }
    
    # Determine which response to use
    query_lower = request.query.lower()
    response_key = "default"

    # greeting detection: handle short greetings like hi/hello/hey first
    greetings = ("hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings")
    if any(g in query_lower for g in greetings) and len((query_text or "").strip()) < 40:
        response_key = "greeting"
    elif any(word in query_lower for word in ["webdav", "web dav", "file share"]):
        response_key = "webdav"
    elif any(word in query_lower for word in ["password", "reset", "login"]):
        response_key = "reset"
    elif any(word in query_lower for word in ["quickbooks", "qb", "accounting"]):
        response_key = "quickbooks"
    
    resp = responses[response_key]
    
    return ChatResponse(
        answer=resp["answer"],
        confidence=resp["confidence"],
        should_escalate=resp["confidence"] < 0.7,
        escalation_reason="Low confidence" if resp["confidence"] < 0.7 else None,
        sources=resp["sources"],
        metadata={
            "visitor_id": request.visitor_id,
            "chat_id": request.chat_id,
            "email": request.email,
            "name": request.name,
            "timestamp": datetime.now().isoformat()
        }
    )

# SalesIQ webhook endpoint
@app.post("/salesiq/chat")
async def salesiq_chat(request: Request):
    """SalesIQ webhook endpoint (robust parsing for JSON/form shapes)"""
    # Read incoming body robustly (JSON -> form -> raw)
    body = None
    try:
        body = await request.json()
    except Exception:
        try:
            form = await request.form()
            body = {k: v for k, v in form.items()}
        except Exception:
            try:
                raw = await request.body()
                body_text = raw.decode('utf-8', errors='ignore')
                body = json.loads(body_text)
            except Exception:
                body = {}

    # Log raw payload for inspection
    try:
        os.makedirs('logs', exist_ok=True)
        with open('logs/salesiq_events.log', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.utcnow().isoformat()} - {json.dumps(body)}\n")
    except Exception:
        pass

    # primary candidate
    query_text = None
    if isinstance(body, dict):
        query_text = body.get('query') or body.get('message') or body.get('text')

    query_lower = (query_text or '').lower()

    responses = {
        "webdav": {
            "answer": "WebDAV is a protocol for web-based file sharing. You can access shared files through File Explorer by mapping a network drive to the WebDAV server URL. Contact IT support if you need the server address.",
            "confidence": 0.95,
            "sources": ["knowledge_base/webdav_setup.md"]
        },
        "reset": {
            "answer": "To reset your password: 1) Go to the login page and click 'Forgot Password' 2) Enter your email address 3) Check your email for the reset link 4) Follow the link and create a new password.",
            "confidence": 0.98,
            "sources": ["knowledge_base/password_reset.md"]
        },
        "quickbooks": {
            "answer": "QuickBooks is accounting software. For issues, check your connection settings and ensure you have the latest version installed. Common fixes: restart QuickBooks, clear cache, or reinstall if needed.",
            "confidence": 0.85,
            "sources": ["knowledge_base/quickbooks.md"]
        },
        "default": {
            "answer": "I'm here to help! You can ask me about password resets, WebDAV access, QuickBooks, remote apps, and other technical issues. What would you like help with?",
            "confidence": 0.7,
            "sources": []
        }
    }
    
    response_key = "default"
    
    if any(word in query_lower for word in ["webdav", "web dav", "file share"]):
        response_key = "webdav"
    elif any(word in query_lower for word in ["password", "reset", "login"]):
        response_key = "reset"
    elif any(word in query_lower for word in ["quickbooks", "qb", "accounting"]):
        response_key = "quickbooks"
    
    resp = responses[response_key]
    # Build the response object
    answer = resp["answer"]
    confidence = resp["confidence"]
    should_escalate = confidence < 0.7

    # Synchronous response payload for Zobot
    sync_payload = {
        "message": answer,
        "type": "text",
        "metadata": {
            "confidence": confidence,
            "sources": resp.get('sources', [])
        }
    }

    # Asynchronously push to Zoho SalesIQ conversation (if credentials present)
    def _async_push():
        try:
            SALESIQ_API_BASE = os.getenv('SALESIQ_API_BASE')
            SALESIQ_ACCESS_TOKEN = os.getenv('SALESIQ_ACCESS_TOKEN')
            conv_id = getattr(request, 'chat_id', None) or getattr(request, 'conversation_id', None) or getattr(request, 'chat_id', None)
            if not SALESIQ_API_BASE or not SALESIQ_ACCESS_TOKEN or not conv_id:
                # Nothing to do when no credentials or conversation id
                return
            headers = {
                'Authorization': f'Zoho-oauthtoken {SALESIQ_ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                'type': 'message',
                'source': 'bot',
                'message': answer,
                'metadata': {
                    'confidence': confidence,
                    'sources': resp.get('sources', [])
                }
            }
            # Best-effort: POST to conversations/{conv_id}/messages (placeholder path)
            url = f"{SALESIQ_API_BASE.rstrip('/')}/conversations/{conv_id}/messages"
            r = requests.post(url, headers=headers, json=payload, timeout=8)
            if r.status_code >= 400:
                logging.warning(f"Zoho push failed: {r.status_code} {r.text}")
        except Exception as e:
            logging.warning(f"Zoho push exception: {e}")

    try:
        t = threading.Thread(target=_async_push, daemon=True)
        t.start()
    except Exception:
        pass

    # Build response object (mirror prior SalesIQChatResponse structure)
    response_obj = {
        "answer": answer,
        "confidence": confidence,
        "should_escalate": should_escalate,
        "escalation_reason": "Low confidence" if should_escalate else None,
        "sources": resp.get('sources', []),
        "metadata": {
            "visitor_id": body.get('visitor_id'),
            "chat_id": body.get('chat_id'),
            "email": body.get('email'),
            "name": body.get('name'),
            "timestamp": datetime.now().isoformat(),
            "integration": "salesiq",
            "sync_payload": sync_payload
        }
    }

    # Save last event for live debugging
    try:
        LAST_EVENT['inbound'] = body
        LAST_EVENT['outbound'] = response_obj
    except Exception:
        pass

    return JSONResponse(content=response_obj)


# Zobot third-party webhook endpoint
@app.get("/zobot/webhook")
def zobot_webhook_info():
    """Informational GET for the Zobot webhook URL.
    Browsers or humans hitting the webhook URL will see this helpful note
    instead of a 405. The actual webhook should POST JSON to this endpoint.
    """
    return {
        "info": "This endpoint accepts POST requests from Zoho Zobot. Use POST /zobot/webhook with JSON body {'message': '<text>'} and optionally ?sync=true or header X-Zobot-Sync:true for synchronous replies."
    }


@app.post("/zobot/webhook")
async def zobot_webhook(request: Request):
    """Endpoint to receive Zobot webhook calls from Zoho SalesIQ.
    - If caller expects a synchronous Zobot response, include header `X-Zobot-Sync: true` or query `?sync=true`.
    - Otherwise the endpoint will return a quick ack and push the final message asynchronously when credentials exist.
    This handler reads JSON and form bodies robustly and records last event in memory.
    """
    # Read incoming body robustly (JSON -> form -> raw)
    body = None
    try:
        body = await request.json()
    except Exception:
        try:
            form = await request.form()
            body = {k: v for k, v in form.items()}
        except Exception:
            try:
                raw = await request.body()
                body_text = raw.decode('utf-8', errors='ignore')
                body = json.loads(body_text)
            except Exception:
                body = {}

    # Log raw payload for debugging
    try:
        os.makedirs('logs', exist_ok=True)
        with open('logs/salesiq_events.log', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.utcnow().isoformat()} - {json.dumps(body)}\n")
    except Exception:
        pass

    # Extract text from common Zobot shapes
    query_text = None
    try:
        if isinstance(body, dict):
            # prioritized keys
            for key in ('message', 'text', 'userMessage', 'visitorMessage', 'query'):
                v = body.get(key)
                if isinstance(v, str) and v.strip():
                    query_text = v.strip()
                    break

            # nested patterns
            if not query_text and 'data' in body and isinstance(body['data'], dict):
                for key in ('message', 'text'):
                    v = body['data'].get(key)
                    if isinstance(v, str) and v.strip():
                        query_text = v.strip(); break

            # last resort: search for likely keys
            if not query_text:
                for k, v in body.items():
                    if isinstance(v, str) and any(w in k.lower() for w in ('message', 'text', 'query')):
                        query_text = v.strip()
                        break
    except Exception:
        query_text = None

    # reuse existing simple matching logic
    query_lower = (query_text or '').lower()
    response_key = "default"

    # Check specific intents FIRST before greeting (so "how to reset password" doesn't match "hii" in greeting)
    if any(word in query_lower for word in ["webdav", "web dav", "file share"]):
        response_key = "webdav"
    elif any(word in query_lower for word in ["password", "reset", "login"]):
        response_key = "reset"
    elif any(word in query_lower for word in ["quickbooks", "qb", "accounting"]):
        response_key = "quickbooks"
    elif any(g in query_lower for g in ("hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings", "hii")):
        # Only treat as greeting if it's a pure greeting (short length)
        if len((query_text or "").strip()) < 20:
            response_key = "greeting"

    # pull response map from existing code block
    responses = {
        "greeting": {
            "answer": "Hi! I'm AceBuddy — I can help with password resets, WebDAV access, QuickBooks, and other IT issues. What can I help you with today?",
            "confidence": 0.9,
            "sources": []
        },
        "webdav": {
            "answer": "WebDAV is a protocol for web-based file sharing. You can access shared files through File Explorer by mapping a network drive to the WebDAV server URL. Contact IT support if you need the server address.",
            "confidence": 0.95,
            "sources": ["knowledge_base/webdav_setup.md"]
        },
        "reset": {
            "answer": "To reset your password: 1) Go to the login page and click 'Forgot Password' 2) Enter your email address 3) Check your email for the reset link 4) Follow the link and create a new password.",
            "confidence": 0.98,
            "sources": ["knowledge_base/password_reset.md"]
        },
        "quickbooks": {
            "answer": "QuickBooks is accounting software. For issues, check your connection settings and ensure you have the latest version installed. Common fixes: restart QuickBooks, clear cache, or reinstall if needed.",
            "confidence": 0.85,
            "sources": ["knowledge_base/quickbooks.md"]
        },
        "default": {
            "answer": "I'm here to help! You can ask me about password resets, WebDAV access, QuickBooks, remote apps, and other technical issues. What would you like help with?",
            "confidence": 0.7,
            "sources": []
        }
    }

    resp = responses.get(response_key, responses['default'])
    answer = resp['answer']
    confidence = resp['confidence']

    # Build Zobot synchronous payload (the widget can accept this when configured)
    sync_payload = {
        "message": answer,
        "type": "text",
        "metadata": {
            "confidence": confidence,
            "sources": resp.get('sources', []),
            "version": "2.0.1-greeting"
        }
    }

    # If the request wants immediate synchronous display, return the sync payload directly
    query_params = dict(request.query_params)
    want_sync = (query_params.get('sync') == 'true') or (request.headers.get('X-Zobot-Sync', '').lower() == 'true')

    # allow an alternate response shape if the caller expects an array of messages
    expect_messages_array = (query_params.get('format') == 'messages') or (request.headers.get('X-Zobot-Expect', '').lower() == 'messages')

    # Async push to Zoho conversation if credentials present (same pattern as salesiq_chat)
    def _async_push_zobot(conv_id=None):
        try:
            SALESIQ_API_BASE = os.getenv('SALESIQ_API_BASE')
            SALESIQ_ACCESS_TOKEN = os.getenv('SALESIQ_ACCESS_TOKEN')
            conv = conv_id or (body.get('conversation_id') if isinstance(body, dict) else None)
            if not SALESIQ_API_BASE or not SALESIQ_ACCESS_TOKEN or not conv:
                return
            headers = {
                'Authorization': f'Zoho-oauthtoken {SALESIQ_ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                'type': 'message',
                'source': 'bot',
                'message': answer,
                'metadata': sync_payload['metadata']
            }
            url = f"{SALESIQ_API_BASE.rstrip('/')}/conversations/{conv}/messages"
            r = requests.post(url, headers=headers, json=payload, timeout=8)
            if r.status_code >= 400:
                logging.warning(f"Zoho push failed: {r.status_code} {r.text}")
        except Exception as e:
            logging.warning(f"Zoho push exception: {e}")

    # Start async push unless caller asked for synchronous behavior only
    if not want_sync:
        try:
            conv_id = body.get('conversation_id') if isinstance(body, dict) else None
            t = threading.Thread(target=_async_push_zobot, args=(conv_id,), daemon=True)
            t.start()
        except Exception:
            pass

    if want_sync:
        # Log the outgoing synchronous payload so we can inspect what the widget receives
        try:
            os.makedirs('logs', exist_ok=True)
            with open('logs/salesiq_responses.log', 'a', encoding='utf-8') as rf:
                rf.write(f"{datetime.utcnow().isoformat()} - response: {json.dumps(sync_payload)} - headers: {json.dumps(dict(request.headers))}\n")
        except Exception:
            pass

        # OFFICIAL ZOHO ZOBOT RESPONSE FORMAT (from Zoho docs):
        # {
        #   "action": "reply",
        #   "replies": ["message1", {"text": "message2", "image": "url"}],
        #   "suggestions": ["suggestion1", "suggestion2"]
        # }
        
        zoho_response = {
            "action": "reply",
            "replies": [answer]
        }

        # log the response for debugging
        try:
            os.makedirs('logs', exist_ok=True)
            with open('logs/salesiq_responses.log', 'a', encoding='utf-8') as rf:
                rf.write(f"{datetime.utcnow().isoformat()} - returning official zoho format: {json.dumps(zoho_response)}\n")
            with open('logs/salesiq_events.log', 'a', encoding='utf-8') as ef:
                ef.write(f"{datetime.utcnow().isoformat()} - outgoing: {json.dumps(zoho_response)}\n")
        except Exception:
            pass

        # Save last event for live debugging
        try:
            LAST_EVENT['inbound'] = body
            LAST_EVENT['outbound'] = zoho_response
        except Exception:
            pass

        return JSONResponse(content=zoho_response, media_type="application/json")

    # Otherwise return an ack that the webhook was received
    return JSONResponse(content={"status": "accepted", "message": "Processing"}, status_code=202)

# SalesIQ status endpoint
@app.get("/salesiq/status")
def salesiq_status():
    """SalesIQ status endpoint"""
    return {
        "status": "operational",
        "mode": "simple",
        "services": {
            "chat": "active",
            "embeddings": "dummy",
            "vector_db": "offline"
        },
        "documents_indexed": 100,
        "timestamp": datetime.now().isoformat()
    }

# SalesIQ analytics endpoint
@app.get("/salesiq/analytics")
def salesiq_analytics():
    """SalesIQ analytics endpoint"""
    return {
        "total_messages": 42,
        "escalations": 8,
        "escalation_rate": 0.19,
        "top_topics": ["password_reset", "webdav_access", "quickbooks_issues"],
        "average_confidence": 0.84,
        "timestamp": datetime.now().isoformat()
    }

# Root endpoint
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": "AceBuddy RAG Chatbot",
        "version": "2.0.0-simple",
        "mode": "simple (no LLM)",
        "docs": "/docs",
        "status": "/health",
        "endpoints": {
            "chat": "POST /chat",
            "salesiq_chat": "POST /salesiq/chat",
            "salesiq_status": "GET /salesiq/status",
            "salesiq_analytics": "GET /salesiq/analytics"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("ACEBUDDY RAG - SIMPLE API SERVER")
    print("="*70)
    print("\n✓ Starting API server on http://localhost:8000")
    print("\n📌 Available endpoints:")
    print("   GET  http://localhost:8000/ (API Info)")
    print("   GET  http://localhost:8000/health (Health Check)")
    print("   GET  http://localhost:8000/docs (Swagger Documentation)")
    print("   POST http://localhost:8000/chat (Main Chat Endpoint)")
    print("   POST http://localhost:8000/salesiq/chat (SalesIQ Webhook)")
    print("   GET  http://localhost:8000/salesiq/status (Status Check)")
    print("   GET  http://localhost:8000/salesiq/analytics (Analytics)")
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Debug echo endpoint to help inspect headers + body from SalesIQ/Zobot test calls
@app.post("/debug/echo")
async def debug_echo(request: Request):
    try:
        # capture headers
        headers = {k: v for k, v in request.headers.items()}
        # try JSON first
        try:
            body = await request.json()
        except Exception:
            try:
                form = await request.form()
                body = {k: v for k, v in form.items()}
            except Exception:
                body = await request.body()
                try:
                    body = body.decode('utf-8')
                except Exception:
                    pass
        return JSONResponse(content={"headers": headers, "body": body})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get('/internal/last_event')
def internal_last_event():
    """Return last inbound/outbound payload seen by the webhook (use for live debugging)."""
    return LAST_EVENT
