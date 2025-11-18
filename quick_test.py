import requests

try:
    print("Testing chatbot...")
    r = requests.post("http://127.0.0.1:8000/chat", json={"query": "How do I reset my password?", "session_id": "test1"}, timeout=30)
    data = r.json()
    print(f"\n{'='*70}")
    print("QUERY: How do I reset my password?")
    print('='*70)
    print(f"\nRESPONSE:\n{data['answer']}")
    print(f"\nConfidence: {data['confidence']}%")
    print('='*70)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
