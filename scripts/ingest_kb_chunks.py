"""
Ingest KB article chunks into Chroma alongside existing atomic chunks
Creates unified knowledge base
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import chromadb
import time

# Load env
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# OpenAI embeddings
try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    MODEL = "text-embedding-3-small"
except Exception as e:
    print(f"❌ Error loading OpenAI: {e}")
    sys.exit(1)

def get_embeddings(texts):
    """Get OpenAI embeddings for texts"""
    if not isinstance(texts, list):
        texts = [texts]
    
    try:
        response = client.embeddings.create(
            model=MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        return None

def ingest_kb_chunks():
    """Load KB chunks and ingest into Chroma"""
    
    print(f"\n{'='*80}")
    print(f"INGESTING KB ARTICLE CHUNKS INTO CHROMA")
    print(f"{'='*80}\n")
    
    proj_root = Path(__file__).parent.parent
    chunks_file = proj_root / "data" / "kb_article_chunks.json"
    chroma_dir = proj_root / "data" / "chroma"
    collection_name = "acebuddy_kb_v2"
    
    # Load chunks
    print(f"📖 Loading KB chunks from: {chunks_file.name}")
    if not chunks_file.exists():
        print(f"❌ Chunks file not found: {chunks_file}")
        print(f"Please run: python scripts/chunk_kb_articles.py")
        return False
    
    with open(chunks_file, 'r', encoding='utf-8') as f:
        kb_chunks = json.load(f)
    
    print(f"✅ Loaded {len(kb_chunks)} KB article chunks\n")
    
    # Connect to Chroma
    print(f"🔌 Connecting to Chroma at: {chroma_dir}")
    chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
    
    # Get existing collection
    try:
        collection = chroma_client.get_collection(collection_name)
        existing_count = collection.count()
        print(f"✅ Connected to existing collection with {existing_count} documents\n")
    except Exception as e:
        print(f"❌ Could not connect to collection: {e}")
        return False
    
    # Prepare data
    print(f"📝 Preparing {len(kb_chunks)} chunks for embedding...")
    
    ids = []
    documents = []
    metadatas = []
    
    for chunk in kb_chunks:
        ids.append(chunk['id'])
        documents.append(chunk['content'])
        metadatas.append(chunk['metadata'])
    
    print(f"✅ Prepared {len(documents)} documents\n")
    
    # Get embeddings
    print(f"🚀 Generating OpenAI embeddings (batch processing)...")
    embeddings = []
    batch_size = 25
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        batch_idx = i // batch_size + 1
        total_batches = (len(documents) - 1) // batch_size + 1
        
        print(f"   Batch {batch_idx}/{total_batches}: embedding {len(batch)} chunks...", end='', flush=True)
        
        batch_embeddings = get_embeddings(batch)
        if batch_embeddings:
            embeddings.extend(batch_embeddings)
            print(f" ✓ ({len(embeddings)}/{len(documents)})")
        else:
            print(f" ✗ FAILED")
            return False
        
        time.sleep(0.5)  # Rate limiting
    
    print(f"\n✅ Generated {len(embeddings)} embeddings (dimension: {len(embeddings[0])})\n")
    
    # Ingest into Chroma
    print(f"💾 Adding chunks to Chroma collection...")
    try:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        print(f"✅ Ingestion successful!\n")
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        return False
    
    # Verify
    new_count = collection.count()
    added = new_count - existing_count
    
    print(f"{'='*80}")
    print(f"📊 VERIFICATION")
    print(f"{'='*80}")
    print(f"✅ Documents before:      {existing_count}")
    print(f"✅ Documents added:       {added}")
    print(f"✅ Total documents now:   {new_count}")
    print(f"✅ Collection name:       {collection_name}")
    print(f"✅ Embedding dimension:   {len(embeddings[0])}")
    print(f"✅ Ready for RAG queries\n")
    
    return True

if __name__ == "__main__":
    print("\n⚠️  NOTE: This script requires KB article chunks to be prepared.")
    print("Make sure you have:")
    print("  1. Downloaded Excel file")
    print("  2. Extracted KB article links")
    print("  3. Downloaded all KB articles")
    print("  4. Cleaned and preprocessed the data")
    print("  5. Created atomic chunks")
    print("\nFor a complete walkthrough, run:")
    print("  python scripts/process_kb_articles.py")
    print("  python scripts/chunk_kb_articles.py")
    print("  python scripts/ingest_kb_chunks.py\n")
    
    success = ingest_kb_chunks()
    sys.exit(0 if success else 1)
