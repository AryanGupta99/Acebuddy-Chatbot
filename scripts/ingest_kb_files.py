"""
Ingest the actual KB markdown files into ChromaDB
These have better structured content than the Zobot data
"""
import sys
import os
from pathlib import Path
import hashlib
import chromadb
from chromadb.config import Settings

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# DummyEmbedding class (same as in main.py)
class DummyEmbedding:
    """Fallback embedding using hash-based vectors"""
    def encode(self, text):
        """Generate a deterministic vector from text hash"""
        hash_bytes = hashlib.sha256(text.encode('utf-8')).digest()
        vector = [b / 255.0 for b in hash_bytes[:384]]  # Normalize to [0,1]
        # Pad to 384 dimensions if needed
        while len(vector) < 384:
            vector.append(0.0)
        return [vector]  # Return 2D array like SentenceTransformer

def chunk_text(text: str, max_length: int = 1000) -> list:
    """Split text into chunks by sections"""
    chunks = []
    
    # Split by markdown headers
    sections = text.split('\n## ')
    
    for i, section in enumerate(sections):
        if i > 0:
            section = '## ' + section  # Re-add header
        
        # If section is too long, split by paragraphs
        if len(section) > max_length:
            paragraphs = section.split('\n\n')
            current_chunk = ""
            
            for para in paragraphs:
                if len(current_chunk) + len(para) > max_length and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = para
                else:
                    current_chunk += "\n\n" + para if current_chunk else para
            
            if current_chunk:
                chunks.append(current_chunk.strip())
        else:
            chunks.append(section.strip())
    
    return [c for c in chunks if len(c.strip()) > 50]  # Filter out tiny chunks

def main():
    print("=" * 70)
    print("INGESTING KB MARKDOWN FILES INTO CHROMADB")
    print("=" * 70)
    
    # Initialize embedder
    print("\n📦 Initializing DummyEmbedding...")
    embedder = DummyEmbedding()
    
    # Initialize ChromaDB
    chroma_dir = Path(__file__).parent.parent / "data" / "chroma"
    chroma_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 Connecting to ChromaDB at: {chroma_dir}")
    client = chromadb.PersistentClient(path=str(chroma_dir))
    
    # Get or create collection
    collection = client.get_or_create_collection(
        name="acebuddy_kb",
        metadata={"description": "AceBuddy knowledge base"}
    )
    
    print(f"✓ Collection: acebuddy_kb (existing documents: {collection.count()})")
    
    # Find KB files
    kb_dir = Path(__file__).parent.parent / "data" / "kb"
    if not kb_dir.exists():
        print(f"❌ KB directory not found: {kb_dir}")
        return
    
    kb_files = list(kb_dir.glob("*.md"))
    print(f"\n📚 Found {len(kb_files)} KB files")
    
    # Ingest each file
    total_chunks = 0
    for kb_file in kb_files:
        print(f"\n📄 Processing: {kb_file.name}")
        
        # Read file
        with open(kb_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into chunks
        chunks = chunk_text(content, max_length=1200)
        print(f"   ├─ Split into {len(chunks)} chunks")
        
        # Embed and store each chunk
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = embedder.encode(chunk)[0]  # Get 1D array
            
            # Create document ID
            doc_id = f"kb_{kb_file.stem}_chunk_{i}"
            
            # Add to collection
            collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{
                    "source": f"kb_file",
                    "file": kb_file.name,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }]
            )
        
        total_chunks += len(chunks)
        print(f"   └─ ✓ Ingested {len(chunks)} chunks")
    
    print(f"\n" + "=" * 70)
    print(f"✅ SUCCESS: Ingested {total_chunks} chunks from {len(kb_files)} KB files")
    print(f"📊 Total documents in collection: {collection.count()}")
    print("=" * 70)

if __name__ == "__main__":
    main()
