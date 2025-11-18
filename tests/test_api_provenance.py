"""
API Provenance Test
===================

Tests that the /chat endpoint returns rich provenance information:
- Intent classification
- Context with metadata (source, chunk_id, rank, confidence)
"""

import pytest
import requests
import time
import os


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 30


@pytest.fixture(scope="module")
def wait_for_api():
    """Wait for API to be ready before running tests"""
    max_retries = 10
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ API is ready at {API_BASE_URL}")
                return True
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                print(f"⏳ Waiting for API... ({attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                pytest.skip(f"API not available at {API_BASE_URL}")
    return False


class TestAPIProvenance:
    """Test API provenance and intent features"""
    
    def test_health_endpoint(self, wait_for_api):
        """Test that health endpoint is working"""
        response = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"✅ Health check: {data}")
    
    def test_chat_response_structure(self, wait_for_api):
        """Test that chat response has expected structure with provenance"""
        payload = {
            "query": "How do I reset my password?",
            "user_id": "test_user"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Check main fields
        assert "answer" in data, "Response missing 'answer' field"
        assert "intent" in data, "Response missing 'intent' field"
        assert "intent_confidence" in data, "Response missing 'intent_confidence' field"
        assert "confidence" in data, "Response missing 'confidence' field"
        
        print(f"✅ Response structure valid")
        print(f"   Intent: {data['intent']} (confidence: {data['intent_confidence']:.2f})")
        print(f"   Answer length: {len(data['answer'])} chars")
    
    def test_context_with_metadata(self, wait_for_api):
        """Test that context_with_metadata contains provenance fields"""
        payload = {
            "query": "I can't connect to RDP",
            "user_id": "test_user"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check context_with_metadata field exists
        assert "context_with_metadata" in data, "Response missing 'context_with_metadata' field"
        
        context_items = data["context_with_metadata"]
        
        if len(context_items) > 0:
            # Check first context item has all required fields
            first_item = context_items[0]
            
            required_fields = ["content", "source", "chunk_id", "rank", "confidence"]
            for field in required_fields:
                assert field in first_item, f"Context item missing '{field}' field"
            
            # Validate field types
            assert isinstance(first_item["content"], str), "content should be string"
            assert isinstance(first_item["rank"], int), "rank should be integer"
            assert isinstance(first_item["confidence"], (int, float)), "confidence should be numeric"
            assert first_item["rank"] >= 1, "rank should be >= 1"
            assert 0 <= first_item["confidence"] <= 1, "confidence should be between 0 and 1"
            
            print(f"✅ Context metadata valid:")
            print(f"   Total context items: {len(context_items)}")
            print(f"   First item:")
            print(f"      Source: {first_item['source']}")
            print(f"      Chunk ID: {first_item['chunk_id']}")
            print(f"      Rank: {first_item['rank']}")
            print(f"      Confidence: {first_item['confidence']:.3f}")
            print(f"      Content preview: {first_item['content'][:100]}...")
        else:
            print("⚠️  No context items returned (may be expected if DB is empty)")
    
    def test_intent_classification(self, wait_for_api):
        """Test that intent classification works for known intents"""
        test_cases = [
            {
                "query": "How do I reset my password?",
                "expected_intent": "password_reset"
            },
            {
                "query": "I can't connect to remote desktop",
                "expected_intent": "rdp_issue"
            },
            {
                "query": "My disk is full",
                "expected_intent": "disk_issue"
            },
            {
                "query": "How do I add a new user?",
                "expected_intent": "user_management"
            },
        ]
        
        for test_case in test_cases:
            payload = {
                "query": test_case["query"],
                "user_id": "test_user"
            }
            
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json=payload,
                timeout=TIMEOUT
            )
            
            assert response.status_code == 200
            data = response.json()
            
            intent = data.get("intent")
            intent_confidence = data.get("intent_confidence", 0)
            
            # Check intent matches expected (or is at least not unknown if confidence is high)
            if intent_confidence > 0.3:
                assert intent == test_case["expected_intent"], \
                    f"Expected intent '{test_case['expected_intent']}', got '{intent}'"
            
            print(f"✅ Intent test passed:")
            print(f"   Query: {test_case['query']}")
            print(f"   Intent: {intent} (confidence: {intent_confidence:.2f})")
            print(f"   Expected: {test_case['expected_intent']}")
    
    def test_backward_compatibility(self, wait_for_api):
        """Test that 'context' field is still present for backward compatibility"""
        payload = {
            "query": "test query",
            "user_id": "test_user"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Old 'context' field should still exist
        assert "context" in data, "Response missing 'context' field (backward compatibility)"
        assert isinstance(data["context"], list), "'context' should be a list"
        
        print(f"✅ Backward compatibility maintained:")
        print(f"   context field present: {len(data['context'])} items")
        print(f"   context_with_metadata field present: {len(data.get('context_with_metadata', []))} items")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
