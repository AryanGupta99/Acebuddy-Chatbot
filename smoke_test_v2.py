#!/usr/bin/env python3
"""
Synchronous smoke test runner - avoids async/SSL issues
Tests with new atomic chunks to measure quality improvement
"""

import json
import os
import sys
import time
from datetime import datetime
import ssl

# Disable SSL verification for local testing
import urllib3
urllib3.disable_warnings()
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Add the project root to path
proj_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, proj_root)
sys.path.insert(0, os.path.join(proj_root, 'scripts'))

# Monkey-patch SSL before importing anything
import ssl
ssl.verify_mode = ssl.CERT_NONE

# Import app components directly
from app.main import initialize_services, retrieve_context, query_openai, ChatRequest
from app.main import embedding_model, collection
import logging

logging.basicConfig(level=logging.WARNING)  # Quiet logging

def test_smoke():
    """Run smoke tests synchronously"""
    
    print(f"\n{'='*70}")
    print("SMOKE TEST: NEW ATOMIC CHUNKS")
    print(f"{'='*70}\n")
    
    print("📌 Initializing services...")
    initialize_services()
    print("✅ Services initialized\n")
    
    queries = [
        "How do I reset my password?",
        "How can I increase disk storage on my server?",
        "My RDP connection keeps disconnecting, what should I check?",
        "Printer is not responding on Windows 10 — troubleshooting steps?",
        "How do I configure email (SMTP) for our application?",
        "How do I add or remove a user from the system?",
        "Server CPU is high — how to diagnose performance issues?",
        "QuickBooks shows data error on startup, what should I try?",
        "How do I set up a monitor for server alerts?",
        "Where can I find the AceBuddy support guide?"
    ]
    
    results = []
    
    for i, query in enumerate(queries, start=1):
        print(f"\n[{i}/{len(queries)}] Query: {query}")
        
        # Retrieve context
        context_result = retrieve_context(query, top_k=5, enhance=False)
        
        contexts = context_result.get('context_with_metadata', [])
        confidence = context_result.get('confidence', 0)
        
        print(f"    ✓ Retrieved {len(contexts)} contexts (confidence: {confidence:.3f})")
        
        # Generate answer using OpenAI
        system_prompt = """You are AceBuddy, an intelligent IT support chatbot. 
Use ONLY the provided context to answer user questions. 
If the context doesn't contain enough information, say 'I need to escalate this to our IT team.'
Be specific and actionable in your responses."""
        
        context_text = "\n".join([c['content'] for c in contexts])
        user_message = f"Question: {query}\n\nContext:\n{context_text}"
        
        try:
            answer = query_openai(
                system_message=system_prompt,
                user_message=user_message,
                model="gpt-4o-mini",
                temperature=0.2,
                max_tokens=512
            )
            print(f"    ✓ Generated answer ({len(answer)} chars)")
        except Exception as e:
            print(f"    ✗ Generation failed: {e}")
            answer = f"ERROR: {e}"
        
        # Compile result
        result = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "contexts": contexts,
            "confidence": confidence,
            "answer": answer,
            "answer_length": len(answer)
        }
        
        results.append(result)
        time.sleep(0.5)  # Rate limiting
    
    # Save results
    os.makedirs('data', exist_ok=True)
    out_path = os.path.join('data', 'smoke_test_results_v2.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"✅ SMOKE TEST COMPLETE!")
    print(f"{'='*70}")
    print(f"📊 Results saved to: {out_path}")
    print(f"📈 Total queries: {len(results)}")
    
    # Calculate statistics
    avg_confidence = sum(r['confidence'] for r in results) / len(results) if results else 0
    avg_contexts = sum(len(r['contexts']) for r in results) / len(results) if results else 0
    avg_answer_length = sum(r['answer_length'] for r in results) / len(results) if results else 0
    
    print(f"\n📊 STATISTICS:")
    print(f"  • Average confidence: {avg_confidence:.3f} (target: 0.60+)")
    print(f"  • Average contexts retrieved: {avg_contexts:.1f}")
    print(f"  • Average answer length: {avg_answer_length:.0f} chars")
    
    # Show per-query breakdown
    print(f"\n{'QUERY':<50} | {'CONF':>6} | {'CTX':>3} | {'ANSWER LEN':>10}")
    print("-" * 75)
    for r in results:
        q = r['query'][:47]
        conf = f"{r['confidence']:.3f}"
        ctx = str(len(r['contexts']))
        ans_len = str(r['answer_length'])
        print(f"{q:<50} | {conf:>6} | {ctx:>3} | {ans_len:>10}")
    
    print(f"\n{'='*70}\n")
    return results

if __name__ == "__main__":
    test_smoke()
