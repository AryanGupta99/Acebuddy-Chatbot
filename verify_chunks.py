import json

data = json.load(open('data/manual_kb_chunks.json'))
print(f"Total chunks: {len(data['chunks'])}")
print(f"\nMetadata:")
print(json.dumps(data['metadata'], indent=2))
print(f"\nSample chunk:")
print(f"  ID: {data['chunks'][0]['id']}")
print(f"  Text: {data['chunks'][0]['text'][:80]}...")
print(f"  Has embedding: {bool(data['chunks'][0].get('embedding'))}")
print(f"  Embedding length: {len(data['chunks'][0].get('embedding', []))}")
