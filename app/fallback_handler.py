"""
Intelligent Fallback System
==========================

Handles cases where RAG cannot provide confident answers:
- Low confidence detection
- Helpful suggestions based on intent
- Related questions
- Escalation paths
"""

import logging
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)


class FallbackHandler:
    """Handle fallback scenarios intelligently"""
    
    def __init__(self):
        # Confidence thresholds
        self.low_confidence_threshold = 0.3
        self.medium_confidence_threshold = 0.6
        
        # Common support paths
        self.escalation_contacts = {
            "technical": "support@acecloudhosting.com",
            "billing": "billing@acecloudhosting.com",
            "sales": "sales@acecloudhosting.com"
        }
        
        # Fallback responses by intent
        self.fallback_templates = {
            "how_to": "I don't have specific instructions for that, but here are some related resources...",
            "troubleshooting": "I couldn't find an exact solution, but let me suggest some troubleshooting steps...",
            "information": "I don't have that information in my knowledge base, but I can help you find it...",
            "unknown": "I'm not sure I understand your question correctly. Could you rephrase it?"
        }
    
    def should_use_fallback(
        self,
        confidence: float,
        context_quality: float,
        response: str
    ) -> bool:
        """
        Determine if fallback should be used
        
        Args:
            confidence: Response confidence score (0-1)
            context_quality: Quality of retrieved context (0-1)
            response: Generated response text
        
        Returns:
            True if fallback needed
        """
        # Low confidence trigger
        if confidence < self.low_confidence_threshold:
            return True
        
        # Poor context trigger
        if context_quality < 0.4:
            return True
        
        # Detect uncertain language in response
        uncertain_phrases = [
            "i'm not sure",
            "i don't know",
            "i cannot",
            "i don't have",
            "unclear",
            "unable to find"
        ]
        
        response_lower = response.lower()
        if any(phrase in response_lower for phrase in uncertain_phrases):
            return True
        
        # Response too short (likely incomplete)
        if len(response.split()) < 10:
            return True
        
        return False
    
    def generate_fallback_response(
        self,
        query: str,
        intent: Optional[str],
        confidence: float,
        partial_response: str,
        context_docs: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate intelligent fallback response
        
        Returns:
            {
                "answer": str,
                "suggestions": List[str],
                "related_questions": List[str],
                "escalation": Dict,
                "fallback_reason": str
            }
        """
        # Determine fallback reason
        if confidence < 0.2:
            reason = "very_low_confidence"
        elif confidence < self.low_confidence_threshold:
            reason = "low_confidence"
        elif len(context_docs) == 0:
            reason = "no_relevant_context"
        else:
            reason = "uncertain_response"
        
        # Build fallback response
        fallback_response = self._build_fallback_message(
            query, intent, reason, partial_response
        )
        
        # Generate suggestions
        suggestions = self._generate_suggestions(query, intent, context_docs)
        
        # Generate related questions
        related = self._generate_related_questions(query, intent)
        
        # Determine escalation path
        escalation = self._determine_escalation(query, intent)
        
        return {
            "answer": fallback_response,
            "suggestions": suggestions,
            "related_questions": related,
            "escalation": escalation,
            "fallback_reason": reason,
            "confidence": confidence,
            "is_fallback": True
        }
    
    def _build_fallback_message(
        self,
        query: str,
        intent: Optional[str],
        reason: str,
        partial_response: str
    ) -> str:
        """Build helpful fallback message"""
        # Start with acknowledgment
        message = "I want to help you with that. "
        
        # Add context-specific intro
        if reason == "very_low_confidence":
            message += "However, I don't have specific information about this in my current knowledge base. "
        elif reason == "no_relevant_context":
            message += "I couldn't find relevant information about this specific topic. "
        else:
            message += "I have limited information about this. "
        
        # Add partial info if available
        if partial_response and len(partial_response) > 20:
            message += f"\n\nWhat I can tell you:\n{partial_response}\n\n"
        
        # Add intent-specific guidance
        if intent == "how_to":
            message += "For detailed step-by-step instructions, "
        elif intent == "troubleshooting":
            message += "For technical troubleshooting assistance, "
        elif intent == "billing":
            message += "For billing questions, "
        else:
            message += "For more specific help, "
        
        message += "please see the suggestions below or contact our support team."
        
        return message
    
    def _generate_suggestions(
        self,
        query: str,
        intent: Optional[str],
        context_docs: List[Dict]
    ) -> List[str]:
        """Generate helpful suggestions"""
        suggestions = []
        
        # Intent-based suggestions
        if intent == "how_to":
            suggestions.extend([
                "Check our knowledge base articles for step-by-step guides",
                "Try rephrasing your question to be more specific",
                "Contact support for personalized assistance"
            ])
        elif intent == "troubleshooting":
            suggestions.extend([
                "Verify the issue is still occurring",
                "Try basic troubleshooting: restart, check connections, verify credentials",
                "Gather error messages or screenshots to share with support"
            ])
        elif intent == "account_management":
            suggestions.extend([
                "Use the self-service portal at https://manage.acecloudhosting.com",
                "Contact your account manager for account changes",
                "Check your email for recent account notifications"
            ])
        else:
            suggestions.extend([
                "Try asking a more specific question",
                "Browse our knowledge base for related topics",
                "Contact our support team for direct assistance"
            ])
        
        # Add suggestions based on available context
        if context_docs:
            # Extract topics from context
            topics = set()
            for doc in context_docs[:3]:
                topic = doc.get("metadata", {}).get("topic", "")
                if topic:
                    topics.add(topic)
            
            if topics:
                topics_str = ", ".join(list(topics)[:3])
                suggestions.append(f"Explore related topics: {topics_str}")
        
        return suggestions[:5]  # Max 5 suggestions
    
    def _generate_related_questions(
        self,
        query: str,
        intent: Optional[str]
    ) -> List[str]:
        """Generate related questions user might ask"""
        related = []
        
        # Extract key terms from query
        query_lower = query.lower()
        
        # Common IT support related questions
        if "password" in query_lower:
            related.extend([
                "How do I reset my password?",
                "What are the password requirements?",
                "How do I enable multi-factor authentication?"
            ])
        elif "quickbooks" in query_lower:
            related.extend([
                "How do I upgrade QuickBooks?",
                "How to fix QuickBooks login issues?",
                "How do I backup QuickBooks data?"
            ])
        elif "server" in query_lower:
            related.extend([
                "How do I connect to my server?",
                "How to increase server resources?",
                "How do I reboot my server?"
            ])
        elif "user" in query_lower:
            related.extend([
                "How do I add a new user?",
                "How to remove a user?",
                "How to change user permissions?"
            ])
        elif "printer" in query_lower:
            related.extend([
                "How do I setup a printer?",
                "How to troubleshoot printer issues?",
                "How do I add a network printer?"
            ])
        else:
            # Generic related questions
            related.extend([
                "What services does Ace Cloud Hosting offer?",
                "How do I access support?",
                "Where can I find account information?"
            ])
        
        return related[:5]  # Max 5 related questions
    
    def _determine_escalation(
        self,
        query: str,
        intent: Optional[str]
    ) -> Dict[str, Any]:
        """Determine appropriate escalation path"""
        query_lower = query.lower()
        
        # Billing-related
        if any(word in query_lower for word in ["bill", "invoice", "payment", "charge", "refund"]):
            return {
                "type": "billing",
                "contact": self.escalation_contacts["billing"],
                "message": "For billing inquiries, please contact our billing team",
                "urgent": "refund" in query_lower or "charge" in query_lower
            }
        
        # Sales-related
        if any(word in query_lower for word in ["upgrade", "purchase", "plan", "pricing"]):
            return {
                "type": "sales",
                "contact": self.escalation_contacts["sales"],
                "message": "For upgrades and pricing, please contact our sales team",
                "urgent": False
            }
        
        # Technical support (default)
        return {
            "type": "technical",
            "contact": self.escalation_contacts["technical"],
            "message": "For technical assistance, please contact our support team",
            "urgent": any(word in query_lower for word in ["urgent", "down", "broken", "critical", "emergency"]),
            "available_24_7": True
        }
    
    def enhance_low_confidence_response(
        self,
        response: str,
        confidence: float,
        suggestions: List[str]
    ) -> str:
        """
        Enhance low confidence response with disclaimers and suggestions
        """
        if confidence >= self.medium_confidence_threshold:
            return response  # No enhancement needed
        
        enhanced = response
        
        # Add confidence disclaimer for medium confidence
        if self.low_confidence_threshold <= confidence < self.medium_confidence_threshold:
            enhanced = f"Based on available information:\n\n{enhanced}\n\n"
            enhanced += "Please note: This information may not be complete. "
            enhanced += "For definitive guidance, please contact support."
        
        # Add suggestions
        if suggestions:
            enhanced += "\n\n**Helpful suggestions:**\n"
            for i, suggestion in enumerate(suggestions[:3], 1):
                enhanced += f"{i}. {suggestion}\n"
        
        return enhanced
