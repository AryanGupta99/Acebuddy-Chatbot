"""
Ingest atomic chunks into Chroma with OpenAI embeddings
- Clear old collection (acebuddy_kb_v2)
- Create new collection
- Embed and ingest 92 atomic chunks
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
CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma"
ATOMIC_CHUNKS_FILE = Path(__file__).parent.parent / "data" / "atomic_chunks.json"

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

def ingest_atomic_chunks():
    """Load atomic chunks and ingest into Chroma"""
    
    print(f"\n{'='*70}")
    print(f"ATOMIC CHUNKS INGESTION PIPELINE")
    print(f"{'='*70}\n")
    
    # Load chunks
    print(f"📖 Loading atomic chunks from: {ATOMIC_CHUNKS_FILE}")
    with open(ATOMIC_CHUNKS_FILE, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"✅ Loaded {len(chunks)} atomic chunks\n")
    
    # Connect to Chroma
    print(f"🔌 Connecting to Chroma at: {CHROMA_DIR}")
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Delete old collection if exists
    collection_name = "acebuddy_kb_v2"
    try:
        chroma_client.delete_collection(collection_name)
        print(f"🗑️  Deleted old collection: {collection_name}")
    except Exception as e:
        print(f"ℹ️  Old collection not found (OK): {e}")
    
    time.sleep(1)
    
    # Create new collection
    print(f"✨ Creating new collection: {collection_name}")
    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Prepare data
    print(f"\n📝 Preparing {len(chunks)} chunks for embedding...")
    
    ids = []
    documents = []
    metadatas = []
    
    for i, chunk in enumerate(chunks):
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
        print(f"   Batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}: embedding {len(batch)} chunks...", end='', flush=True)
        
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
    print(f"💾 Ingesting into Chroma...")
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
    count = collection.count()
    print(f"{'='*70}")
    print(f"📊 VERIFICATION")
    print(f"{'='*70}")
    print(f"✅ Total documents in collection: {count}")
    print(f"✅ Collection name: {collection_name}")
    print(f"✅ Embedding dimension: {len(embeddings[0])}")
    print(f"✅ Ready for RAG queries\n")
    
    return True

if __name__ == "__main__":
    success = ingest_atomic_chunks()
    sys.exit(0 if success else 1)
