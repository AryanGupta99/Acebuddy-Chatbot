"""
Simple test - check actual response format
"""
import requests
import json

BASE_URL = "http://localhost:8000"

query = "How do I connect to a server drive using WebDAV on Windows?"

print(f"Testing: {query}\n")

try:
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"query": query},
        timeout=45
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
except Exception as e:
    print(f"ERROR: {e}")
