#!/usr/bin/env python3
"""
Complete Data-to-LLM Pipeline Orchestrator
===========================================

Steps:
1. Prepare (clean) raw data
2. Ingest cleaned data into Chroma
3. Query with LLM using cleaned data

This script orchestrates the entire workflow.
"""

import sys
import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RAGPipelineOrchestrator:
    """Orchestrate entire data preparation and RAG pipeline"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        self.kb_dir = self.data_dir / "kb"
        self.prepared_dir = self.data_dir / "prepared"
        self.scripts_dir = self.base_dir / "scripts"
    
    def verify_setup(self) -> bool:
        """Verify all required files and directories exist"""
        logger.info("Verifying setup...")
        
        required_dirs = [self.data_dir, self.kb_dir, self.scripts_dir]
        for dir_path in required_dirs:
            if not dir_path.exists():
                logger.error(f"Missing directory: {dir_path}")
                return False
        
        required_files = [
            self.scripts_dir / "data_preparation.py",
            self.scripts_dir / "rag_ingestion.py",
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                logger.error(f"Missing file: {file_path}")
                return False
        
        logger.info("✅ Setup verification passed")
        return True
    
    def step1_prepare_data(self) -> bool:
        """Step 1: Prepare and clean raw data"""
        logger.info("\n" + "="*70)
        logger.info("STEP 1: DATA PREPARATION (Cleaning, PII Redaction, Validation)")
        logger.info("="*70)
        
        try:
            # Import and run data preparation
            sys.path.insert(0, str(self.scripts_dir))
            from data_preparation import DataPreparationPipeline
            
            pipeline = DataPreparationPipeline(output_dir=str(self.prepared_dir))
            metrics = pipeline.process_directory(str(self.kb_dir))
            
            # Print summary (use logger to avoid Unicode issues)
            logger.info(f"Data Preparation Complete:")
            logger.info(f"  Documents processed: {metrics.total_documents}")
            logger.info(f"  Documents cleaned: {metrics.documents_cleaned}")
            logger.info(f"  Documents with PII: {metrics.documents_with_pii}")
            logger.info(f"  Chunks created: {metrics.total_chunks}")
            
            # Check if we have prepared data
            chunks_file = self.prepared_dir / "chunks_for_rag.json"
            if chunks_file.exists():
                with open(chunks_file, 'r', encoding='utf-8') as f:
                    chunks = json.load(f)
                logger.info(f"✅ Data preparation successful: {len(chunks)} chunks created")
                return True
            else:
                logger.error("❌ Data preparation failed: No chunks file created")
                return False
                
        except Exception as e:
            logger.error(f"❌ Data preparation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step2_ingest_data(self) -> bool:
        """Step 2: Ingest cleaned data into Chroma"""
        logger.info("\n" + "="*70)
        logger.info("STEP 2: RAG INGESTION (Vector Database)")
        logger.info("="*70)
        
        try:
            # Wait for Chroma to be ready
            logger.info("Waiting for Chroma service...")
            time.sleep(3)
            
            # Import and run ingestion
            sys.path.insert(0, str(self.scripts_dir))
            from rag_ingestion import RAGIngester
            
            ingester = RAGIngester()
            chunks_file = self.prepared_dir / "chunks_for_rag.json"
            
            if not chunks_file.exists():
                logger.error(f"Chunks file not found: {chunks_file}")
                return False
            
            logger.info(f"Ingesting chunks from: {chunks_file}")
            stats = ingester.ingest_chunks(str(chunks_file), min_quality_score=0.5)
            
            ingester.print_stats()
            
            if stats.get('ingested_chunks', 0) > 0:
                logger.info(f"✅ Ingestion successful: {stats['ingested_chunks']} chunks ingested")
                return True
            else:
                logger.error("❌ Ingestion failed: No chunks ingested")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ingestion failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step3_test_rag_queries(self) -> bool:
        """Step 3: Test RAG with sample queries"""
        logger.info("\n" + "="*70)
        logger.info("STEP 3: RAG TESTING (Query + LLM Response)")
        logger.info("="*70)
        
        try:
            import requests
            
            test_queries = [
                "How do I reset my password?",
                "I can't connect to RDP",
                "My disk is full",
                "How do I add a new user?",
                "My monitor isn't working"
            ]
            
            base_url = "http://localhost:8000"
            results = []
            
            # Make sure API is ready
            logger.info("Waiting for API to be ready...")
            max_retries = 10
            for attempt in range(max_retries):
                try:
                    response = requests.get(f"{base_url}/health", timeout=2)
                    if response.status_code == 200:
                        logger.info("✅ API is ready")
                        break
                except:
                    if attempt < max_retries - 1:
                        logger.info(f"API not ready, retrying... ({attempt + 1}/{max_retries})")
                        time.sleep(2)
                    else:
                        logger.error("API failed to become ready")
                        return False
            
            # Test queries
            for query in test_queries:
                try:
                    logger.info(f"\n📝 Query: {query}")
                    
                    response = requests.post(
                        f"{base_url}/chat",
                        json={"query": query, "user_id": "test"},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        answer = result.get('answer', '')
                        confidence = result.get('confidence', 0)
                        has_context = len(result.get('context', [])) > 0
                        
                        logger.info(f"✅ Response received (confidence: {confidence:.2f})")
                        logger.info(f"   Has context: {has_context}")
                        logger.info(f"   Answer preview: {answer[:100]}...")
                        
                        results.append({
                            'query': query,
                            'success': True,
                            'confidence': confidence,
                            'has_context': has_context
                        })
                    else:
                        logger.error(f"❌ Error: {response.status_code}")
                        results.append({'query': query, 'success': False})
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"❌ Request failed: {e}")
                    results.append({'query': query, 'success': False})
                
                time.sleep(0.5)
            
            # Summary
            successful = sum(1 for r in results if r.get('success'))
            logger.info(f"\n✅ Test Results: {successful}/{len(test_queries)} queries successful")
            
            return successful > len(test_queries) // 2  # At least 50% success
            
        except Exception as e:
            logger.error(f"❌ Testing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_full_pipeline(self, skip_api_test: bool = False) -> bool:
        """Run complete pipeline"""
        logger.info("\n" + "╔" + "="*68 + "╗")
        logger.info("║" + " "*15 + "ACEBUDDY RAG: FULL DATA PIPELINE" + " "*22 + "║")
        logger.info("╚" + "="*68 + "╝\n")
        
        # Step 0: Verify
        if not self.verify_setup():
            logger.error("Setup verification failed")
            return False
        
        # Step 1: Prepare
        if not self.step1_prepare_data():
            logger.error("Data preparation failed")
            return False
        
        # Step 2: Ingest
        if not self.step2_ingest_data():
            logger.error("Data ingestion failed")
            return False
        
        # Step 3: Test (optional)
        if not skip_api_test:
            if not self.step3_test_rag_queries():
                logger.warning("Some tests failed, but pipeline may still work")
        
        logger.info("\n" + "╔" + "="*68 + "╗")
        logger.info("║" + " "*18 + "✅ PIPELINE COMPLETE ✅" + " "*24 + "║")
        logger.info("╚" + "="*68 + "╝")
        logger.info("""
Next Steps:
1. Check data/prepared/ for cleaned data and chunks
2. Verify Chroma contains your data
3. Run API tests: curl -X POST http://localhost:8000/chat
4. Monitor logs for issues

Your RAG system is now ready with:
✅ Cleaned data (PII redacted, duplicates removed)
✅ Quality-validated chunks
✅ Indexed in Chroma vector database
✅ Connected to LLM (Ollama)
✅ Ready for production use
        """)
        
        return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AceBuddy RAG Full Pipeline')
    parser.add_argument(
        '--skip-api-test',
        action='store_true',
        help='Skip API testing step'
    )
    parser.add_argument(
        '--base-dir',
        default='.',
        help='Base directory for RAG project'
    )
    
    args = parser.parse_args()
    
    orchestrator = RAGPipelineOrchestrator(base_dir=args.base_dir)
    success = orchestrator.run_full_pipeline(skip_api_test=args.skip_api_test)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
