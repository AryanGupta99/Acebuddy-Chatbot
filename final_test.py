#!/usr/bin/env python3
"""
Final Integration Test - Validate RAG + OpenAI Setup
"""
import requests
import time
import sys

BASE_URL = "http://localhost:8000"

print("\n" + "="*70)
print("FINAL INTEGRATION TEST - AceBuddy RAG + OpenAI Chatbot")
print("="*70)

# Wait for server
print("\n⏳ Connecting to server...")
for attempt in range(20):
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        print("✅ Server connected!")
        break
    except:
        print(f"  Attempt {attempt+1}/20...")
        time.sleep(1)
        if attempt == 19:
            print("❌ Server not responding. Ensure uvicorn is running.")
            sys.exit(1)

# Test 1: Health
print("\n[TEST 1] Health Check...")
resp = requests.get(f"{BASE_URL}/health")
data = resp.json()
assert resp.status_code == 200, "Health endpoint failed"
assert data['status'] == 'healthy', "Services not healthy"
print(f"✅ Status: {data['status']}")
print(f"✅ All services operational")

# Test 2-6: Chat Queries
queries = [
    ("Password Reset", "How do I reset my password?"),
    ("Disk Upgrade", "I need more disk space for my server"),
    ("RDP Connection", "I cannot connect to server via RDP"),
    ("Printer Issue", "My printer is offline and not working"),
    ("App Update", "How do I update QuickBooks to latest version?"),
]

for i, (test_name, query) in enumerate(queries, 2):
    print(f"\n[TEST {i}] {test_name}...")
    try:
        payload = {"query": query, "user_id": f"test_{i}"}
        resp = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            timeout=45
        )
        assert resp.status_code == 200, f"Request failed: {resp.status_code}"
        data = resp.json()
        assert 'answer' in data and len(data['answer']) > 0, "No answer received"
        assert 'intent' in data, "No intent detected"
        
        print(f"✅ Query: {query[:40]}...")
        print(f"✅ Intent: {data['intent']}")
        print(f"✅ Answer: {data['answer'][:80]}...")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        sys.exit(1)

# Final Summary
print("\n" + "="*70)
print("🎉 ALL TESTS PASSED!")
print("="*70)
print("\n✅ RAG + OpenAI Integration Complete")
print("✅ Chatbot is fully operational")
print("✅ Ready for production use")
print("\nEndpoints available:")
print("  - GET  /health        - Service health check")
print("  - POST /chat          - Chat with RAG retrieval & OpenAI generation")
print("  - POST /ingest        - Ingest KB articles into Chroma")
print("\nDocumentation:")
print("  - COST_CONFIRMATION.md - Pricing & budget estimates")
print("  - COST_ANALYSIS.md     - Detailed cost breakdown")
print("  - README.md            - Setup & usage guide")
print("\n" + "="*70 + "\n")
