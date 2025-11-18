"""
Aggressive Re-Chunking Strategy
- Break KB into atomic chunks (150-200 tokens each)
- Strategy: Split by steps, fields, specific instructions—NOT broad topics
- Goal: Improve semantic matching from 15-20% → 65-75% confidence
"""

import json
import os
from pathlib import Path
import re

KB_DIR = Path(__file__).parent.parent / "data" / "kb"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "atomic_chunks.json"

def estimate_tokens(text):
    """Rough token estimate: 1 token ≈ 4 characters"""
    return len(text) // 4

def split_by_headers(text):
    """Split text by markdown headers to find natural boundaries"""
    parts = []
    current = []
    lines = text.split('\n')
    
    for line in lines:
        if line.startswith('#'):
            if current:
                parts.append('\n'.join(current).strip())
                current = []
            current.append(line)
        else:
            current.append(line)
    
    if current:
        parts.append('\n'.join(current).strip())
    
    return [p for p in parts if p.strip()]

def split_by_numbered_lists(text):
    """Split by numbered lists to create step-by-step chunks"""
    chunks = []
    current_chunk = []
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        # Detect numbered list items (1., 2., 3., etc.)
        if re.match(r'^\d+\.\s+', line.strip()):
            if current_chunk and estimate_tokens('\n'.join(current_chunk)) > 50:
                chunks.append('\n'.join(current_chunk).strip())
                current_chunk = []
        current_chunk.append(line)
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk).strip())
    
    return [c for c in chunks if c.strip()]

def split_by_bullet_groups(text):
    """Split by bullet points to create sub-sections"""
    chunks = []
    current_chunk = []
    in_bullets = False
    
    for line in text.split('\n'):
        is_bullet = line.strip().startswith(('-', '*', '•'))
        
        if is_bullet and not in_bullets:
            # Starting bullet section
            if current_chunk and estimate_tokens('\n'.join(current_chunk)) > 50:
                chunks.append('\n'.join(current_chunk).strip())
                current_chunk = []
            in_bullets = True
        elif not is_bullet and in_bullets and line.strip():
            # Ending bullet section
            if estimate_tokens('\n'.join(current_chunk)) > 50:
                chunks.append('\n'.join(current_chunk).strip())
                current_chunk = []
            in_bullets = False
        
        current_chunk.append(line)
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk).strip())
    
    return [c for c in chunks if c.strip()]

def aggressive_chunk(text, target_tokens=180):
    """
    Aggressive chunking strategy:
    1. Split by headers (sections)
    2. For each section, split by numbered lists (steps)
    3. For each step, split by bullets (details)
    4. Merge if under target size, split if over
    """
    
    # First pass: split by headers
    sections = split_by_headers(text)
    
    all_chunks = []
    
    for section in sections:
        tokens = estimate_tokens(section)
        
        if tokens <= target_tokens:
            # Keep as-is
            all_chunks.append(section)
        elif tokens <= target_tokens * 2:
            # Try splitting by lists
            list_chunks = split_by_numbered_lists(section)
            if len(list_chunks) > 1:
                all_chunks.extend(list_chunks)
            else:
                # Try splitting by bullets
                bullet_chunks = split_by_bullet_groups(section)
                if len(bullet_chunks) > 1:
                    all_chunks.extend(bullet_chunks)
                else:
                    all_chunks.append(section)
        else:
            # Aggressive: split by lists, then bullets
            list_chunks = split_by_numbered_lists(section)
            for list_chunk in list_chunks:
                if estimate_tokens(list_chunk) <= target_tokens:
                    all_chunks.append(list_chunk)
                else:
                    bullet_chunks = split_by_bullet_groups(list_chunk)
                    all_chunks.extend(bullet_chunks)
    
    # Final pass: merge too-small chunks, re-split too-large ones
    final_chunks = []
    current = ""
    
    for chunk in all_chunks:
        candidate = current + "\n" + chunk if current else chunk
        tokens = estimate_tokens(candidate)
        
        if tokens <= target_tokens:
            current = candidate
        else:
            if current:
                final_chunks.append(current.strip())
            if estimate_tokens(chunk) <= target_tokens:
                current = chunk
            else:
                # This chunk is still too big—keep it anyway
                final_chunks.append(chunk)
                current = ""
    
    if current:
        final_chunks.append(current.strip())
    
    return [c for c in final_chunks if c.strip()]

def process_kb_files():
    """Process all KB files and create atomic chunks"""
    
    all_chunks = []
    chunk_id_counter = 0
    
    # Get all markdown and text files
    kb_files = sorted(KB_DIR.glob("*.md")) + sorted(KB_DIR.glob("*.txt"))
    
    print(f"\n{'='*60}")
    print(f"AGGRESSIVE RE-CHUNKING PIPELINE")
    print(f"{'='*60}\n")
    
    for kb_file in kb_files:
        print(f"Processing: {kb_file.name}")
        
        with open(kb_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Aggressive chunk
        chunks = aggressive_chunk(content, target_tokens=180)
        
        print(f"  Original size: {estimate_tokens(content)} tokens")
        print(f"  Chunks created: {len(chunks)}")
        
        # Add metadata
        for chunk in chunks:
            tokens = estimate_tokens(chunk)
            all_chunks.append({
                "id": f"atomic_{chunk_id_counter:04d}",
                "content": chunk,
                "metadata": {
                    "source": "kb_file",
                    "file": kb_file.name,
                    "tokens": tokens,
                    "chunk_type": "atomic"
                }
            })
            chunk_id_counter += 1
        
        print(f"  Sample chunk: {chunks[0][:100]}...\n")
    
    # Save to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"{'='*60}")
    print(f"✅ Total atomic chunks created: {len(all_chunks)}")
    print(f"📁 Saved to: {OUTPUT_FILE}")
    print(f"{'='*60}\n")
    
    return all_chunks

if __name__ == "__main__":
    process_kb_files()
