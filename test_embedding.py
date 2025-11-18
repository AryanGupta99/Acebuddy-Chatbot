import hashlib
import numpy as np

class DummyEmbedding:
    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        for text in texts:
            h = hashlib.sha256(text.encode('utf-8')).digest()
            vals = []
            i = 0
            while len(vals) < 384:
                chunk = h[i % len(h)]
                vals.append(chunk / 255.0)
                i += 1
            embeddings.append(vals[:384])
        return np.array(embeddings)

embedder = DummyEmbedding()

# Test with a single text
text = "This is a test document"
embedding = embedder.encode(text)

print(f"Embedding shape: {embedding.shape}")
print(f"Embedding dtype: {embedding.dtype}")
print(f"Embedding type: {type(embedding)}")
print(f"First 10 values: {embedding[0][:10]}")

# Convert to list
embedding_list = embedding.tolist()
print(f"\nAs list - type: {type(embedding_list)}")
print(f"As list - length: {len(embedding_list)}")
print(f"As list[0] - type: {type(embedding_list[0])}")
print(f"As list[0] - length: {len(embedding_list[0])}")
