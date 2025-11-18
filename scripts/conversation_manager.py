"""
Conversation History Manager
============================

Manages multi-turn conversations with context window and session management.
"""

import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib


@dataclass
class Message:
    """Single message in conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: float
    intent: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict] = None


@dataclass
class Conversation:
    """Conversation session"""
    session_id: str
    user_id: str
    messages: List[Message]
    created_at: float
    last_updated: float
    context_summary: str = ""
    
    def add_message(self, message: Message):
        """Add message to conversation"""
        self.messages.append(message)
        self.last_updated = time.time()
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get recent messages"""
        return self.messages[-limit:]
    
    def get_context_window(self, max_tokens: int = 2000) -> List[Message]:
        """
        Get messages that fit within token budget
        Simple approximation: 1 token ≈ 4 characters
        """
        total_chars = 0
        context_messages = []
        
        for message in reversed(self.messages):
            msg_chars = len(message.content)
            if total_chars + msg_chars > max_tokens * 4:
                break
            context_messages.insert(0, message)
            total_chars += msg_chars
        
        return context_messages
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'messages': [asdict(m) for m in self.messages],
            'created_at': self.created_at,
            'last_updated': self.last_updated,
            'context_summary': self.context_summary
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Conversation':
        """Create from dictionary"""
        messages = [Message(**m) for m in data['messages']]
        return cls(
            session_id=data['session_id'],
            user_id=data['user_id'],
            messages=messages,
            created_at=data['created_at'],
            last_updated=data['last_updated'],
            context_summary=data.get('context_summary', '')
        )


class ConversationManager:
    """Manages conversation sessions"""
    
    def __init__(self, session_timeout_minutes: int = 30, max_sessions: int = 1000):
        self.sessions: Dict[str, Conversation] = {}
        self.user_sessions: Dict[str, List[str]] = defaultdict(list)
        self.session_timeout = session_timeout_minutes * 60
        self.max_sessions = max_sessions
    
    def create_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        """Create new conversation session"""
        if session_id is None:
            session_id = self._generate_session_id(user_id)
        
        conversation = Conversation(
            session_id=session_id,
            user_id=user_id,
            messages=[],
            created_at=time.time(),
            last_updated=time.time()
        )
        
        self.sessions[session_id] = conversation
        self.user_sessions[user_id].append(session_id)
        
        # Cleanup old sessions if needed
        self._cleanup_old_sessions()
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Conversation]:
        """Get conversation session"""
        session = self.sessions.get(session_id)
        
        if session:
            # Check if session is expired
            if time.time() - session.last_updated > self.session_timeout:
                self.delete_session(session_id)
                return None
        
        return session
    
    def get_or_create_session(self, user_id: str, session_id: Optional[str] = None) -> Conversation:
        """Get existing session or create new one"""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        
        # Create new session
        new_session_id = self.create_session(user_id, session_id)
        return self.sessions[new_session_id]
    
    def add_message(self, session_id: str, role: str, content: str, 
                   intent: Optional[str] = None, confidence: Optional[float] = None,
                   metadata: Optional[Dict] = None) -> bool:
        """Add message to conversation"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        message = Message(
            role=role,
            content=content,
            timestamp=time.time(),
            intent=intent,
            confidence=confidence,
            metadata=metadata
        )
        
        session.add_message(message)
        return True
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        recent_messages = session.get_recent_messages(limit)
        return [asdict(m) for m in recent_messages]
    
    def get_context_for_prompt(self, session_id: str, max_tokens: int = 2000) -> str:
        """Get formatted conversation context for LLM prompt"""
        session = self.get_session(session_id)
        if not session or not session.messages:
            return ""
        
        context_messages = session.get_context_window(max_tokens)
        
        # Format as conversation history
        formatted = []
        for msg in context_messages:
            prefix = "User" if msg.role == "user" else "Assistant"
            formatted.append(f"{prefix}: {msg.content}")
        
        return "\n".join(formatted)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete conversation session"""
        session = self.sessions.get(session_id)
        if session:
            user_id = session.user_id
            self.user_sessions[user_id].remove(session_id)
            del self.sessions[session_id]
            return True
        return False
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all sessions for a user"""
        return self.user_sessions.get(user_id, [])
    
    def _generate_session_id(self, user_id: str) -> str:
        """Generate unique session ID"""
        timestamp = str(time.time())
        data = f"{user_id}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _cleanup_old_sessions(self):
        """Remove expired sessions"""
        if len(self.sessions) <= self.max_sessions:
            return
        
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.last_updated > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        # If still over limit, remove oldest sessions
        if len(self.sessions) > self.max_sessions:
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1].last_updated
            )
            
            to_remove = len(self.sessions) - self.max_sessions
            for session_id, _ in sorted_sessions[:to_remove]:
                self.delete_session(session_id)
    
    def get_stats(self) -> Dict:
        """Get conversation statistics"""
        total_messages = sum(len(s.messages) for s in self.sessions.values())
        avg_messages = total_messages / len(self.sessions) if self.sessions else 0
        
        return {
            'total_sessions': len(self.sessions),
            'total_users': len(self.user_sessions),
            'total_messages': total_messages,
            'avg_messages_per_session': round(avg_messages, 2),
            'active_sessions': len([s for s in self.sessions.values() 
                                   if time.time() - s.last_updated < 300])  # Active in last 5 min
        }


# Global conversation manager instance
_conversation_manager = None


def get_conversation_manager() -> ConversationManager:
    """Get or create global conversation manager"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager


if __name__ == "__main__":
    # Test conversation manager
    manager = ConversationManager()
    
    # Create session
    session_id = manager.create_session("test_user")
    print(f"Created session: {session_id}")
    
    # Add messages
    manager.add_message(session_id, "user", "How do I reset my password?", 
                       intent="password_reset", confidence=0.8)
    manager.add_message(session_id, "assistant", "To reset your password, go to...")
    manager.add_message(session_id, "user", "What if I forgot my email?")
    manager.add_message(session_id, "assistant", "If you forgot your email...")
    
    # Get history
    history = manager.get_conversation_history(session_id)
    print(f"\nConversation history ({len(history)} messages):")
    for msg in history:
        print(f"  {msg['role']}: {msg['content'][:50]}...")
    
    # Get context for prompt
    context = manager.get_context_for_prompt(session_id)
    print(f"\nContext for prompt:\n{context}")
    
    # Get stats
    stats = manager.get_stats()
    print(f"\nStats: {stats}")
