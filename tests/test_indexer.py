import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.indexer import get_file_hash, get_or_build_index

def test_get_file_hash(temp_txt_file):
    """Test file hashing."""
    hash1 = get_file_hash(temp_txt_file)
    hash2 = get_file_hash(temp_txt_file)

    # Same file should produce same hash
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex string length

def test_get_file_hash_different_files(tmp_path):
    """Test that different files produce different hashes."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    file1.write_text("content1")
    file2.write_text("content2")

    hash1 = get_file_hash(str(file1))
    hash2 = get_file_hash(str(file2))

    assert hash1 != hash2

@patch("app.indexer.OpenAIEmbeddings")
def test_get_or_build_index_builds_fresh(mock_embeddings, temp_txt_file, tmp_path):
    """Test building a fresh index when cache doesn't exist."""
    # Mock FAISS.from_documents
    mock_vector_store = MagicMock(spec=FAISS)
    mock_embeddings_instance = MagicMock()

    with patch("app.indexer.FAISS.from_documents", return_value=mock_vector_store) as mock_from_docs:
        with patch("app.indexer.os.getenv", return_value="sk-test-key"):
            chunks = [Document(page_content="test", metadata={"page": 0})]
            index_dir = str(tmp_path / "indexes")

            result = get_or_build_index(temp_txt_file, chunks, index_dir=index_dir)

            # Should call FAISS.from_documents
            mock_from_docs.assert_called_once()
            # Should call save_local
            mock_vector_store.save_local.assert_called_once()

            assert result == mock_vector_store

@patch("app.indexer.FAISS.load_local")
@patch("app.indexer.OpenAIEmbeddings")
def test_get_or_build_index_loads_cached(mock_embeddings, mock_load_local, temp_txt_file, tmp_path):
    """Test loading from cache when index exists."""
    mock_vector_store = MagicMock(spec=FAISS)
    mock_load_local.return_value = mock_vector_store

    index_dir = str(tmp_path / "indexes")
    cache_path = Path(index_dir) / get_file_hash(temp_txt_file)
    cache_path.mkdir(parents=True, exist_ok=True)

    # Create fake index files
    (cache_path / "index.faiss").write_bytes(b"fake")
    (cache_path / "index.pkl").write_bytes(b"fake")

    with patch("app.indexer.os.getenv", return_value="sk-test-key"):
        chunks = [Document(page_content="test", metadata={"page": 0})]

        result = get_or_build_index(temp_txt_file, chunks, index_dir=index_dir)

        # Should call load_local, not from_documents
        mock_load_local.assert_called_once()
        assert result == mock_vector_store

@patch("app.indexer.FAISS.from_documents")
@patch("app.indexer.OpenAIEmbeddings")
def test_get_or_build_index_cache_dir_created(mock_embeddings, mock_from_docs, temp_txt_file, tmp_path):
    """Test that cache directory is created if it doesn't exist."""
    mock_vector_store = MagicMock(spec=FAISS)
    mock_from_docs.return_value = mock_vector_store

    index_dir = str(tmp_path / "new_indexes")

    with patch("app.indexer.os.getenv", return_value="sk-test-key"):
        chunks = [Document(page_content="test", metadata={"page": 0})]

        get_or_build_index(temp_txt_file, chunks, index_dir=index_dir)

        # Directory should have been created
        assert Path(index_dir).exists()
