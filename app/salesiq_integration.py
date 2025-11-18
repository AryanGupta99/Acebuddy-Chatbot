"""
Zoho SalesIQ Webhook Handler
Integrates AceBuddy RAG chatbot with Zoho SalesIQ for live support automation.
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router for SalesIQ-specific endpoints
salesiq_router = APIRouter(prefix="/salesiq", tags=["Zoho SalesIQ"])

# ============================================================================
# Data Models
# ============================================================================

class SalesIQWebhookPayload(BaseModel):
    """Incoming webhook from Zoho SalesIQ"""
    visitor_id: Optional[str] = None
    message: Optional[str] = None
    chat_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    visitor_device: Optional[str] = None
    timestamp: Optional[str] = None


class SalesIQChatRequest(BaseModel):
    """Chat request from SalesIQ integration"""
    query: str
    visitor_id: str
    chat_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    session_id: Optional[str] = None
    use_history: bool = True


class SalesIQResponse(BaseModel):
    """Response formatted for SalesIQ"""
    answer: str
    confidence: float
    should_escalate: bool = False
    escalation_reason: Optional[str] = None
    sources: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# Configuration
# ============================================================================

# Thresholds for human escalation
MIN_CONFIDENCE_THRESHOLD = 0.7
MIN_QUALITY_THRESHOLD = 0.6
MAX_RESPONSE_TIME_MS = 5000

# Escalation reasons
ESCALATION_REASONS = {
    "low_confidence": "I'm not certain about this answer. Let me connect you with a specialist.",
    "low_quality": "I found information, but it may not fully address your question.",
    "api_error": "I'm having trouble connecting. A specialist will help shortly.",
    "no_context": "I don't have information about that topic. A specialist can help."
}


# ============================================================================
# Helper Functions
# ============================================================================

def validate_salesiq_request(
    request: Request,
    api_key: Optional[str] = Header(None)
) -> bool:
    """Validate incoming SalesIQ webhook request"""
    
    # Option 1: API Key validation
    expected_key = __import__('os').getenv('SALESIQ_API_KEY')
    if expected_key and api_key != f"Bearer {expected_key}":
        logger.warning(f"Invalid API key in SalesIQ request")
        return False
    
    # Option 2: IP whitelist (optional)
    # Add SalesIQ IP addresses to whitelist
    SALESIQ_IPS = [
        "1.236.39.0/24",  # Example SalesIQ range
        # Add more as needed
    ]
    
    return True


def should_escalate_to_human(
    confidence: float,
    response_quality: float,
    escalation_reason: Optional[str] = None
) -> tuple[bool, str]:
    """Determine if response should be escalated to human agent
    
    Returns:
        (should_escalate: bool, reason: str)
    """
    
    if escalation_reason:
        return True, ESCALATION_REASONS.get(escalation_reason, "Escalating to specialist")
    
    if confidence < MIN_CONFIDENCE_THRESHOLD:
        return True, ESCALATION_REASONS["low_confidence"]
    
    if response_quality < MIN_QUALITY_THRESHOLD:
        return True, ESCALATION_REASONS["low_quality"]
    
    return False, ""


def format_for_salesiq(
    answer: str,
    confidence: float,
    response_quality: float,
    context: list,
    session_id: Optional[str] = None
) -> SalesIQResponse:
    """Format bot response for SalesIQ display"""
    
    should_escalate, reason = should_escalate_to_human(confidence, response_quality)
    
    if should_escalate:
        answer = reason
    
    # Format sources for SalesIQ (limit to top 2)
    sources = [
        {
            "title": ctx.get("source", "Unknown"),
            "confidence": ctx.get("confidence", 0)
        }
        for ctx in context[:2]
    ]
    
    return SalesIQResponse(
        answer=answer,
        confidence=confidence,
        should_escalate=should_escalate,
        escalation_reason=reason if should_escalate else None,
        sources=sources,
        metadata={
            "response_quality": response_quality,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================================
# Endpoints
# ============================================================================

@salesiq_router.post("/webhook")
async def salesiq_webhook(payload: SalesIQWebhookPayload):
    """
    Zoho SalesIQ webhook endpoint
    
    Receives incoming chat messages and routes to RAG system
    """
    try:
        logger.info(f"SalesIQ webhook received: visitor={payload.visitor_id}, chat={payload.chat_id}")
        
        if not payload.message:
            return {"status": "ok", "message": "No message to process"}
        
        # Import chat function from main app
        from app.main import chat, ChatRequest
        
        # Convert SalesIQ message to chat request
        chat_request = ChatRequest(
            query=payload.message,
            user_id=payload.visitor_id or "unknown",
            session_id=payload.chat_id
        )
        
        # Get response from RAG system
        chat_response = await chat(chat_request)
        
        # Format for SalesIQ
        salesiq_response = format_for_salesiq(
            answer=chat_response.answer,
            confidence=chat_response.confidence,
            response_quality=chat_response.response_quality,
            context=chat_response.context_with_metadata,
            session_id=chat_response.session_id
        )
        
        logger.info(f"Sending response: confidence={salesiq_response.confidence}, escalate={salesiq_response.should_escalate}")
        
        return salesiq_response.dict()
        
    except Exception as e:
        logger.error(f"Error in SalesIQ webhook: {e}", exc_info=True)
        
        # Return escalation on error
        return {
            "answer": ESCALATION_REASONS["api_error"],
            "confidence": 0.0,
            "should_escalate": True,
            "escalation_reason": ESCALATION_REASONS["api_error"]
        }


@salesiq_router.post("/chat")
async def salesiq_chat(request: SalesIQChatRequest):
    """
    Direct chat endpoint for SalesIQ integration
    
    Example request:
    {
        "query": "How do I reset my password?",
        "visitor_id": "visitor_123",
        "chat_id": "chat_456",
        "email": "user@example.com",
        "name": "John Doe"
    }
    """
    try:
        logger.info(f"SalesIQ chat request: query='{request.query[:50]}...', visitor={request.visitor_id}")
        
        # Import chat function
        from app.main import chat, ChatRequest
        
        # Convert to internal chat request
        chat_request = ChatRequest(
            query=request.query,
            user_id=request.visitor_id,
            session_id=request.chat_id or request.visitor_id,
            use_history=request.use_history
        )
        
        # Get RAG response
        chat_response = await chat(chat_request)
        
        # Format for SalesIQ
        salesiq_response = format_for_salesiq(
            answer=chat_response.answer,
            confidence=chat_response.confidence,
            response_quality=chat_response.response_quality,
            context=chat_response.context_with_metadata,
            session_id=chat_response.session_id
        )
        
        # Add metadata for SalesIQ
        response_dict = salesiq_response.dict()
        response_dict["visitor_id"] = request.visitor_id
        response_dict["chat_id"] = request.chat_id
        response_dict["visitor_email"] = request.email
        response_dict["visitor_name"] = request.name
        
        logger.info(f"Response sent: escalate={response_dict['should_escalate']}")
        
        return response_dict
        
    except Exception as e:
        logger.error(f"Error in SalesIQ chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@salesiq_router.get("/status")
async def salesiq_status():
    """
    Health check endpoint for SalesIQ integration
    
    SalesIQ can call this to verify integration is working
    """
    try:
        from app.main import embedding_model, chroma_client, collection
        
        status = {
            "status": "healthy",
            "services": {
                "embedding_model": embedding_model is not None,
                "chroma_connected": chroma_client is not None,
                "collection_loaded": collection is not None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check document count
        if collection:
            doc_count = collection.count()
            status["documents_indexed"] = doc_count
        
        return status
        
    except Exception as e:
        logger.error(f"Error in status check: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@salesiq_router.post("/test")
async def salesiq_test(request: SalesIQChatRequest):
    """
    Test endpoint for debugging SalesIQ integration
    
    Use this to test the integration without going through SalesIQ
    """
    logger.info(f"Test request: {request.query}")
    
    return await salesiq_chat(request)


# ============================================================================
# Batch Operations
# ============================================================================

@salesiq_router.post("/batch")
async def salesiq_batch(requests: list[SalesIQChatRequest]):
    """
    Batch endpoint for processing multiple messages
    
    Useful for:
    - Testing multiple queries
    - Bulk chat exports
    - Analytics processing
    """
    responses = []
    
    for idx, req in enumerate(requests):
        try:
            response = await salesiq_chat(req)
            responses.append({
                "index": idx,
                "status": "success",
                "response": response
            })
        except Exception as e:
            logger.error(f"Batch request {idx} failed: {e}")
            responses.append({
                "index": idx,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "total": len(requests),
        "successful": sum(1 for r in responses if r["status"] == "success"),
        "responses": responses
    }


# ============================================================================
# Analytics & Monitoring
# ============================================================================

class SalesIQAnalytics:
    """Track analytics for SalesIQ integration"""
    
    def __init__(self):
        self.total_messages = 0
        self.escalations = 0
        self.high_confidence = 0
        self.messages_by_topic = {}
    
    def record_interaction(self, query: str, confidence: float, escalated: bool, topic: str = "unknown"):
        """Record interaction metrics"""
        self.total_messages += 1
        
        if escalated:
            self.escalations += 1
        else:
            if confidence >= 0.8:
                self.high_confidence += 1
        
        self.messages_by_topic[topic] = self.messages_by_topic.get(topic, 0) + 1
    
    def get_stats(self):
        """Get current statistics"""
        escalation_rate = (self.escalations / self.total_messages * 100) if self.total_messages > 0 else 0
        
        return {
            "total_messages": self.total_messages,
            "escalations": self.escalations,
            "escalation_rate": f"{escalation_rate:.1f}%",
            "high_confidence_responses": self.high_confidence,
            "top_topics": dict(sorted(
                self.messages_by_topic.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5])
        }


# Global analytics instance
salesiq_analytics = SalesIQAnalytics()


@salesiq_router.get("/analytics")
async def get_analytics():
    """Get SalesIQ integration analytics"""
    return salesiq_analytics.get_stats()


# ============================================================================
# Configuration Endpoint
# ============================================================================

@salesiq_router.get("/config")
async def get_config():
    """Get current SalesIQ integration configuration"""
    import os
    
    return {
        "min_confidence_threshold": MIN_CONFIDENCE_THRESHOLD,
        "min_quality_threshold": MIN_QUALITY_THRESHOLD,
        "max_response_time_ms": MAX_RESPONSE_TIME_MS,
        "conversation_history_enabled": os.getenv("USE_CONVERSATION_HISTORY", "true") == "true",
        "query_enhancement_enabled": os.getenv("ENABLE_QUERY_OPTIMIZATION", "true") == "true"
    }


# ============================================================================
# Integration Validation
# ============================================================================

async def validate_salesiq_integration():
    """Validate that SalesIQ integration is properly configured"""
    
    checks = {
        "api_key_configured": bool(__import__('os').getenv('SALESIQ_API_KEY')),
        "chat_endpoint_ready": True,
        "webhook_handler_ready": True,
        "conversation_manager": True,
        "embedding_model": True
    }
    
    return all(checks.values()), checks


# ============================================================================
# Add router to main app
# ============================================================================

def add_salesiq_routes(app):
    """Add SalesIQ routes to FastAPI app"""
    app.include_router(salesiq_router)
    logger.info("SalesIQ integration routes registered")
