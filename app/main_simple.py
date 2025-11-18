"""
Simplified FastAPI server for webhook testing.
This version avoids problematic imports and provides basic functionality.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
from datetime import datetime
import logging

try:
    from salesiq_push import send_message_to_salesiq
except Exception:
    # fallback if module not available
    def send_message_to_salesiq(*args, **kwargs):
        logging.getLogger(__name__).info("salesiq_push not available — dry-run")
        return {"dry_run": True}

app = FastAPI(title="AceBuddy RAG Chatbot (Simple Mode)", version="2.0.0-simple")

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
    
    # Determine which response to use
    query_lower = request.query.lower()
    response_key = "default"
    
    if any(word in query_lower for word in ["webdav", "web dav", "file share"]):
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
def salesiq_chat(request: SalesIQChatRequest) -> SalesIQChatResponse:
    """SalesIQ webhook endpoint"""
    
    # Use the same logic as main chat endpoint
    query_lower = request.query.lower()
    
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
    
    # Build response model
    response_model = SalesIQChatResponse(
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
            "timestamp": datetime.now().isoformat(),
            "integration": "salesiq"
        }
    )

    # Attempt to push the reply asynchronously into SalesIQ conversation
    # Use chat_id if available, otherwise visitor_id
    conversation_id = request.chat_id or request.visitor_id
    try:
        send_message_to_salesiq(
            conversation_id=conversation_id,
            message=response_model.answer,
            confidence=response_model.confidence,
            should_escalate=response_model.should_escalate,
            extra_metadata={"sources": response_model.sources}
        )
    except Exception as e:
        logging.getLogger(__name__).exception(f"Error pushing to SalesIQ: {e}")

    # Return acknowledgement to webhook caller
    return response_model

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
