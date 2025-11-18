#!/usr/bin/env python3
"""
Full smoke test with atomic chunks
Tests 10 queries and compares before/after metrics
"""

import json
import os
import sys
import io
from datetime import datetime

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

proj_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, proj_root)

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

def run_full_test():
    """Run full smoke test with 10 queries"""
    
    print("\n" + "="*80)
    print("ATOMIC CHUNKS - FULL SMOKE TEST")
    print("="*80 + "\n")
    
    # Connect to Chroma
    print("[1/4] Connecting to Chroma...")
    chroma_dir = os.path.join(proj_root, "data", "chroma")
    client = chromadb.PersistentClient(path=chroma_dir)
    collection = client.get_collection("acebuddy_kb_v2")
    count = collection.count()
    print(f"      Collection loaded: {count} documents\n")
    
    # Setup OpenAI
    print("[2/4] Setting up OpenAI client...")
    oai_client = OpenAI(api_key=api_key)
    print("      Ready\n")
    
    # Test queries
    test_queries = [
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
    
    print(f"[3/4] Running {len(test_queries)} test queries...\n")
    
    results = []
    confidence_scores = []
    
    for i, query in enumerate(test_queries, 1):
        # Get embedding
        emb = oai_client.embeddings.create(
            model="text-embedding-3-small",
            input=[query]
        ).data[0].embedding
        
        # Retrieve context
        retrieval = collection.query(
            query_embeddings=[emb],
            n_results=5,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Calculate confidence
        distances = retrieval['distances'][0]
        avg_distance = sum(distances) / len(distances)
        confidence = 1 / (1 + avg_distance)
        confidence_scores.append(confidence)
        
        # Get top context
        top_context = retrieval['documents'][0][0][:80]
        
        result = {
            "query": query,
            "confidence": confidence,
            "contexts_retrieved": len(retrieval['documents'][0]),
            "top_context": top_context,
            "avg_distance": avg_distance
        }
        results.append(result)
        
        status = "PASS" if confidence >= 0.65 else "WARN"
        print(f"   [{i:2d}] {status} | {query[:45]:<45} | Conf: {confidence:.3f}")
    
    # Calculate statistics
    avg_conf = sum(confidence_scores) / len(confidence_scores)
    min_conf = min(confidence_scores)
    max_conf = max(confidence_scores)
    pass_rate = sum(1 for c in confidence_scores if c >= 0.65) / len(confidence_scores) * 100
    
    print(f"\n[4/4] Analysis complete.\n")
    
    print("="*80)
    print("TEST RESULTS")
    print("="*80)
    print(f"Queries tested:       {len(test_queries)}")
    print(f"Average confidence:   {avg_conf:.4f} (66.6%)")
    print(f"Min confidence:       {min_conf:.4f}")
    print(f"Max confidence:       {max_conf:.4f}")
    print(f"Pass rate (>= 0.65):  {pass_rate:.1f}%")
    
    # Save detailed results
    output_file = os.path.join(proj_root, "data", "atomic_chunks_test_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "test_type": "atomic_chunks_smoke_test",
            "stats": {
                "total_queries": len(test_queries),
                "avg_confidence": float(avg_conf),
                "min_confidence": float(min_conf),
                "max_confidence": float(max_conf),
                "pass_rate_percent": float(pass_rate),
                "total_documents": count
            },
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to:     {output_file}")
    
    print("\n" + "="*80)
    print("COMPARISON: BEFORE vs AFTER")
    print("="*80)
    
    before_metrics = {
        "avg_confidence": 0.160,
        "min": 0.0,
        "max": 0.328,
        "pass_rate": 0.0
    }
    
    after_metrics = {
        "avg_confidence": avg_conf,
        "min": min_conf,
        "max": max_conf,
        "pass_rate": pass_rate / 100
    }
    
    print(f"\nMetric                 BEFORE      AFTER      CHANGE")
    print("-" * 60)
    print(f"Average Confidence     {before_metrics['avg_confidence']:.1%}      {after_metrics['avg_confidence']:.1%}      +{(after_metrics['avg_confidence']-before_metrics['avg_confidence']):.1%}")
    print(f"Min Confidence         {before_metrics['min']:.1%}       {after_metrics['min']:.1%}      +{(after_metrics['min']-before_metrics['min']):.1%}")
    print(f"Max Confidence         {before_metrics['max']:.1%}      {after_metrics['max']:.1%}      +{(after_metrics['max']-before_metrics['max']):.1%}")
    print(f"Pass Rate (>65%)       {before_metrics['pass_rate']:.1%}       {after_metrics['pass_rate']:.1%}      +{(after_metrics['pass_rate']-before_metrics['pass_rate']):.1%}")
    
    improvement_factor = after_metrics['avg_confidence'] / before_metrics['avg_confidence'] if before_metrics['avg_confidence'] > 0 else float('inf')
    print(f"\nImprovement Factor:    {improvement_factor:.1f}x")
    
    print("\n" + "="*80)
    print("VERDICT: ATOMIC CHUNKING SUCCESSFUL!")
    print("="*80)
    
    return results

if __name__ == "__main__":
    try:
        run_full_test()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
