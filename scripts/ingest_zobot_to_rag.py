"""
Ingest Zobot Extracted Data into RAG System

This script takes the extracted Zobot Q&A pairs and topic documents,
and ingests them into the ChromaDB vector database for semantic retrieval.

Features:
- Loads extracted Q&A pairs from JSON
- Chunks documents appropriately for RAG
- Adds metadata for filtering
- Preserves chatbot personality and context
- Supports incremental updates
"""

import json
import sys
from pathlib import Path
from typing import List, Dict
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.rag_ingestion import RAGIngester

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ZobotRAGIngestion:
    """Ingest Zobot extracted data into RAG system"""
    
    def __init__(self, extracted_data_dir: str):
        self.extracted_data_dir = Path(extracted_data_dir)
        
        # Use persistent local client
        import chromadb
        persist_directory = str(Path(__file__).parent.parent / "data" / "chroma")
        logger.info(f"Using persistent local ChromaDB at: {persist_directory}")
        
        # Create custom RAG ingester with persistent client
        self.rag = RAGIngester()
        self.rag.client = chromadb.PersistentClient(path=persist_directory)
        self.rag.collection = self.rag._get_or_create_collection()
        
        # Verify directories
        if not self.extracted_data_dir.exists():
            raise FileNotFoundError(f"Extracted data directory not found: {self.extracted_data_dir}")
    
    def load_qa_pairs(self) -> List[Dict]:
        """Load extracted Q&A pairs from JSON"""
        json_file = self.extracted_data_dir / 'zobot_qa_pairs.json'
        
        if not json_file.exists():
            raise FileNotFoundError(f"Q&A pairs file not found: {json_file}")
        
        logger.info(f"Loading Q&A pairs from: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            qa_pairs = json.load(f)
        
        logger.info(f"Loaded {len(qa_pairs)} Q&A pairs")
        return qa_pairs
    
    def load_topic_documents(self) -> List[Dict]:
        """Load topic documents from markdown files"""
        topics_dir = self.extracted_data_dir / 'topics'
        
        if not topics_dir.exists():
            logger.warning(f"Topics directory not found: {topics_dir}")
            return []
        
        documents = []
        
        for md_file in topics_dir.glob('*.md'):
            logger.info(f"Loading topic document: {md_file.name}")
            
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract topic name from filename
            topic = md_file.stem.replace('_', ' ').title()
            
            documents.append({
                'content': content,
                'metadata': {
                    'source': 'zobot_topic_document',
                    'topic': topic,
                    'filename': md_file.name,
                    'doc_type': 'comprehensive_topic'
                }
            })
        
        logger.info(f"Loaded {len(documents)} topic documents")
        return documents
    
    def create_chunk_from_qa(self, qa: Dict) -> Dict:
        """Create a RAG chunk from a Q&A pair"""
        # Format the content in a conversational style
        content_parts = [
            f"**Question:** {qa['question']}",
            "",
            "**Answer:**",
            qa['answer']
        ]
        
        # Add links if present
        if 'links' in qa and qa['links']:
            content_parts.extend(["", "**Related Resources:**"])
            for link in qa['links']:
                link_text = link.get('text', 'Resource')
                link_url = link.get('url', '')
                content_parts.append(f"- {link_text}: {link_url}")
        
        content = '\n'.join(content_parts)
        
        # Create metadata
        metadata = {
            'source': 'acebuddy_chatbot',
            'topic': qa['topic'],
            'question': qa['question'],
            'has_links': qa['metadata'].get('has_links', False),
            'has_articles': qa['metadata'].get('has_articles', False),
            'context': qa['metadata'].get('context', ''),
            'doc_type': 'qa_pair'
        }
        
        # Add articles if present
        if 'articles' in qa:
            metadata['article_ids'] = qa['articles']
        
        return {
            'content': content,
            'metadata': metadata
        }
    
    def chunk_topic_document(self, doc: Dict, max_chunk_size: int = 1000) -> List[Dict]:
        """Split a topic document into chunks"""
        content = doc['content']
        metadata = doc['metadata']
        
        # Split by sections (## headers)
        sections = []
        current_section = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        # Create chunks from sections
        chunks = []
        for i, section in enumerate(sections):
            chunk_metadata = metadata.copy()
            chunk_metadata['section_number'] = i + 1
            chunk_metadata['total_sections'] = len(sections)
            
            chunks.append({
                'content': section,
                'metadata': chunk_metadata
            })
        
        logger.debug(f"Split topic '{metadata['topic']}' into {len(chunks)} chunks")
        return chunks
    
    def ingest_qa_pairs(self, qa_pairs: List[Dict]) -> int:
        """Ingest Q&A pairs into RAG system"""
        logger.info("Ingesting Q&A pairs...")
        
        chunks = []
        for qa in qa_pairs:
            chunk = self.create_chunk_from_qa(qa)
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks from Q&A pairs")
        
        # Add to ChromaDB
        success_count = 0
        for chunk in chunks:
            try:
                self.rag.add_document(
                    content=chunk['content'],
                    metadata=chunk['metadata']
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to add chunk: {e}")
        
        logger.info(f"Successfully ingested {success_count}/{len(chunks)} Q&A pairs")
        return success_count
    
    def ingest_topic_documents(self, documents: List[Dict]) -> int:
        """Ingest topic documents into RAG system"""
        logger.info("Ingesting topic documents...")
        
        total_chunks = []
        for doc in documents:
            chunks = self.chunk_topic_document(doc)
            total_chunks.extend(chunks)
        
        logger.info(f"Created {len(total_chunks)} chunks from {len(documents)} topic documents")
        
        # Add to ChromaDB
        success_count = 0
        for chunk in total_chunks:
            try:
                self.rag.add_document(
                    content=chunk['content'],
                    metadata=chunk['metadata']
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to add chunk: {e}")
        
        logger.info(f"Successfully ingested {success_count}/{len(total_chunks)} topic chunks")
        return success_count
    
    def ingest_master_document(self) -> bool:
        """Ingest the master knowledge document"""
        master_file = self.extracted_data_dir / 'acebuddy_chatbot_knowledge.md'
        
        if not master_file.exists():
            logger.warning(f"Master document not found: {master_file}")
            return False
        
        logger.info(f"Ingesting master document: {master_file}")
        
        with open(master_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into major sections (# headers)
        sections = []
        current_section = []
        
        for line in content.split('\n'):
            if line.startswith('# ') and current_section:
                sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        logger.info(f"Split master document into {len(sections)} sections")
        
        # Add each section
        success_count = 0
        for i, section in enumerate(sections):
            try:
                self.rag.add_document(
                    content=section,
                    metadata={
                        'source': 'zobot_master_document',
                        'section_number': i + 1,
                        'total_sections': len(sections),
                        'doc_type': 'master_knowledge',
                        'filename': master_file.name
                    }
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to add section {i+1}: {e}")
        
        logger.info(f"Successfully ingested {success_count}/{len(sections)} master document sections")
        return success_count == len(sections)
    
    def run(self, include_qa: bool = True, include_topics: bool = True, include_master: bool = True):
        """Main ingestion workflow"""
        logger.info("=" * 60)
        logger.info("Zobot RAG Ingestion Started")
        logger.info("=" * 60)
        
        total_ingested = 0
        
        try:
            # Ingest Q&A pairs
            if include_qa:
                qa_pairs = self.load_qa_pairs()
                count = self.ingest_qa_pairs(qa_pairs)
                total_ingested += count
                logger.info(f"✓ Q&A pairs ingested: {count}")
            
            # Ingest topic documents
            if include_topics:
                topic_docs = self.load_topic_documents()
                if topic_docs:
                    count = self.ingest_topic_documents(topic_docs)
                    total_ingested += count
                    logger.info(f"✓ Topic documents ingested: {count} chunks")
            
            # Ingest master document
            if include_master:
                success = self.ingest_master_document()
                if success:
                    logger.info(f"✓ Master document ingested")
            
            # Get collection stats
            stats = self.rag.get_collection_stats()
            
            logger.info("=" * 60)
            logger.info("Ingestion Complete!")
            logger.info(f"Total items ingested in this run: {total_ingested}")
            logger.info(f"Total items in collection: {stats['count']}")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}", exc_info=True)
            return False


def main():
    """Main execution"""
    workspace_root = Path(__file__).parent.parent
    extracted_data_dir = workspace_root / 'data' / 'zobot_extracted'
    
    # Check if extracted data exists
    if not extracted_data_dir.exists():
        logger.error(f"Extracted data directory not found: {extracted_data_dir}")
        logger.error("Please run 'python scripts/extract_zobot_data.py' first!")
        return False
    
    # Check if Q&A pairs file exists
    qa_file = extracted_data_dir / 'zobot_qa_pairs.json'
    if not qa_file.exists():
        logger.error(f"Q&A pairs file not found: {qa_file}")
        logger.error("Please run 'python scripts/extract_zobot_data.py' first!")
        return False
    
    # Run ingestion
    ingestion = ZobotRAGIngestion(str(extracted_data_dir))
    success = ingestion.run()
    
    if success:
        logger.info("\n🎉 Success! Zobot data has been ingested into the RAG system.")
        logger.info("\n🤖 Your chatbot now has access to all the Acebuddy conversation flows!")
        logger.info("\n💬 Test it with queries like:")
        logger.info("   - 'How do I reset my password?'")
        logger.info("   - 'How to setup QuickBooks?'")
        logger.info("   - 'What are the steps for user addition?'")
        logger.info("   - 'How do I increase server memory?'")
    
    return success


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
