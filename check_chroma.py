import chromadb
from pathlib import Path

chroma_dir = Path("data/chroma")
client = chromadb.PersistentClient(path=str(chroma_dir))

collection = client.get_or_create_collection("acebuddy_kb")
count = collection.count()

print(f"Collection: acebuddy_kb")
print(f"Document count: {count}")

if count > 0:
    # Get some samples
    results = collection.get(limit=5)
    print(f"\nSample documents:")
    for i, (id, doc, meta) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
        print(f"\n{i+1}. ID: {id}")
        print(f"   Doc (first 100 chars): {doc[:100]}...")
        print(f"   Metadata: {meta}")
