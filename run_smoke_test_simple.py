#!/usr/bin/env python3
"""Simple in-process smoke test runner that avoids SDK version conflicts."""

import json
import os
import sys
import asyncio
import time
from datetime import datetime

# Add the project root to path
proj_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, proj_root)
sys.path.insert(0, os.path.join(proj_root, 'scripts'))

# Import app components directly
from app.main import initialize_services, ChatRequest, chat

def main():
    """Run smoke tests."""
    print("Initializing services...")
    initialize_services()
    print("Services initialized successfully")
    
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
    
    async def run_queries():
        for i, q in enumerate(queries, start=1):
            print(f"\nQuery {i}/{len(queries)}: {q}")
            req = ChatRequest(
                query=q,
                session_id=f"local_smoke_{i}",
                use_history=False,
                enhance_query=True
            )
            try:
                resp = await chat(req)
                # Convert to dict
                try:
                    data = resp.model_dump()
                except Exception:
                    data = {
                        "answer": resp.answer,
                        "intent": resp.intent,
                        "intent_confidence": resp.intent_confidence,
                        "context": resp.context,
                        "context_with_metadata": resp.context_with_metadata,
                        "confidence": resp.confidence,
                        "session_id": resp.session_id,
                        "response_quality": resp.response_quality,
                        "query_enhanced": resp.query_enhanced
                    }
                print(f"  Answer length: {len(data.get('answer', ''))} chars")
                print(f"  Intent: {data.get('intent')} (conf: {data.get('intent_confidence', 0):.2f})")
                print(f"  Context items: {len(data.get('context_with_metadata', []))}")
            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()
                data = {"error": str(e)}
            
            results.append({
                "query": q,
                "timestamp": datetime.now().isoformat(),
                "response": data
            })
            
            time.sleep(0.5)
    
    # Run the async queries
    asyncio.run(run_queries())
    
    # Save results
    os.makedirs('data', exist_ok=True)
    out_path = os.path.join('data', 'smoke_test_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Smoke test complete! Wrote {len(results)} results to {out_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for i, r in enumerate(results, start=1):
        q = r['query'][:50]
        resp = r['response']
        if 'error' in resp:
            status = f"❌ {resp['error']}"
        else:
            intent = resp.get('intent', 'unknown')
            contexts = len(resp.get('context_with_metadata', []))
            answer = resp.get('answer', '')[:50]
            status = f"✅ Intent: {intent} | Contexts: {contexts} | Answer: {answer}..."
        print(f"{i}. {q} -> {status}")

if __name__ == '__main__':
    main()
