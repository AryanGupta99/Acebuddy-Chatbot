#!/usr/bin/env python3
"""
Start server and run tests all in one script
"""
import subprocess
import time
import requests
import sys

def wait_for_server(url="http://127.0.0.1:8000/health", max_wait=30):
    """Wait for server to be ready"""
    start = time.time()
    while time.time() - start < max_wait:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            pass
        print(".", end="", flush=True)
        time.sleep(1)
    return False

def run_tests():
    """Run chatbot tests"""
    queries = [
        "How do I reset my password?",
        "How do I troubleshoot RDP connection issues?",
        "How do I add a new user?",
    ]
    
    print("\n\n" + "="*80)
    print("RUNNING CHATBOT TESTS")
    print("="*80 + "\n")
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}] {query}")
        print("-" * 80)
        
        try:
            response = requests.post(
                "http://127.0.0.1:8000/chat",
                json={"query": query, "session_id": f"test_{i}"},
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS")
                print(f"Response: {data['answer'][:500]}...")
                print(f"Confidence: {data['confidence']}%\n")
            else:
                print(f"❌ Failed: HTTP {response.status_code}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    print("Starting server...")
    
    # Start the server
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("Waiting for server to start...")
    if wait_for_server():
        run_tests()
        print("\n✅ Tests complete!")
    else:
        print("\n❌ Server did not start in time")
    
    # Cleanup
    server_proc.terminate()
    print("Server stopped.")
