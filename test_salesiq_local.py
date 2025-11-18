#!/usr/bin/env python3
"""
Local SalesIQ Webhook Test
Test the integration without configuring in actual SalesIQ
"""

import requests
import json
import time

# Configuration
API_URL = "http://localhost:8000"
SALESIQ_CHAT_ENDPOINT = f"{API_URL}/salesiq/chat"

# Test queries
TEST_QUERIES = [
    {
        "query": "How do I reset my password?",
        "visitor_id": "test_visitor_1",
        "chat_id": "test_chat_1",
        "name": "Test User 1"
    },
    {
        "query": "How to connect WebDAV on Windows?",
        "visitor_id": "test_visitor_2",
        "chat_id": "test_chat_2",
        "name": "Test User 2"
    },
    {
        "query": "How to setup email in QuickBooks?",
        "visitor_id": "test_visitor_3",
        "chat_id": "test_chat_3",
        "name": "Test User 3"
    },
    {
        "query": "How to export reports from QuickBooks?",
        "visitor_id": "test_visitor_4",
        "chat_id": "test_chat_4",
        "name": "Test User 4"
    },
    {
        "query": "Unknown topic that should escalate",
        "visitor_id": "test_visitor_5",
        "chat_id": "test_chat_5",
        "name": "Test User 5"
    }
]


def test_health_check():
    """Test if API is running"""
    print("\n" + "="*60)
    print("🔍 HEALTH CHECK")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is running!")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print(f"   Make sure to run: python app/main.py")
        return False


def test_salesiq_status():
    """Test SalesIQ status endpoint"""
    print("\n" + "="*60)
    print("🔗 SALESIQ STATUS")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/salesiq/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SalesIQ integration ready!")
            print(f"   Status: {data.get('status')}")
            print(f"   Documents indexed: {data.get('documents_indexed', 'N/A')}")
            return True
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_single_query(query_data):
    """Test a single chat query"""
    print(f"\n📝 Query: {query_data['query']}")
    print("-" * 60)
    
    try:
        response = requests.post(
            SALESIQ_CHAT_ENDPOINT,
            json=query_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract key fields
            answer = data.get('answer', 'No answer')
            confidence = data.get('confidence', 0)
            should_escalate = data.get('should_escalate', False)
            sources = data.get('context_with_metadata', [])
            
            print(f"✅ Response received")
            print(f"   Confidence: {confidence:.2%}")
            print(f"   Escalate: {'Yes ⚠️' if should_escalate else 'No ✓'}")
            print(f"   Answer: {answer[:150]}...")
            print(f"   Sources: {len(sources)} found")
            
            return {
                'success': True,
                'confidence': confidence,
                'escalate': should_escalate,
                'sources': len(sources)
            }
        else:
            print(f"❌ API returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return {'success': False}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'success': False}


def test_all_queries():
    """Run all test queries"""
    print("\n" + "="*60)
    print("🧪 RUNNING TEST QUERIES")
    print("="*60)
    
    results = []
    for idx, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[{idx}/{len(TEST_QUERIES)}]")
        result = test_single_query(query)
        results.append(result)
        time.sleep(1)  # Small delay between requests
    
    return results


def test_batch_queries():
    """Test batch endpoint"""
    print("\n" + "="*60)
    print("📦 BATCH TEST")
    print("="*60)
    
    try:
        response = requests.post(
            f"{API_URL}/salesiq/batch",
            json=TEST_QUERIES[:3],
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Batch request successful")
            print(f"   Total: {data.get('total')}")
            print(f"   Successful: {data.get('successful')}")
            return True
        else:
            print(f"❌ Batch request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_analytics():
    """Test analytics endpoint"""
    print("\n" + "="*60)
    print("📊 ANALYTICS")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/salesiq/analytics", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analytics available")
            print(f"   Total messages: {data.get('total_messages', 0)}")
            print(f"   Escalations: {data.get('escalations', 0)}")
            print(f"   Escalation rate: {data.get('escalation_rate', '0%')}")
            return True
        else:
            print(f"❌ Analytics check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("📈 TEST SUMMARY")
    print("="*60)
    
    successful = sum(1 for r in results if r.get('success'))
    avg_confidence = sum(r.get('confidence', 0) for r in results) / len(results) if results else 0
    escalations = sum(1 for r in results if r.get('escalate'))
    
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"📊 Avg Confidence: {avg_confidence:.2%}")
    print(f"⚠️  Escalations: {escalations}")
    
    print("\n✨ Integration Test Complete!")


def main():
    """Run all tests"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     ACEBUDDY - ZOHO SALESIQ WEBHOOK LOCAL TEST            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ API is not running. Start it with: python app/main.py")
        return
    
    # Test 2: SalesIQ status
    if not test_salesiq_status():
        print("\n⚠️  SalesIQ integration not ready")
        return
    
    # Test 3: Run queries
    results = test_all_queries()
    
    # Test 4: Batch test
    test_batch_queries()
    
    # Test 5: Analytics
    test_analytics()
    
    # Summary
    print_summary(results)
    
    print("\n" + "="*60)
    print("🎯 NEXT STEPS:")
    print("="*60)
    print("1. If all tests pass ✅, configure webhook in SalesIQ")
    print("2. SalesIQ Settings → Integrations → Webhooks")
    print("3. Add URL: http://your-server:8000/salesiq/chat")
    print("4. Method: POST, Content-Type: application/json")
    print("5. Test webhook connection")
    print("="*60)


if __name__ == "__main__":
    main()
