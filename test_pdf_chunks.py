"""
Test the chatbot with the newly ingested PDF chunks.
Evaluate response quality and confidence scores.
"""

import os
import sys
from pathlib import Path
import json
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from app.main import app
from fastapi.testclient import TestClient

# Load environment
load_dotenv()

# Test queries focused on the new PDF topics
TEST_QUERIES = [
    "How do I connect to a server drive using WebDAV on Windows?",
    "What are the steps to export reports from QuickBooks to Excel?",
    "How do I publish a remote app on a local computer?",
    "How can I setup email in QuickBooks with Gmail?",
    "What is WebDAV and how is it used?",
    "Can you explain the QuickBooks export process?",
    "What is remote app publishing?",
    "How do I configure Outlook with QuickBooks?",
    "What's the process for WebDAV connection?",
    "Tell me about QuickBooks email integration"
]

def run_tests():
    """Run comprehensive tests on the chatbot."""
    print("=" * 80)
    print("CHATBOT TEST SUITE - PDF CHUNKS")
    print("=" * 80)
    
    client = TestClient(app)
    
    results = []
    total_confidence = 0
    min_confidence = 100
    max_confidence = 0
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[Query {i}/{len(TEST_QUERIES)}] {query}")
        
        try:
            # Send request to chatbot
            response = client.post(
                "/chat",
                json={"message": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract response and confidence
                answer = data.get('response', '')
                confidence = data.get('confidence', 0)
                sources = data.get('sources', [])
                
                # Track metrics
                total_confidence += confidence
                min_confidence = min(min_confidence, confidence)
                max_confidence = max(max_confidence, confidence)
                
                # Store result
                results.append({
                    'query': query,
                    'confidence': confidence,
                    'answer_length': len(answer),
                    'sources_count': len(sources),
                    'status': 'SUCCESS' if confidence >= 0.65 else 'LOW_CONFIDENCE'
                })
                
                # Print result
                print(f"  Confidence: {confidence:.1%}")
                print(f"  Answer length: {len(answer)} chars")
                print(f"  Sources: {len(sources)}")
                print(f"  Status: {'✓ GOOD' if confidence >= 0.65 else '⚠ LOW'}")
                
                # Show snippet
                if answer:
                    print(f"  Answer: {answer[:150]}...")
                
                # Show sources
                if sources:
                    print(f"  Top source: {sources[0].get('title', 'Unknown')[:60]}...")
                
            else:
                print(f"  ERROR: HTTP {response.status_code}")
                results.append({
                    'query': query,
                    'confidence': 0,
                    'status': 'ERROR',
                    'error': response.text
                })
        
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                'query': query,
                'confidence': 0,
                'status': 'ERROR',
                'error': str(e)
            })
    
    # Calculate statistics
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    successful = [r for r in results if r.get('confidence', 0) >= 0.65]
    avg_confidence = total_confidence / len(TEST_QUERIES) if TEST_QUERIES else 0
    
    print(f"\nTotal queries: {len(TEST_QUERIES)}")
    print(f"Successful (≥65%): {len(successful)}/{len(TEST_QUERIES)} ({len(successful)*100/len(TEST_QUERIES):.1f}%)")
    print(f"\nConfidence Scores:")
    print(f"  Average: {avg_confidence:.1%}")
    print(f"  Minimum: {min_confidence:.1%}")
    print(f"  Maximum: {max_confidence:.1%}")
    
    # Detailed breakdown
    print(f"\nDetailed Results:")
    for i, result in enumerate(results, 1):
        status = "✓" if result['status'] == 'SUCCESS' else "✗" if result['status'] == 'ERROR' else "⚠"
        print(f"  {i}. {status} {result['query'][:50]}... → {result.get('confidence', 0):.1%}")
    
    # Save results
    output_file = Path('pdf_test_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_queries': len(TEST_QUERIES),
                'successful': len(successful),
                'success_rate': f"{len(successful)*100/len(TEST_QUERIES):.1f}%",
                'average_confidence': f"{avg_confidence:.1%}",
                'min_confidence': f"{min_confidence:.1%}",
                'max_confidence': f"{max_confidence:.1%}"
            },
            'results': results
        }, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    try:
        results = run_tests()
        
        # Exit with success if most queries had good confidence
        successful = [r for r in results if r.get('confidence', 0) >= 0.65]
        if len(successful) >= len(results) * 0.6:  # 60% pass rate
            print("\n✓ Test suite PASSED")
            sys.exit(0)
        else:
            print("\n⚠ Test suite had low confidence scores")
            sys.exit(1)
    
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
