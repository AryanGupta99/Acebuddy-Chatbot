#!/usr/bin/env python3
"""Direct test of atomic chunks without async/SSL issues"""

import json
import os
import sys
import io

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

proj_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, proj_root)

# Set SSL verify to false BEFORE any imports
os.environ['PYTHONHTTPSVERIFY'] = '0'

print("Importing modules...")
try:
    import chromadb
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test 1: Can we connect to Chroma?
    print("\n[TEST 1] Connecting to Chroma...")
    chroma_dir = os.path.join(proj_root, "data", "chroma")
    client = chromadb.PersistentClient(path=chroma_dir)
    
    collection = client.get_collection("acebuddy_kb_v2")
    count = collection.count()
    print(f"✅ Connected! Collection has {count} documents\n")
    
    # Test 2: Can we embed a query?
    print("[TEST 2] Testing OpenAI embeddings...")
    from openai import OpenAI
    api_key = os.getenv('OPENAI_API_KEY')
    
    oai_client = OpenAI(api_key=api_key)
    test_query = "How do I reset my password?"
    
    emb_response = oai_client.embeddings.create(
        model="text-embedding-3-small",
        input=[test_query]
    )
    embedding = emb_response.data[0].embedding
    print(f"✅ Got embedding (dim: {len(embedding)})\n")
    
    # Test 3: Can we retrieve?
    print("[TEST 3] Retrieving context for test query...")
    results = collection.query(
        query_embeddings=[embedding],
        n_results=5
    )
    
    print(f"✅ Retrieved {len(results['documents'][0])} contexts\n")
    
    # Show top result
    print("[TOP CONTEXT]")
    top_doc = results['documents'][0][0]
    print(f"{top_doc[:200]}...\n")
    
    # Calculate confidence
    distances = results['distances'][0]
    avg_distance = sum(distances) / len(distances)
    confidence = 1 / (1 + avg_distance)  # Convert to confidence score
    print(f"Average distance: {avg_distance:.4f}")
    print(f"Confidence: {confidence:.4f}\n")
    
    # Test 4: Test a few queries
    print("[TEST 4] Testing multiple queries...\n")
    
    test_queries = [
        "How do I reset my password?",
        "How can I increase disk storage?",
        "My RDP connection keeps disconnecting",
    ]
    
    for q in test_queries:
        emb = oai_client.embeddings.create(
            model="text-embedding-3-small",
            input=[q]
        ).data[0].embedding
        
        results = collection.query(
            query_embeddings=[emb],
            n_results=5,
            include=['documents', 'metadatas', 'distances']
        )
        
        distances = results['distances'][0]
        avg_dist = sum(distances) / len(distances)
        conf = 1 / (1 + avg_dist)
        
        # Show what was retrieved
        print(f"Query: {q}")
        print(f"  Confidence: {conf:.4f}")
        print(f"  Top result: {results['documents'][0][0][:80]}...")
        print()
    
    print("\n✅ ALL TESTS PASSED!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
