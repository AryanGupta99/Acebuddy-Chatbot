#!/usr/bin/env python
import requests
import sys

print("Starting test...")
sys.stdout.flush()

try:
    print("Connecting to chatbot...")
    sys.stdout.flush()
    
    response = requests.post(
        "http://127.0.0.1:8000/chat",
        json={"query": "How do I reset my password?", "session_id": "test1"},
        timeout=45
    )
    
    print(f"Response status: {response.status_code}")
    sys.stdout.flush()
    
    data = response.json()
    
    print("\n" + "="*70)
    print("QUERY: How do I reset my password?")
    print("="*70)
    print(f"\nRESPONSE:\n{data['answer']}")
    print(f"\nConfidence: {data['confidence']}%")
    print("="*70)
    
except requests.exceptions.Timeout:
    print("ERROR: Request timed out (server took too long)")
except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to server at http://127.0.0.1:8000")
    print("Is the server running?")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
