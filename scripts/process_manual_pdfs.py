"""
Process manually downloaded PDF files:
1. Extract text from PDFs
2. Clean and preprocess
3. Create atomic chunks
4. Embed with OpenAI
5. Ingest into Chroma
"""

import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import re
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import PyPDF2
import nltk
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Get OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not set in .env")
    sys.exit(1)

from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Download NLTK data if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading NLTK tokenizer data...")
    nltk.download('punkt', quiet=True)

# Configuration
PDF_FOLDER = Path("data/kb_downloads/downloaded")
CLEANED_FOLDER = Path("data/kb_downloads/cleaned_manual")
OUTPUT_CHUNKS = Path("data/manual_kb_chunks.json")
BATCH_SIZE = 25
TARGET_TOKENS = 180
EMBEDDING_MODEL = "text-embedding-3-small"

# Create output folder
CLEANED_FOLDER.mkdir(parents=True, exist_ok=True)


def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF file."""
    print(f"  Extracting text from: {Path(pdf_path).name}")
    
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            print(f"    Total pages: {num_pages}")
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    if page_num % 5 == 0:
                        print(f"    Processed {page_num}/{num_pages} pages...")
                except Exception as e:
                    print(f"    Warning: Error extracting page {page_num}: {e}")
        
        return text
    except Exception as e:
        print(f"    ERROR: Failed to extract PDF: {e}")
        return ""


def clean_text(text: str) -> str:
    """Clean extracted text."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common PDF artifacts
    text = re.sub(r'Page \d+', '', text)
    text = re.sub(r'Page \d+ of \d+', '', text)
    
    # Remove header/footer patterns
    text = re.sub(r'\d{1,2}:\d{2}', '', text)
    text = re.sub(r'http\S+', '', text)  # Remove URLs first
    
    # Remove special characters but keep structure
    text = text.replace('\x00', '')
    text = text.replace('\x0c', '')
    
    # Normalize punctuation
    text = text.replace('  ', ' ')
    
    return text.strip()


def estimate_tokens(text: str) -> int:
    """Estimate tokens using simple word count (roughly 1 token = 1.3 words)."""
    words = len(text.split())
    return max(1, int(words / 1.3))


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    try:
        sentences = sent_tokenize(text)
        return [s.strip() for s in sentences if s.strip()]
    except:
        # Fallback: split by period
        sentences = text.split('. ')
        return [s.strip() for s in sentences if s.strip()]


def create_atomic_chunks(text: str, title: str, source_file: str) -> List[Dict]:
    """Create atomic chunks from text."""
    chunks = []
    sentences = split_into_sentences(text)
    
    current_chunk = []
    current_tokens = 0
    chunk_id = 0
    
    for sentence in sentences:
        tokens = estimate_tokens(sentence)
        
        # If adding this sentence exceeds target, save current chunk
        if current_tokens + tokens > TARGET_TOKENS and current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_tokens = estimate_tokens(chunk_text)
            
            chunks.append({
                "id": f"{source_file}_chunk_{chunk_id}",
                "text": chunk_text,
                "title": title,
                "source": source_file,
                "tokens": chunk_tokens,
                "chunk_id": chunk_id
            })
            chunk_id += 1
            current_chunk = []
            current_tokens = 0
        
        current_chunk.append(sentence)
        current_tokens += tokens
    
    # Save final chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunk_tokens = estimate_tokens(chunk_text)
        
        chunks.append({
            "id": f"{source_file}_chunk_{chunk_id}",
            "text": chunk_text,
            "title": title,
            "source": source_file,
            "tokens": chunk_tokens,
            "chunk_id": chunk_id
        })
    
    return chunks


def get_embedding(text: str) -> List[float]:
    """Get embedding from OpenAI."""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"    ERROR getting embedding: {e}")
        return []


def embed_chunks(chunks: List[Dict]) -> List[Dict]:
    """Embed all chunks using OpenAI."""
    print(f"\nEmbedding {len(chunks)} chunks...")
    
    embedded_chunks = []
    
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i+BATCH_SIZE]
        print(f"  Processing batch {i//BATCH_SIZE + 1}/{(len(chunks)-1)//BATCH_SIZE + 1}")
        
        for chunk in batch:
            embedding = get_embedding(chunk['text'])
            if embedding:
                chunk['embedding'] = embedding
                embedded_chunks.append(chunk)
            else:
                print(f"    Skipping chunk {chunk['id']} (embedding failed)")
        
        # Rate limiting
        time.sleep(0.5)
    
    return embedded_chunks


def process_pdfs():
    """Main processing pipeline."""
    print("=" * 80)
    print("PDF PROCESSING PIPELINE")
    print("=" * 80)
    
    if not PDF_FOLDER.exists():
        print(f"ERROR: PDF folder not found: {PDF_FOLDER}")
        return None
    
    # Step 1: Extract text from PDFs
    print("\n[STEP 1] Extracting text from PDFs...")
    pdf_files = list(PDF_FOLDER.glob("*.pdf"))
    
    if not pdf_files:
        print("ERROR: No PDF files found")
        return None
    
    print(f"Found {len(pdf_files)} PDF files")
    
    extracted_data = {}
    for pdf_file in sorted(pdf_files):
        print(f"\nProcessing: {pdf_file.name}")
        
        text = extract_pdf_text(str(pdf_file))
        if not text:
            print(f"  WARNING: No text extracted from {pdf_file.name}")
            continue
        
        extracted_data[pdf_file.stem] = {
            'filename': pdf_file.name,
            'raw_text': text,
            'extracted_chars': len(text)
        }
        
        print(f"  Extracted {len(text)} characters")
    
    if not extracted_data:
        print("ERROR: Failed to extract text from any PDFs")
        return None
    
    # Step 2: Clean text
    print("\n[STEP 2] Cleaning extracted text...")
    
    cleaned_data = {}
    for stem, data in extracted_data.items():
        print(f"  Cleaning: {data['filename']}")
        
        cleaned_text = clean_text(data['raw_text'])
        cleaned_data[stem] = {
            'filename': data['filename'],
            'text': cleaned_text,
            'raw_chars': data['extracted_chars'],
            'cleaned_chars': len(cleaned_text)
        }
        
        print(f"    Raw: {data['extracted_chars']} → Cleaned: {len(cleaned_text)} characters")
        
        # Save cleaned text
        cleaned_file = CLEANED_FOLDER / f"{stem}_cleaned.txt"
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        print(f"    Saved to: {cleaned_file}")
    
    # Step 3: Create atomic chunks
    print("\n[STEP 3] Creating atomic chunks...")
    
    all_chunks = []
    chunk_stats = {}
    
    for stem, data in cleaned_data.items():
        print(f"  Chunking: {data['filename']}")
        
        chunks = create_atomic_chunks(data['text'], stem, stem)
        all_chunks.extend(chunks)
        chunk_stats[stem] = {
            'filename': data['filename'],
            'total_chunks': len(chunks),
            'total_tokens': sum(c['tokens'] for c in chunks),
            'avg_tokens': sum(c['tokens'] for c in chunks) // len(chunks) if chunks else 0
        }
        
        print(f"    Created {len(chunks)} chunks, {chunk_stats[stem]['total_tokens']} total tokens")
    
    print(f"\n  Total: {len(all_chunks)} chunks from {len(cleaned_data)} documents")
    
    # Step 4: Embed chunks
    print("\n[STEP 4] Embedding chunks with OpenAI...")
    
    embedded_chunks = embed_chunks(all_chunks)
    
    print(f"  Successfully embedded {len(embedded_chunks)}/{len(all_chunks)} chunks")
    
    # Step 5: Save results
    print("\n[STEP 5] Saving chunks...")
    
    output_data = {
        'metadata': {
            'total_documents': len(cleaned_data),
            'total_chunks': len(embedded_chunks),
            'embedding_model': EMBEDDING_MODEL,
            'target_tokens': TARGET_TOKENS,
            'documents': chunk_stats
        },
        'chunks': embedded_chunks
    }
    
    with open(OUTPUT_CHUNKS, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"  Saved to: {OUTPUT_CHUNKS}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("PROCESSING SUMMARY")
    print("=" * 80)
    print(f"Documents processed: {len(cleaned_data)}")
    print(f"Total chunks created: {len(embedded_chunks)}")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    
    for stem, stats in chunk_stats.items():
        print(f"\n  {stats['filename']}")
        print(f"    - Chunks: {stats['total_chunks']}")
        print(f"    - Tokens: {stats['total_tokens']} (avg {stats['avg_tokens']} per chunk)")
    
    print("\n" + "=" * 80)
    
    return embedded_chunks


if __name__ == "__main__":
    try:
        chunks = process_pdfs()
        
        if chunks:
            print("\n✓ Processing complete!")
            print(f"Ready to ingest {len(chunks)} chunks into Chroma")
            sys.exit(0)
        else:
            print("\n✗ Processing failed")
            sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
