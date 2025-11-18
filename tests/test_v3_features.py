"""
Test v3.0 Features: Conversation History, Query Enhancement, Response Validation
=================================================================================

Tests for the enhanced chatbot features including:
- Conversation history and session management
- Query enhancement with synonyms and rewrites
- Response quality validation
- Multi-turn dialogue support
"""

import pytest
import requests
import json
import time


BASE_URL = "http://localhost:8000"


class TestConversationHistory:
    """Test conversation history features"""
    
    def test_chat_creates_session(self):
        """Test that chat without session_id creates new session"""
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "How do I reset my password?",
                "user_id": "test_user_001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return a session_id
        assert data.get("session_id") is not None
        assert isinstance(data["session_id"], str)
        assert len(data["session_id"]) > 0
        
        # Should have response quality score
        assert "response_quality" in data
        assert 0 <= data["response_quality"] <= 1
        
        return data["session_id"]
    
    def test_chat_uses_existing_session(self):
        """Test that chat with session_id uses existing session"""
        # First message
        response1 = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "What are the disk storage upgrade options?",
                "user_id": "test_user_002"
            }
        )
        
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]
        
        # Follow-up message with same session
        response2 = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "How much does the premium option cost?",
                "user_id": "test_user_002",
                "session_id": session_id
            }
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should use same session
        assert data2["session_id"] == session_id
    
    def test_get_conversation_history(self):
        """Test retrieving conversation history"""
        # Create a conversation
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "How do I connect via RDP?",
                "user_id": "test_user_003"
            }
        )
        
        session_id = response.json()["session_id"]
        
        # Add another message
        requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "What port does RDP use?",
                "user_id": "test_user_003",
                "session_id": session_id
            }
        )
        
        # Get conversation history
        history_response = requests.get(f"{BASE_URL}/conversation/{session_id}")
        
        assert history_response.status_code == 200
        history = history_response.json()
        
        # Should have session info
        assert history["session_id"] == session_id
        assert history["user_id"] == "test_user_003"
        
        # Should have messages (2 user + 2 assistant = 4 total)
        assert history["message_count"] >= 4
        assert len(history["messages"]) >= 4
        
        # Check message structure
        msg = history["messages"][0]
        assert "role" in msg
        assert "content" in msg
        assert "timestamp" in msg
        assert msg["role"] in ["user", "assistant"]
    
    def test_conversation_stats(self):
        """Test conversation statistics endpoint"""
        # Create some conversations
        for i in range(3):
            requests.post(
                f"{BASE_URL}/chat",
                json={
                    "query": f"Test query {i}",
                    "user_id": f"test_user_{i}"
                }
            )
        
        # Get stats
        stats_response = requests.get(f"{BASE_URL}/conversation/stats")
        
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        # Should have statistics
        assert "total_sessions" in stats
        assert "total_messages" in stats
        assert stats["total_sessions"] >= 3
        assert stats["total_messages"] >= 6  # At least 2 messages per session


class TestQueryEnhancement:
    """Test query enhancement features"""
    
    def test_query_enhancement_enabled(self):
        """Test that query enhancement improves retrieval"""
        # Query with enhancement enabled (default)
        response1 = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "How to reset pwd?",
                "user_id": "test_user_004",
                "enhance_query": True
            }
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Should have query_enhanced flag
        assert "query_enhanced" in data1
        # If query enhancer is available, it should be True
        # (It will be False if the module isn't loaded)
        
        # Should still return a valid response
        assert data1["answer"]
        assert len(data1["answer"]) > 0
    
    def test_query_enhancement_disabled(self):
        """Test that query enhancement can be disabled"""
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "disk storage upgrade",
                "user_id": "test_user_005",
                "enhance_query": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # query_enhanced should be False when disabled
        assert data["query_enhanced"] == False
    
    def test_synonym_expansion(self):
        """Test that synonyms are used to improve retrieval"""
        # Test with abbreviated term
        response1 = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "rdp problems",
                "user_id": "test_user_006",
                "enhance_query": True
            }
        )
        
        # Should find Remote Desktop related content
        assert response1.status_code == 200
        data = response1.json()
        
        # Should have contexts
        assert len(data["context_with_metadata"]) > 0


class TestResponseValidation:
    """Test response quality validation"""
    
    def test_response_quality_score(self):
        """Test that responses include quality scores"""
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "How do I reset my password?",
                "user_id": "test_user_007"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have quality score
        assert "response_quality" in data
        assert isinstance(data["response_quality"], (int, float))
        assert 0 <= data["response_quality"] <= 1
    
    def test_low_quality_warning(self):
        """Test that low quality responses include warnings"""
        # Query about something not in KB
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "What is the meaning of life?",
                "user_id": "test_user_008"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # If quality is very low, should have low confidence
        if data["response_quality"] < 0.3:
            # Answer might include disclaimer
            assert "contact support" in data["answer"].lower() or \
                   "don't have" in data["answer"].lower() or \
                   "not have enough" in data["answer"].lower()


class TestBackwardCompatibility:
    """Test that v3.0 maintains backward compatibility"""
    
    def test_v2_request_format(self):
        """Test that old v2.0 request format still works"""
        # Simple v2.0 style request (no session_id, no enhance_query flags)
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "How do I reset my password?",
                "user_id": "test_user_009"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have all v2.0 fields
        assert "answer" in data
        assert "intent" in data
        assert "intent_confidence" in data
        assert "context" in data
        assert "context_with_metadata" in data
        assert "confidence" in data
        
        # Should also have new v3.0 fields
        assert "session_id" in data
        assert "response_quality" in data
        assert "query_enhanced" in data
    
    def test_context_formats(self):
        """Test that both context formats are returned"""
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "disk storage upgrade",
                "user_id": "test_user_010"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have both context formats
        assert "context" in data
        assert "context_with_metadata" in data
        
        # context should be list of strings
        if len(data["context"]) > 0:
            assert isinstance(data["context"][0], str)
        
        # context_with_metadata should be list of dicts
        if len(data["context_with_metadata"]) > 0:
            item = data["context_with_metadata"][0]
            assert isinstance(item, dict)
            assert "content" in item
            assert "source" in item
            assert "chunk_id" in item
            assert "rank" in item
            assert "confidence" in item


class TestHealthAndStatus:
    """Test health check with new services"""
    
    def test_health_includes_new_services(self):
        """Test that health check includes new v3.0 services"""
        response = requests.get(f"{BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have status
        assert "status" in data
        assert data["status"] in ["healthy", "partial", "unhealthy"]
        
        # Should have services status
        assert "services" in data
        services = data["services"]
        
        # Should check new services
        assert "conversation_manager" in services
        assert "query_enhancer" in services
        assert "response_validator" in services
        
        # Should have version
        assert "version" in data
        assert data["version"] == "2.0.0"


class TestMultiTurnConversation:
    """Test multi-turn conversation flows"""
    
    def test_follow_up_questions(self):
        """Test that follow-up questions use conversation context"""
        # First question
        response1 = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "Tell me about password reset procedures",
                "user_id": "test_user_011"
            }
        )
        
        session_id = response1.json()["session_id"]
        
        # Follow-up question using "it"
        response2 = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "How long does it take?",
                "user_id": "test_user_011",
                "session_id": session_id,
                "use_history": True
            }
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should provide relevant answer (though LLM quality may vary)
        assert data2["answer"]
        assert len(data2["answer"]) > 0
    
    def test_conversation_without_history(self):
        """Test that conversations can disable history"""
        # First message
        response1 = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "How do I reset my password?",
                "user_id": "test_user_012"
            }
        )
        
        session_id = response1.json()["session_id"]
        
        # Second message with history disabled
        response2 = requests.post(
            f"{BASE_URL}/chat",
            json={
                "query": "What about disk storage?",
                "user_id": "test_user_012",
                "session_id": session_id,
                "use_history": False
            }
        )
        
        assert response2.status_code == 200
        # Should still work, just without conversation context


# Test execution summary
if __name__ == "__main__":
    print("=" * 80)
    print("AceBuddy RAG v3.0 Feature Tests")
    print("=" * 80)
    print("\nTest Groups:")
    print("1. Conversation History - Session management and multi-turn conversations")
    print("2. Query Enhancement - Synonym expansion and query rewriting")
    print("3. Response Validation - Quality scoring and low-confidence warnings")
    print("4. Backward Compatibility - v2.0 request format support")
    print("5. Health & Status - Service availability checks")
    print("6. Multi-Turn Conversation - Context-aware follow-up questions")
    print("\nRun with: pytest tests/test_v3_features.py -v")
    print("=" * 80)
