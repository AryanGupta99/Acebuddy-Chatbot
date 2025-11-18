"""
Quick direct test of the ingested PDF chunks.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import FastAPI app
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test queries for PDF topics
queries = [
    "How do I connect to a server drive using WebDAV?",
    "How to export QuickBooks reports to Excel?",
    "How do I setup email in QuickBooks?",
    "What are the steps to publish remote apps?",
]

print("=" * 80)
print("TESTING PDF CHUNKS INTEGRATION")
print("=" * 80)

results = []
total_confidence = 0

for i, query in enumerate(queries, 1):
    print(f"\n[{i}] {query}")
    
    try:
        response = client.post("/chat", json={"message": query}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            confidence = data.get('confidence', 0)
            answer = data.get('response', '')
            sources = data.get('sources', [])
            
            total_confidence += confidence
            results.append({
                'query': query,
                'confidence': confidence,
                'sources': len(sources)
            })
            
            print(f"    Confidence: {confidence:.1%}")
            print(f"    Answer: {answer[:100]}...")
            if sources:
                print(f"    Source: {sources[0].get('title', 'Unknown')}")
            
        else:
            print(f"    ERROR: {response.status_code}")
            results.append({'query': query, 'confidence': 0})
    
    except Exception as e:
        print(f"    ERROR: {e}")
        results.append({'query': query, 'confidence': 0})

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
avg_confidence = total_confidence / len(queries)
print(f"Average confidence: {avg_confidence:.1%}")
print(f"Results:")
for r in results:
    print(f"  • {r['query'][:50]}... → {r['confidence']:.1%}")

# Save results
with open('manual_pdf_test_results.json', 'w') as f:
    json.dump({
        'avg_confidence': f"{avg_confidence:.1%}",
        'results': results
    }, f, indent=2)

print(f"\n✓ Results saved to manual_pdf_test_results.json")
