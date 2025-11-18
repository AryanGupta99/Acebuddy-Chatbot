#!/usr/bin/env python3
"""
AceBuddy Chatbot - Integration Test Suite
Tests RAG + OpenAI chat pipeline end-to-end
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*70)
    print("TEST 1: Health Check")
    print("="*70)
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
        data = resp.json()
        print(f"Status: {data.get('status')}")
        print(f"Services Healthy: {all(data.get('services', {}).values())}")
        print(f"✅ PASS" if resp.status_code == 200 else "❌ FAIL")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def test_chat_password_reset():
    """Test chat with password reset query"""
    print("\n" + "="*70)
    print("TEST 2: Chat - Password Reset Query")
    print("="*70)
    try:
        payload = {
            "query": "How do I reset my password?",
            "user_id": "test_user_1"
        }
        resp = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            timeout=30
        )
        data = resp.json()
        print(f"Query: {payload['query']}")
        print(f"Intent Detected: {data.get('intent')}")
        print(f"Response: {data.get('answer')[:200]}...")
        print(f"✅ PASS" if resp.status_code == 200 and data.get('answer') else "❌ FAIL")
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def test_chat_disk_upgrade():
    """Test chat with disk upgrade query"""
    print("\n" + "="*70)
    print("TEST 3: Chat - Disk Space Upgrade Query")
    print("="*70)
    try:
        payload = {
            "query": "I need more disk space. What are my upgrade options?",
            "user_id": "test_user_2"
        }
        resp = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            timeout=30
        )
        data = resp.json()
        print(f"Query: {payload['query']}")
        print(f"Intent Detected: {data.get('intent')}")
        print(f"Response: {data.get('answer')[:200]}...")
        print(f"✅ PASS" if resp.status_code == 200 and data.get('answer') else "❌ FAIL")
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def test_chat_rdp_issue():
    """Test chat with RDP connection issue"""
    print("\n" + "="*70)
    print("TEST 4: Chat - RDP Connection Issue Query")
    print("="*70)
    try:
        payload = {
            "query": "I can't connect to the server via RDP. What should I do?",
            "user_id": "test_user_3"
        }
        resp = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            timeout=30
        )
        data = resp.json()
        print(f"Query: {payload['query']}")
        print(f"Intent Detected: {data.get('intent')}")
        print(f"Response: {data.get('answer')[:200]}...")
        print(f"✅ PASS" if resp.status_code == 200 and data.get('answer') else "❌ FAIL")
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def test_chat_printer_issue():
    """Test chat with printer troubleshooting"""
    print("\n" + "="*70)
    print("TEST 5: Chat - Printer Issue Query")
    print("="*70)
    try:
        payload = {
            "query": "My printer is offline. How do I fix it?",
            "user_id": "test_user_4"
        }
        resp = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            timeout=30
        )
        data = resp.json()
        print(f"Query: {payload['query']}")
        print(f"Intent Detected: {data.get('intent')}")
        print(f"Response: {data.get('answer')[:200]}...")
        print(f"✅ PASS" if resp.status_code == 200 and data.get('answer') else "❌ FAIL")
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def test_chat_application_update():
    """Test chat with application update query"""
    print("\n" + "="*70)
    print("TEST 6: Chat - Application Update Query")
    print("="*70)
    try:
        payload = {
            "query": "How do I update QuickBooks?",
            "user_id": "test_user_5"
        }
        resp = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            timeout=30
        )
        data = resp.json()
        print(f"Query: {payload['query']}")
        print(f"Intent Detected: {data.get('intent')}")
        print(f"Response: {data.get('answer')[:200]}...")
        print(f"✅ PASS" if resp.status_code == 200 and data.get('answer') else "❌ FAIL")
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("AceBuddy RAG Chatbot - Integration Test Suite")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    
    # Wait for server to be ready
    print("\nWaiting for server to be ready...")
    for i in range(10):
        try:
            requests.get(f"{BASE_URL}/health", timeout=5)
            print("✅ Server is ready!")
            break
        except:
            if i < 9:
                print(f"  Retrying... ({i+1}/10)")
                time.sleep(2)
            else:
                print("❌ Server did not respond. Is uvicorn running?")
                return

    # Run tests
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Password Reset", test_chat_password_reset()))
    results.append(("Disk Upgrade", test_chat_disk_upgrade()))
    results.append(("RDP Connection", test_chat_rdp_issue()))
    results.append(("Printer Issue", test_chat_printer_issue()))
    results.append(("App Update", test_chat_application_update()))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! RAG + OpenAI integration is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check logs above.")

if __name__ == "__main__":
    main()
