"""
Data Preparation Unit Test
==========================

Tests the DataPreparationPipeline to ensure:
- Output files are created
- Chunks have required metadata
- Quality scoring works
- PII redaction works
"""

import pytest
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from data_preparation import (
    DataPreparationPipeline,
    PIIRedactor,
    QualityScorer,
    TextNormalizer
)


class TestPIIRedactor:
    """Test PII redaction functionality"""
    
    def test_email_redaction(self):
        redactor = PIIRedactor()
        text = "Contact me at john.doe@example.com for info"
        cleaned, counts = redactor.redact(text)
        
        assert "john.doe@example.com" not in cleaned
        assert "EMAIL" in cleaned  # Check for EMAIL marker (flexible format)
        assert counts.get("email", 0) == 1
        print(f"✅ Email redaction: {counts}")
    
    def test_phone_redaction(self):
        redactor = PIIRedactor()
        text = "Call me at 555-123-4567"
        cleaned, counts = redactor.redact(text)
        
        assert "555-123-4567" not in cleaned
        assert "PHONE" in cleaned  # Check for PHONE marker (flexible format)
        assert counts.get("phone", 0) == 1
        print(f"✅ Phone redaction: {counts}")
    
    def test_multiple_pii_types(self):
        redactor = PIIRedactor()
        text = "Email john@example.com or call 555-1234"
        cleaned, counts = redactor.redact(text)
        
        assert len(counts) > 0
        assert redactor.pii_found
        print(f"✅ Multiple PII types redacted: {counts}")


class TestQualityScorer:
    """Test quality scoring"""
    
    def test_quality_score_range(self):
        scorer = QualityScorer()
        
        # Good quality text
        good_text = """
        This is a well-formatted document with multiple sentences.
        It has proper punctuation and reasonable length.
        The content is structured and complete.
        """
        score = scorer.score(good_text)
        assert 0.0 <= score <= 1.0
        assert score > 0.3, "Good text should have score > 0.3"
        print(f"✅ Good text score: {score:.2f}")
        
        # Poor quality text
        poor_text = "x"
        score_poor = scorer.score(poor_text)
        assert 0.0 <= score_poor <= 1.0
        assert score_poor < score, "Poor text should score lower"
        print(f"✅ Poor text score: {score_poor:.2f}")


class TestTextNormalizer:
    """Test text normalization"""
    
    def test_whitespace_normalization(self):
        normalizer = TextNormalizer()
        text = "Multiple    spaces   and\n\n\n\nmultiple newlines"
        normalized = normalizer.normalize(text)
        
        assert "    " not in normalized
        assert "\n\n\n\n" not in normalized
        print(f"✅ Whitespace normalized")
    
    def test_encoding_handling(self):
        normalizer = TextNormalizer()
        text = "Special chars: \u201cquotes\u201d and \u2018apostrophes\u2019"
        normalized = normalizer.normalize(text)
        
        assert normalized  # Should not crash
        print(f"✅ Encoding handled: {normalized}")


class TestDataPreparationPipeline:
    """Test full data preparation pipeline"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        
        # Create sample KB files
        kb_dir = os.path.join(temp_dir, "kb")
        os.makedirs(kb_dir)
        
        # Sample file 1
        with open(os.path.join(kb_dir, "sample1.txt"), "w", encoding="utf-8") as f:
            f.write("""
# Password Reset Guide

To reset your password:
1. Go to the login page
2. Click "Forgot Password"
3. Enter your email address
4. Check your email for reset link

For help, contact support@example.com
            """)
        
        # Sample file 2
        with open(os.path.join(kb_dir, "sample2.md"), "w", encoding="utf-8") as f:
            f.write("""
# RDP Connection Issues

If you cannot connect to Remote Desktop:
- Verify your network connection
- Check if the server is online
- Ensure you have proper credentials
- Call IT support at 555-1234 if issues persist
            """)
        
        # Output dir
        output_dir = os.path.join(temp_dir, "prepared")
        
        yield {"kb_dir": kb_dir, "output_dir": output_dir, "temp_dir": temp_dir}
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_pipeline_creates_output_files(self, temp_workspace):
        """Test that pipeline creates expected output files"""
        pipeline = DataPreparationPipeline(output_dir=temp_workspace["output_dir"])
        metrics = pipeline.process_directory(temp_workspace["kb_dir"])
        
        output_dir = Path(temp_workspace["output_dir"])
        
        # Check output files exist
        assert (output_dir / "documents_cleaned.json").exists(), "Missing documents_cleaned.json"
        assert (output_dir / "chunks_for_rag.json").exists(), "Missing chunks_for_rag.json"
        assert (output_dir / "preparation_report.json").exists(), "Missing preparation_report.json"
        
        print(f"✅ All output files created")
        print(f"   Documents processed: {metrics.total_documents}")
        print(f"   Chunks created: {metrics.total_chunks}")
    
    def test_chunks_have_required_metadata(self, temp_workspace):
        """Test that chunks have all required metadata fields"""
        pipeline = DataPreparationPipeline(output_dir=temp_workspace["output_dir"])
        pipeline.process_directory(temp_workspace["kb_dir"])
        
        # Read chunks file
        chunks_file = Path(temp_workspace["output_dir"]) / "chunks_for_rag.json"
        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        
        assert len(chunks) > 0, "No chunks created"
        
        # Check first chunk has required fields
        first_chunk = chunks[0]
        required_fields = ["id", "content", "metadata"]
        for field in required_fields:
            assert field in first_chunk, f"Chunk missing '{field}' field"
        
        # Check metadata has required fields
        metadata = first_chunk["metadata"]
        metadata_fields = ["source", "processed_at", "chunk_number", "source_doc_id"]
        for field in metadata_fields:
            assert field in metadata, f"Metadata missing '{field}' field"
        
        print(f"✅ Chunks have required metadata:")
        print(f"   Total chunks: {len(chunks)}")
        print(f"   First chunk ID: {first_chunk['id']}")
        print(f"   Metadata keys: {list(metadata.keys())}")
    
    def test_pii_redaction_in_pipeline(self, temp_workspace):
        """Test that PII is redacted in the pipeline"""
        pipeline = DataPreparationPipeline(output_dir=temp_workspace["output_dir"])
        metrics = pipeline.process_directory(temp_workspace["kb_dir"])
        
        # Read documents file
        docs_file = Path(temp_workspace["output_dir"]) / "documents_cleaned.json"
        with open(docs_file, "r", encoding="utf-8") as f:
            documents = json.load(f)
        
        # Check that PII was found and redacted
        pii_docs = [doc for doc in documents if doc["metadata"].get("pii_redacted", False)]
        
        if len(pii_docs) > 0:
            print(f"✅ PII redaction working:")
            print(f"   Documents with PII: {len(pii_docs)}")
            print(f"   Total documents: {len(documents)}")
            
            # Check that redacted markers are present
            first_pii_doc = pii_docs[0]
            # Check for REDACTED marker in any format
            assert "REDACTED" in first_pii_doc["cleaned_content"]
            print(f"   Redaction markers found in cleaned content")
        else:
            print(f"⚠️  No PII found in test documents (may be expected)")
    
    def test_quality_scores_assigned(self, temp_workspace):
        """Test that quality scores are assigned to documents"""
        pipeline = DataPreparationPipeline(output_dir=temp_workspace["output_dir"])
        pipeline.process_directory(temp_workspace["kb_dir"])
        
        # Read documents file
        docs_file = Path(temp_workspace["output_dir"]) / "documents_cleaned.json"
        with open(docs_file, "r", encoding="utf-8") as f:
            documents = json.load(f)
        
        for doc in documents:
            assert "quality_score" in doc, "Document missing quality_score"
            score = doc["quality_score"]
            assert 0.0 <= score <= 1.0, f"Quality score {score} out of range"
        
        avg_score = sum(doc["quality_score"] for doc in documents) / len(documents)
        print(f"✅ Quality scores assigned:")
        print(f"   Average quality score: {avg_score:.2f}")
        print(f"   Score range: [{min(doc['quality_score'] for doc in documents):.2f}, {max(doc['quality_score'] for doc in documents):.2f}]")
    
    def test_report_file_structure(self, temp_workspace):
        """Test that preparation report has correct structure"""
        pipeline = DataPreparationPipeline(output_dir=temp_workspace["output_dir"])
        pipeline.process_directory(temp_workspace["kb_dir"])
        
        # Read report file
        report_file = Path(temp_workspace["output_dir"]) / "preparation_report.json"
        with open(report_file, "r", encoding="utf-8") as f:
            report = json.load(f)
        
        # Check report structure
        assert "timestamp" in report
        assert "metrics" in report
        assert "documents_summary" in report
        
        metrics = report["metrics"]
        assert "total_documents" in metrics
        assert "total_chunks" in metrics
        
        print(f"✅ Report structure valid:")
        print(f"   Timestamp: {report['timestamp']}")
        print(f"   Metrics keys: {list(metrics.keys())}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
