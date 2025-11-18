"""
Ingest manually processed PDF chunks into Chroma collection.
Merges new chunks with existing 92 chunks.
"""

import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

# Load environment
load_dotenv()

# Configuration
INPUT_CHUNKS = Path("data/manual_kb_chunks.json")
CHROMA_PATH = Path("data/chroma")
COLLECTION_NAME = "acebuddy_kb_v2"
EMBEDDING_MODEL = "text-embedding-3-small"


def load_chunks(filepath: Path) -> List[Dict]:
    """Load chunks from JSON file."""
    if not filepath.exists():
        print(f"ERROR: Chunks file not found: {filepath}")
        return []
    
    print(f"Loading chunks from: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    chunks = data.get('chunks', [])
    metadata = data.get('metadata', {})
    
    print(f"  Loaded {len(chunks)} chunks")
    print(f"  Metadata: {json.dumps(metadata, indent=2)}")
    
    return chunks


def ingest_chunks_to_chroma(chunks: List[Dict]):
    """Ingest chunks into Chroma collection."""
    print("\n[STEP 1] Connecting to Chroma...")
    
    # Initialize Chroma client using new API
    try:
        chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=Settings(anonymized_telemetry=False) if Settings else None
        )
    except Exception:
        # Fallback to older API
        try:
            if Settings:
                chroma_client = chromadb.Client(Settings(persist_directory=str(CHROMA_PATH), anonymized_telemetry=False))
            else:
                chroma_client = chromadb.Client()
        except Exception as e:
            print(f"ERROR: Failed to connect to Chroma: {e}")
            return False
    
    # Get or create collection
    print(f"[STEP 2] Getting collection: {COLLECTION_NAME}")
    
    try:
        collection = chroma_client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=None  # We have embeddings already
        )
        print(f"  Collection found")
        
        # Get current stats
        count_before = collection.count()
        print(f"  Documents before: {count_before}")
    except Exception as e:
        print(f"  Collection not found, creating new one...")
        collection = chroma_client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=None
        )
        count_before = 0
        print(f"  Created new collection")
    
    # Prepare data for ingestion
    print(f"\n[STEP 3] Preparing {len(chunks)} chunks for ingestion...")
    
    ids = []
    embeddings = []
    documents = []
    metadatas = []
    
    for i, chunk in enumerate(chunks):
        chunk_id = chunk.get('id', f'chunk_{i}')
        
        ids.append(chunk_id)
        embeddings.append(chunk['embedding'])
        documents.append(chunk['text'])
        
        # Prepare metadata
        metadata = {
            'title': chunk.get('title', 'Unknown'),
            'source': chunk.get('source', 'unknown'),
            'tokens': chunk.get('tokens', 0),
            'chunk_id': chunk.get('chunk_id', i)
        }
        metadatas.append(metadata)
        
        if (i + 1) % 100 == 0:
            print(f"  Prepared {i + 1}/{len(chunks)} chunks...")
    
    # Add chunks to collection
    print(f"\n[STEP 4] Adding chunks to collection...")
    
    try:
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        # Verify
        count_after = collection.count()
        print(f"  Documents before: {count_before}")
        print(f"  Documents added: {len(chunks)}")
        print(f"  Documents after: {count_after}")
        print(f"  ✓ Successfully added {len(chunks)} chunks")
        
    except Exception as e:
        print(f"  ERROR during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Persist changes
    print(f"\n[STEP 5] Persisting changes...")
    try:
        client.persist()
        print("  ✓ Changes persisted")
    except Exception as e:
        print(f"  Warning: Persist may not be available: {e}")
    
    return True


def verify_ingestion():
    """Verify that chunks were ingested correctly."""
    print("\n[STEP 6] Verifying ingestion...")
    
    try:
        chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=Settings(anonymized_telemetry=False) if Settings else None
        )
    except Exception:
        try:
            if Settings:
                chroma_client = chromadb.Client(Settings(persist_directory=str(CHROMA_PATH), anonymized_telemetry=False))
            else:
                chroma_client = chromadb.Client()
        except Exception as e:
            print(f"  ERROR: Failed to connect to Chroma: {e}")
            return False
    
    try:
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
        count = collection.count()
        
        print(f"  Total documents in collection: {count}")
        
        # Sample a chunk
        print(f"\n  Sampling recent chunks:")
        
        results = collection.get(limit=3)
        
        if results and results['ids']:
            for i, (chunk_id, doc, metadata) in enumerate(zip(
                results['ids'],
                results['documents'],
                results['metadatas']
            )):
                print(f"\n  Sample {i+1}: {chunk_id}")
                print(f"    Title: {metadata.get('title', 'Unknown')}")
                print(f"    Source: {metadata.get('source', 'unknown')}")
                print(f"    Tokens: {metadata.get('tokens', 0)}")
                print(f"    Text: {doc[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"  ERROR during verification: {e}")
        return False


def main():
    """Main ingestion pipeline."""
    print("=" * 80)
    print("CHROMA INGESTION PIPELINE")
    print("=" * 80)
    
    # Load chunks
    chunks = load_chunks(INPUT_CHUNKS)
    
    if not chunks:
        print("\nERROR: No chunks to ingest")
        return False
    
    # Ingest into Chroma
    success = ingest_chunks_to_chroma(chunks)
    
    if success:
        # Verify
        verify_ingestion()
        
        print("\n" + "=" * 80)
        print("✓ INGESTION COMPLETE")
        print("=" * 80)
        print(f"Successfully ingested {len(chunks)} chunks into Chroma")
        print(f"Collection: {COLLECTION_NAME}")
        print(f"Storage: {CHROMA_PATH}")
        
        return True
    else:
        print("\n✗ Ingestion failed")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
