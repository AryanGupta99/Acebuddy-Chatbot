"""
Chunk KB articles using atomic chunking strategy (150-200 tokens)
Creates chunks compatible with existing system
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import List, Dict

def estimate_tokens(text: str) -> int:
    """Estimate token count: 1 token ≈ 4 characters"""
    return len(text) // 4

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences"""
    # Simple sentence splitter
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def atomic_chunk_article(text: str, title: str, source_file: str, target_tokens: int = 180) -> List[Dict]:
    """
    Create atomic chunks from article text
    Strategy: split by sentences, merge until target size
    """
    
    chunks = []
    sentences = split_into_sentences(text)
    
    if not sentences:
        return []
    
    current_chunk = []
    current_tokens = 0
    
    for sentence in sentences:
        tokens = estimate_tokens(sentence)
        
        if current_tokens + tokens <= target_tokens:
            # Add to current chunk
            current_chunk.append(sentence)
            current_tokens += tokens
        else:
            # Save current chunk and start new one
            if current_chunk:
                chunk_text = ' '.join(current_chunk).strip()
                chunks.append({
                    "title": title,
                    "source_file": source_file,
                    "content": chunk_text,
                    "tokens": estimate_tokens(chunk_text),
                    "sentences": len(current_chunk)
                })
            
            # Start new chunk
            current_chunk = [sentence]
            current_tokens = tokens
    
    # Save last chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk).strip()
        chunks.append({
            "title": title,
            "source_file": source_file,
            "content": chunk_text,
            "tokens": estimate_tokens(chunk_text),
            "sentences": len(current_chunk)
        })
    
    return chunks

def chunk_kb_articles(cleaned_dir: Path, output_json: Path) -> Dict:
    """Process all cleaned KB articles into atomic chunks"""
    
    print(f"\n{'='*80}")
    print(f"CREATING ATOMIC CHUNKS")
    print(f"{'='*80}\n")
    
    all_chunks = []
    articles_processed = 0
    total_tokens = 0
    chunk_id_counter = 0
    
    files = sorted(cleaned_dir.glob("*.txt"))
    print(f"📝 Chunking {len(files)} cleaned articles...\n")
    
    for file_idx, filepath in enumerate(files, 1):
        try:
            # Read cleaned text
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            
            if not text or len(text.strip()) < 50:
                continue
            
            title = filepath.stem
            
            # Create atomic chunks
            chunks = atomic_chunk_article(text, title, filepath.name)
            
            if not chunks:
                continue
            
            # Add chunks with IDs
            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = f"kb_article_{chunk_id_counter:05d}"
                chunk_id_counter += 1
                
                all_chunks.append({
                    "id": chunk_id,
                    "content": chunk['content'],
                    "metadata": {
                        "source": "kb_article",
                        "title": chunk['title'],
                        "source_file": chunk['source_file'],
                        "chunk_index": chunk_idx,
                        "tokens": chunk['tokens'],
                        "sentences": chunk['sentences']
                    }
                })
                
                total_tokens += chunk['tokens']
            
            articles_processed += 1
            
            if articles_processed % 5 == 0:
                print(f"   Processed {articles_processed} articles, {chunk_id_counter} chunks...", end='\r')
        
        except Exception as e:
            print(f"   ⚠️  Error processing {filepath.name}: {e}")
    
    print(f"\n{'='*80}")
    print(f"📊 CHUNKING SUMMARY")
    print(f"{'='*80}")
    print(f"Articles processed:   {articles_processed}")
    print(f"Total chunks:         {len(all_chunks)}")
    print(f"Avg tokens/chunk:     {total_tokens // max(1, len(all_chunks))}")
    print(f"Total tokens:         {total_tokens:,}\n")
    
    # Save chunks
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved to: {output_json}\n")
    
    return {
        "total_chunks": len(all_chunks),
        "total_tokens": total_tokens,
        "articles_processed": articles_processed
    }

def main():
    """Main chunking pipeline"""
    
    proj_root = Path(__file__).parent.parent
    cleaned_dir = proj_root / "data" / "kb_downloads" / "cleaned"
    output_json = proj_root / "data" / "kb_article_chunks.json"
    
    if not cleaned_dir.exists():
        print(f"❌ Cleaned directory not found: {cleaned_dir}")
        print(f"Please run: python scripts/process_kb_articles.py")
        return
    
    # Chunk articles
    stats = chunk_kb_articles(cleaned_dir, output_json)
    
    if stats['total_chunks'] > 0:
        print(f"✅ Ready to ingest!")
        print(f"\nNext: python scripts/ingest_kb_chunks.py\n")

if __name__ == "__main__":
    main()
