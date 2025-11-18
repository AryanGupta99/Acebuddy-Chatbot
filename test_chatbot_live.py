"""
Test the live chatbot with advanced features
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_chat(query, session_id="test_session"):
    """Test a chat query"""
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print('='*80)
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"query": query, "session_id": session_id}
        )
        
        elapsed = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Response (took {elapsed:.0f}ms):")
            print(f"Answer: {data.get('answer', 'N/A')}")
            print(f"\nMetadata:")
            print(f"  - Confidence: {data.get('confidence', 0):.2%}")
            print(f"  - Intent: {data.get('intent', 'unknown')}")
            print(f"  - Context docs: {len(data.get('context', []))}")
            if data.get('suggestions'):
                print(f"  - Suggestions: {', '.join(data['suggestions'])}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Server Health:")
            print(f"  Status: {data['status']}")
            print(f"  Documents: {data.get('documents_count', 'N/A')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    print("🚀 Testing AceBuddy Advanced RAG Chatbot")
    print("="*80)
    
    # Test health
    test_health()
    
    # Test queries
    test_queries = [
        "How do I reset my password?",  # Should hit Zobot knowledge
        "How do I reset my password?",  # Second time - should hit cache!
        "QuickBooks upgrade procedure",  # QuickBooks topic
        "RDP connection troubleshooting",  # Technical support
        "How to configure my zigzag feature?",  # Unknown - should trigger fallback
    ]
    
    for query in test_queries:
        test_chat(query)
        time.sleep(0.5)  # Small delay between requests
    
    print(f"\n{'='*80}")
    print("✅ Testing complete!")
    print("="*80)
