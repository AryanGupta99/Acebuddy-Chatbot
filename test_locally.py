#!/usr/bin/env python3
"""
LOCAL TESTING WITHOUT NGROK
This script lets you test the SalesIQ webhook locally without needing ngrok.
Perfect for verifying your setup works before connecting to SalesIQ.
"""

import requests
import json
from datetime import datetime

def test_salesiq_webhook():
    """Test the SalesIQ webhook endpoint"""
    
    BASE_URL = "http://localhost:8000"
    
    print("\n" + "="*70)
    print("ACEBUDDY RAG - LOCAL SALESIQ WEBHOOK TEST")
    print("="*70)
    
    # Check API is running
    print("\n1️⃣  Checking if API is running...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ API is running on localhost:8000")
        else:
            print(f"   ❌ API returned status {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Cannot reach API: {e}")
        print("   Make sure: python app/main_simple.py is running")
        return
    
    # Test queries
    test_cases = [
        {
            "name": "Password Reset Query",
            "payload": {
                "query": "How do I reset my password?",
                "visitor_id": "visitor_123",
                "chat_id": "chat_abc",
                "email": "user@example.com",
                "name": "John Doe"
            }
        },
        {
            "name": "WebDAV Access Query",
            "payload": {
                "query": "How do I access WebDAV?",
                "visitor_id": "visitor_456",
                "chat_id": "chat_def",
                "email": "user@example.com",
                "name": "Jane Smith"
            }
        },
        {
            "name": "QuickBooks Issue Query",
            "payload": {
                "query": "QuickBooks is not connecting",
                "visitor_id": "visitor_789",
                "chat_id": "chat_ghi",
                "email": "user@example.com",
                "name": "Bob Johnson"
            }
        }
    ]
    
    print("\n2️⃣  Testing SalesIQ webhook endpoint...")
    print("   Endpoint: POST /salesiq/chat\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {test['name']}")
        print(f"   Query: \"{test['payload']['query']}\"")
        
        try:
            response = requests.post(
                f"{BASE_URL}/salesiq/chat",
                json=test['payload'],
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {response.status_code}")
                print(f"   Answer: {data.get('answer', 'N/A')[:80]}...")
                print(f"   Confidence: {data.get('confidence', 'N/A')}")
                print(f"   Escalate: {data.get('should_escalate', 'N/A')}")
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test status endpoint
    print(f"\n3️⃣  Testing status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/salesiq/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   API Status: {data.get('status', 'N/A')}")
            print(f"   Documents: {data.get('documents_indexed', 'N/A')}")
        else:
            print(f"   ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test analytics endpoint
    print(f"\n4️⃣  Testing analytics endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/salesiq/analytics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   Total Messages: {data.get('total_messages', 'N/A')}")
            print(f"   Escalations: {data.get('escalations', 'N/A')}")
            print(f"   Escalation Rate: {data.get('escalation_rate', 'N/A')}")
        else:
            print(f"   ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*70)
    print("✅ LOCAL TESTING COMPLETE")
    print("="*70)
    print("\nNext steps for SalesIQ integration:")
    print("1. Since ngrok isn't working, use alternative tunneling:")
    print("   a) npm install -g localtunnel")
    print("      lt --port 8000")
    print("   b) Or ask IT to whitelist ngrok.com")
    print("   c) Or use IP-based access (less secure)")
    print("\n2. Once you have a public URL, configure in SalesIQ:")
    print("   Webhooks → Add → https://<your-url>/salesiq/chat")
    print("   Method: POST")
    print("   Headers: Content-Type: application/json")
    print("\n3. Test webhook in SalesIQ dashboard")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_salesiq_webhook()
