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
import glob
import re

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


# Helper: simple KB search over files in data/kb/
def kb_search(query: str, kb_dir: str = 'data/kb', min_score: int = 2):
    if not query:
        return None
    try:
        query_tokens = set(re.findall(r"\w+", query.lower()))
        best = (None, 0, None)  # (filename, score, excerpt)
        pattern = re.compile(r"\w+")
        for path in glob.glob(os.path.join(kb_dir, '*.md')):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
                tokens = set(pattern.findall(text.lower()))
                score = len(query_tokens & tokens)
                if score > best[1]:
                    excerpt = text.strip().replace('\n', ' ')
                    if len(excerpt) > 800:
                        excerpt = excerpt[:800] + '...'
                    best = (os.path.basename(path), score, excerpt)
            except Exception:
                continue
        if best[1] >= min_score:
            return { 'file': best[0], 'score': best[1], 'excerpt': best[2] }
    except Exception:
        return None
    return None


# Helper: call LLM (OpenAI) if key present. Returns text or None
def call_llm(query: str, system_prompt: str = None):
    key = os.getenv('OPENAI_API_KEY')
    if not key or not query:
        return None
    try:
        headers = {
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
        model = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
        system_msg = system_prompt or 'You are a helpful IT assistant. Answer concisely.'
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_msg},
                {'role': 'user', 'content': query}
            ],
            'temperature': 0.2,
            'max_tokens': 512
        }
        r = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            j = r.json()
            choices = j.get('choices') or []
            if choices:
                return choices[0].get('message', {}).get('content')
    except Exception:
        return None
    return None


# Helper: escalate to human by posting to SalesIQ conversation (best-effort async)
def escalate_to_human(body: dict, note: str = None):
    try:
        SALESIQ_API_BASE = os.getenv('SALESIQ_API_BASE')
        SALESIQ_ACCESS_TOKEN = os.getenv('SALESIQ_ACCESS_TOKEN')
        conv = None
        if isinstance(body, dict):
            conv = body.get('conversation_id') or body.get('visitor', {}).get('active_conversation_id')
        if not SALESIQ_API_BASE or not SALESIQ_ACCESS_TOKEN or not conv:
            return False
        headers = {
            'Authorization': f'Zoho-oauthtoken {SALESIQ_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }
        payload = {
            'type': 'message',
            'source': 'bot',
            'message': note or 'Escalating to human agent',
            'metadata': {
                'escalation': True,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        url = f"{SALESIQ_API_BASE.rstrip('/')}/conversations/{conv}/messages"
        try:
            requests.post(url, headers=headers, json=payload, timeout=6)
        except Exception:
            pass
        return True
    except Exception:
        return False

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

    # Log raw payload for debugging WITH ALL KEYS
    try:
        os.makedirs('logs', exist_ok=True)
        # Log ALL keys in the payload for inspection
        all_keys = list(body.keys()) if isinstance(body, dict) else []
        debug_log = f"{datetime.utcnow().isoformat()} - PAYLOAD_DEBUG: keys={all_keys}, full={json.dumps(body)}\n"
        with open('logs/salesiq_events.log', 'a', encoding='utf-8') as f:
            f.write(debug_log)
    except Exception:
        pass

    # Extract text from common Zobot shapes - EXPANDED to check MORE keys
    query_text = None
    try:
        if isinstance(body, dict):
            # EXPANDED: Check ALL string keys in the payload
            for key in ('message', 'text', 'userMessage', 'visitorMessage', 'query', 'user_message', 'visitor_message', 'msg', 'content', 'input', 'user_input', 'question', 'intent_text', 'incoming_message'):
                v = body.get(key)
                if isinstance(v, str) and v.strip():
                    query_text = v.strip()
                    break

            # nested patterns - check MORE nested keys
            if not query_text and 'data' in body and isinstance(body['data'], dict):
                for key in ('message', 'text', 'content', 'input', 'query'):
                    v = body['data'].get(key)
                    if isinstance(v, str) and v.strip():
                        query_text = v.strip(); break

            # check 'request' nested object (common in Zobot)
            if not query_text and 'request' in body and isinstance(body['request'], dict):
                for key in ('message', 'text', 'input', 'query'):
                    v = body['request'].get(key)
                    if isinstance(v, str) and v.strip():
                        query_text = v.strip(); break

            # check 'message' as nested object
            if not query_text and 'message' in body and isinstance(body['message'], dict):
                for key in ('text', 'content', 'input'):
                    v = body['message'].get(key)
                    if isinstance(v, str) and v.strip():
                        query_text = v.strip(); break

            # last resort: search for likely keys (ANY string-like value with text-related key name)
            if not query_text:
                for k, v in body.items():
                    if isinstance(v, str) and any(w in k.lower() for w in ('message', 'text', 'query', 'content', 'input', 'msg')):
                        query_text = v.strip()
                        break
    except Exception as e:
        query_text = None

    # reuse existing simple matching logic
    query_lower = (query_text or '').lower()
    response_key = "default"

    # Log what we extracted for debugging
    try:
        os.makedirs('logs', exist_ok=True)
        extraction_log = f"{datetime.utcnow().isoformat()} - EXTRACTION: query_text='{query_text}' query_lower='{query_lower}'\n"
        with open('logs/salesiq_events.log', 'a', encoding='utf-8') as f:
            f.write(extraction_log)
    except Exception:
        pass

    # Check specific intents FIRST before greeting
    if any(word in query_lower for word in ["webdav", "web dav", "file share", "map network", "network drive"]):
        response_key = "webdav"
    elif any(word in query_lower for word in ["password", "reset", "login", "forgot", "change password"]):
        response_key = "reset"
    elif any(word in query_lower for word in ["quickbooks", "qb", "accounting", "invoice", "payroll"]):
        response_key = "quickbooks"
    elif any(word in query_lower for word in ["printer", "print", "printing", "paper", "ink", "toner", "hp", "canon", "xerox"]):
        response_key = "printer"
    elif any(word in query_lower for word in ["rdp", "remote desktop", "connect", "connection", "access remote"]):
        response_key = "rdp"
    elif any(word in query_lower for word in ["disk", "storage", "space", "hard drive", "ssd", "upgrade"]):
        response_key = "disk"
    elif any(g in query_lower for g in ("hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings", "hii", "hiii")):
        # Greeting detection
        response_key = "greeting"

    # Log which response was chosen
    try:
        os.makedirs('logs', exist_ok=True)
        intent_log = f"{datetime.utcnow().isoformat()} - INTENT: response_key='{response_key}'\n"
        with open('logs/salesiq_events.log', 'a', encoding='utf-8') as f:
            f.write(intent_log)
    except Exception:
        pass

    # pull response map from existing code block
    responses = {
        "greeting": {
            "answer": "Hi! I'm AceBuddy — I can help with password resets, WebDAV access, QuickBooks, printer issues, remote desktop, storage upgrades, and other IT issues. What can I help you with today?",
            "confidence": 0.9,
            "sources": []
        },
        "webdav": {
            "answer": "WebDAV is a protocol for web-based file sharing. You can access shared files through File Explorer by mapping a network drive to the WebDAV server URL. Contact IT support if you need the server address.",
            "confidence": 0.95,
            "sources": ["knowledge_base/webdav_setup.md"]
        },
        "reset": {
            "answer": "To reset your password: 1) Go to the login page and click 'Forgot Password' 2) Enter your email address 3) Check your email for the reset link 4) Follow the link and create a new password. If you don't receive the email, check your spam folder or contact IT support.",
            "confidence": 0.98,
            "sources": ["knowledge_base/password_reset.md"]
        },
        "quickbooks": {
            "answer": "QuickBooks is accounting software. For issues, check your connection settings and ensure you have the latest version installed. Common fixes: restart QuickBooks, clear cache, or reinstall if needed. Contact IT support for further assistance.",
            "confidence": 0.85,
            "sources": ["knowledge_base/quickbooks.md"]
        },
        "printer": {
            "answer": "To troubleshoot printer issues: 1) Check if the printer is powered on and connected to the network 2) Clear any paper jams 3) Check for error messages on the printer display 4) Reinstall or update printer drivers from the manufacturer's website 5) Restart both the printer and your computer. If the issue persists, contact IT support.",
            "confidence": 0.85,
            "sources": ["knowledge_base/printer_troubleshooting.md"]
        },
        "rdp": {
            "answer": "Remote Desktop Protocol (RDP) allows you to connect to remote computers. To connect: 1) Use Remote Desktop Connection on Windows 2) Enter the computer name or IP address 3) Enter your credentials 4) Click Connect. If you have connection issues, ensure the remote computer is powered on and networked, and contact IT support.",
            "confidence": 0.80,
            "sources": ["knowledge_base/rdp_connection.md"]
        },
        "disk": {
            "answer": "To manage disk storage: 1) Check available space in File Explorer > This PC 2) Delete unnecessary files or move them to external storage 3) Empty the Recycle Bin 4) Run Disk Cleanup (search for it in Windows) 5) Consider upgrading to a larger drive. Contact IT support if you need help with storage upgrades.",
            "confidence": 0.80,
            "sources": ["knowledge_base/disk_storage.md"]
        },
        "default": {
            "answer": "I'm here to help! You can ask me about password resets, WebDAV access, QuickBooks, printer troubleshooting, remote desktop, storage upgrades, and other IT issues. What would you like help with?",
            "confidence": 0.7,
            "sources": []
        }

    }

    # Base response from canned intents (if matched)
    resp = responses.get(response_key, responses['default'])
    answer = resp['answer']
    confidence = resp['confidence']

    # PIPELINE: 1) Zobot node mapping -> 2) canned intent -> 3) KB search -> 4) LLM -> 5) escalate
    # 1) Check for explicit Zobot node mapping file (optional)
    node_reply = None
    try:
        node_id = None
        if isinstance(body, dict):
            node_id = body.get('node') or (body.get('request') or {}).get('node_id') or (body.get('request') or {}).get('node')
            # fallback to handler name
            if not node_id:
                node_id = body.get('handler')
        nodes_map_path = os.path.join('data', 'zobot_nodes.json')
        if node_id and os.path.exists(nodes_map_path):
            try:
                with open(nodes_map_path, 'r', encoding='utf-8') as nf:
                    nodes_map = json.load(nf)
                # nodes_map expected to be {"node_identifier": "reply text"}
                node_reply = nodes_map.get(str(node_id))
            except Exception:
                node_reply = None
    except Exception:
        node_reply = None

    if node_reply:
        answer = node_reply
        confidence = 0.95
        resp_sources = [f'zobot_node:{node_id}']
    else:
        # 2) If canned intent matched (not default), prefer it
        resp_sources = resp.get('sources', [])
        if response_key == 'default' or not answer:
            # 3) KB search
            kb_hit = kb_search(query_text or '')
            if kb_hit:
                answer = f"I found something in our documentation ({kb_hit['file']}): {kb_hit['excerpt']}"
                confidence = 0.88
                resp_sources = [os.path.join('data', 'kb', kb_hit['file'])]
            else:
                # 4) LLM fallback
                llm_ans = call_llm(query_text or '')
                if llm_ans:
                    answer = llm_ans
                    confidence = 0.75
                    resp_sources = ['llm']
                else:
                    # 5) escalate to human (best-effort async) and return a friendly escalation message
                    try:
                        t = threading.Thread(target=escalate_to_human, args=(body, f"User requested human escalation for: {query_text}"), daemon=True)
                        t.start()
                    except Exception:
                        pass
                    answer = "I couldn't find an automated answer. I've forwarded this to a human agent — someone will join shortly."
                    confidence = 0.0
                    resp_sources = []

    # Build Zobot synchronous payload (the widget can accept this when configured)
    sync_payload = {
        "message": answer,
        "type": "text",
        "metadata": {
            "confidence": confidence,
            "sources": resp_sources,
            "version": "2.0.1-pipeline"
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
