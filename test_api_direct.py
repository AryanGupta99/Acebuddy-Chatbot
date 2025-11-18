"""
Direct API test using requests library (no FastAPI test client).
"""

import json
import sys
import os
from pathlib import Path

# Ensure we can import dotenv
from dotenv import load_dotenv

load_dotenv()

# Use requests to call the API
try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system("pip install requests -q")
    import requests

# Make sure the app is running or start it
BASE_URL = "http://localhost:8000"

# Test queries
queries = [
    "How do I connect to a server drive using WebDAV?",
    "How to export QuickBooks reports to Excel?",
    "How do I setup email in QuickBooks?",
]

print("=" * 80)
print("TESTING PDF CHUNKS - API DIRECT TEST")
print("=" * 80)
print(f"Base URL: {BASE_URL}")

results = []
total_confidence = 0

for i, query in enumerate(queries, 1):
    print(f"\n[{i}] {query}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": query},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            confidence = data.get('confidence', 0)
            answer = data.get('response', '')
            sources = data.get('sources', [])
            
            total_confidence += confidence
            results.append({
                'query': query,
                'confidence': confidence,
                'sources': len(sources),
                'answer_preview': answer[:80]
            })
            
            print(f"    ✓ Confidence: {confidence:.1%}")
            print(f"    Answer: {answer[:100]}...")
            if sources:
                print(f"    Top source: {sources[0].get('title', 'Unknown')[:50]}")
            
        else:
            print(f"    ✗ HTTP {response.status_code}")
            print(f"    Response: {response.text[:200]}")
            results.append({'query': query, 'confidence': 0})
    
    except requests.exceptions.ConnectionError:
        print(f"    ✗ Connection failed - Is the app running on {BASE_URL}?")
        results.append({'query': query, 'confidence': 0, 'error': 'Connection refused'})
    except Exception as e:
        print(f"    ✗ ERROR: {e}")
        results.append({'query': query, 'confidence': 0, 'error': str(e)})

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
if results:
    avg_confidence = total_confidence / len(results)
    print(f"Average confidence: {avg_confidence:.1%}")
    print(f"\nResults:")
    for r in results:
        status = "✓" if r.get('confidence', 0) >= 0.65 else "✗"
        print(f"  {status} {r['query'][:40]}... → {r.get('confidence', 0):.1%}")
    
    # Save results
    with open('api_test_results.json', 'w') as f:
        json.dump({
            'avg_confidence': f"{avg_confidence:.1%}",
            'results': results
        }, f, indent=2)
    
    print(f"\n✓ Results saved to api_test_results.json")
else:
    print("No results collected")
