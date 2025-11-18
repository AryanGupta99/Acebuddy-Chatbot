import json
from pathlib import Path

qa_file = Path('data/zobot_extracted/zobot_qa_pairs.json')
with open(qa_file, 'r', encoding='utf-8') as f:
    qa_pairs = json.load(f)

print(f"Type of qa_pairs: {type(qa_pairs)}")
print(f"Length: {len(qa_pairs)}")
if qa_pairs:
    if isinstance(qa_pairs, dict):
        print(f"Keys: {list(qa_pairs.keys())[:5]}")
        first_key = list(qa_pairs.keys())[0]
        print(f"\nFirst item: {first_key}")
        print(f"Value type: {type(qa_pairs[first_key])}")
        print(f"Value: {qa_pairs[first_key]}")
    elif isinstance(qa_pairs, list):
        print(f"First item: {qa_pairs[0]}")
