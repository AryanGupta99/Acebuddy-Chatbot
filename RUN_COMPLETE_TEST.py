#!/usr/bin/env python3
"""
Standalone test - starts server and runs tests
"""
import subprocess
import time
import requests
import sys
import os

def wait_for_server(url="http://127.0.0.1:8000/health", max_wait=30):
    """Wait for server to be ready"""
    print("⏳ Waiting for server to start...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print("✅ Server is ready!\n")
                return True
        except:
            pass
        time.sleep(1)
    return False

print("\n" + "="*90)
print(" "*20 + "🚀 ACEBUDDY RAG CHATBOT - COMPLETE TEST")
print("="*90 + "\n")

# Start server
print("🔧 Starting FastAPI server in background...")
os.chdir(r"C:\Users\aryan.gupta\OneDrive - Real Time Data Services Pvt Ltd\Desktop\AceBuddy-RAG")

server_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

if not wait_for_server():
    print("❌ Server did not start!")
    sys.exit(1)

# Now run tests
print("=" * 90)
print("🧪 RUNNING TESTS\n")

queries = [
    ("How do I reset my password?", "Password Management"),
    ("How do I troubleshoot RDP connection issues?", "RDP Issues"),
    ("How do I add a new user?", "User Management"),
]

for i, (query, domain) in enumerate(queries, 1):
    print(f"[TEST {i}/3] {domain}")
    print("-" * 90)
    print(f"📝 Query: {query}\n")
    
    try:
        start = time.time()
        response = requests.post(
            "http://127.0.0.1:8000/chat",
            json={"query": query, "session_id": f"test_{i}"},
            timeout=120
        )
        elapsed = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS\n")
            print(f"💬 RESPONSE:")
            print("-" * 90)
            print(data['answer'])
            print("-" * 90)
            print(f"\n⏱️  Response Time: {elapsed:.0f}ms ({elapsed/1000:.1f}s)")
            print(f"📊 Confidence: {data.get('confidence', 0):.1f}%")
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 90 + "\n")
    time.sleep(1)

# Cleanup
server_proc.terminate()
print("✅ Test complete!\n")
