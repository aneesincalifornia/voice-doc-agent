import pytest
from langchain_core.documents import Document
from app.chunker import chunk_documents

def test_chunk_documents_basic(sample_text):
    """Test chunking a single document."""
    # Expand text to ensure it will be chunked
    long_text = sample_text * 5
    docs = [Document(page_content=long_text, metadata={"page": 0})]

    chunks = chunk_documents(docs)

    assert len(chunks) >= 1
    assert all(isinstance(c, Document) for c in chunks)
    assert all(len(c.page_content) <= 1200 for c in chunks)

def test_chunk_documents_preserves_metadata(sample_text):
    """Test that chunking preserves document metadata."""
    docs = [
        Document(
            page_content=sample_text,
            metadata={"page": 0, "source": "test.txt"}
        )
    ]

    chunks = chunk_documents(docs)

    for chunk in chunks:
        assert chunk.metadata.get("page") == 0
        assert chunk.metadata.get("source") == "test.txt"

def test_chunk_documents_overlap(sample_text):
    """Test that chunks have overlap (not isolated)."""
    docs = [Document(page_content=sample_text * 3, metadata={"page": 0})]

    chunks = chunk_documents(docs)

    # With overlap, consecutive chunks should have some shared content
    if len(chunks) > 1:
        # Check that some chunks share words (due to overlap)
        chunk1_words = set(chunks[0].page_content.lower().split())
        chunk2_words = set(chunks[1].page_content.lower().split())
        overlap_words = chunk1_words & chunk2_words

        # Should have some overlap
        assert len(overlap_words) > 0

def test_chunk_documents_empty():
    """Test chunking empty document list."""
    chunks = chunk_documents([])

    assert len(chunks) == 0

def test_chunk_documents_short():
    """Test chunking short content that won't be split."""
    short_text = "This is a short document."
    docs = [Document(page_content=short_text, metadata={"page": 0})]

    chunks = chunk_documents(docs)

    # Short text should result in one chunk
    assert len(chunks) == 1
    assert chunks[0].page_content == short_text
