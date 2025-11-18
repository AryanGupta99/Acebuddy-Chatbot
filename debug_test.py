import requests
import json
import time

# Test the chatbot with detailed debugging
url = "http://127.0.0.1:8000/chat"

queries = [
    "How do I reset my password?",
    "How do I troubleshoot RDP connection issues?",
    "How do I add a new user?",
    "What is Acebuddy?"
]

print("=" * 60)
print("TESTING ACEBUDDY RAG CHATBOT")
print("=" * 60)

for i, query in enumerate(queries, 1):
    print(f"\n[{i}/{len(queries)}] Query: {query}")
    print("-" * 60)
    
    data = {
        "query": query,
        "session_id": f"test_{i}"
    }
    
    try:
        start = time.time()
        response = requests.post(url, json=data, timeout=30)
        elapsed = (time.time() - start) * 1000
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Status: SUCCESS")
            print(f"⏱️  Response Time: {elapsed:.0f}ms")
            print(f"📊 Confidence: {result.get('confidence', 0):.1f}%")
            print(f"📚 Contexts Used: {result.get('context_count', 0)}")
            print(f"🔄 Source: {result.get('source', 'unknown')}")
            
            response_text = result.get('response', '').strip()
            if response_text:
                print(f"\n💬 Response:")
                print(response_text[:500])  # First 500 chars
                if len(response_text) > 500:
                    print("... (truncated)")
            else:
                print(f"⚠️  EMPTY RESPONSE!")
                print(f"Full result: {json.dumps(result, indent=2)}")
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    time.sleep(0.5)  # Small delay between requests

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
