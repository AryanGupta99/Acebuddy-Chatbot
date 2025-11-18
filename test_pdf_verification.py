"""
Test chatbot with PDF-related queries
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

# PDF-related test queries
queries = [
    "How do I connect to a server drive using WebDAV on Windows?",
    "What are the steps to export reports from QuickBooks to Excel?",
    "How do I setup email in QuickBooks with Gmail?",
    "How can I publish a remote app on a local computer?",
    "Tell me about WebDAV connections",
    "QuickBooks report export process",
    "Remote app publishing steps",
    "Configuring Outlook in QuickBooks",
]

print("=" * 80)
print("TESTING PDF CHUNKS - CHATBOT VERIFICATION")
print("=" * 80)

results = []
successful = 0

for i, query in enumerate(queries, 1):
    print(f"\n[Query {i}/{len(queries)}]")
    print(f"Q: {query}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"query": query},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            confidence = data.get('confidence', 0)
            answer = data.get('answer', '')
            sources = data.get('sources', [])
            
            results.append({
                'query': query,
                'confidence': confidence,
                'answer_length': len(answer),
                'sources': len(sources)
            })
            
            # Track success (≥60% confidence)
            if confidence >= 0.60:
                successful += 1
                status = "✓ GOOD"
            else:
                status = "⚠ LOW"
            
            print(f"Confidence: {confidence:.1%} {status}")
            print(f"Answer: {answer[:100]}...")
            if sources:
                print(f"Sources: {len(sources)} | Top: {sources[0].get('title', 'Unknown')[:50]}")
        else:
            print(f"ERROR: HTTP {response.status_code}")
            results.append({'query': query, 'confidence': 0})
    
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Connection refused - Server not running")
        break
    except Exception as e:
        print(f"ERROR: {e}")
        results.append({'query': query, 'confidence': 0})
    
    time.sleep(1)

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
if results:
    avg_confidence = sum(r.get('confidence', 0) for r in results) / len(results)
    print(f"\nTotal queries tested: {len(results)}")
    print(f"Successful (≥60%): {successful}/{len(results)} ({successful*100/len(results):.0f}%)")
    print(f"Average confidence: {avg_confidence:.1%}")
    
    print(f"\nDetailed Results:")
    for i, r in enumerate(results, 1):
        status = "✓" if r.get('confidence', 0) >= 0.60 else "✗"
        print(f"  {i}. {status} {r['query'][:45]}... → {r.get('confidence', 0):.1%}")
    
    # Save results
    with open('pdf_test_verification.json', 'w') as f:
        json.dump({
            'total': len(results),
            'successful': successful,
            'success_rate': f"{successful*100/len(results):.1f}%",
            'avg_confidence': f"{avg_confidence:.1%}",
            'results': results
        }, f, indent=2)
    
    print(f"\n✓ Results saved: pdf_test_verification.json")
else:
    print("No results - could not connect to server")
