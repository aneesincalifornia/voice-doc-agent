import os
import hashlib
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List

def get_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file for cache keying."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def get_or_build_index(
    document_path: str,
    chunks: List[Document],
    index_dir: str = "indexes"
) -> FAISS:
    """
    Get or build a FAISS index for the document.

    Indexes are cached at indexes/<file-hash>/index.faiss
    If a document was already indexed, loads from cache (saves embedding cost).
    """
    file_hash = get_file_hash(document_path)
    cache_path = Path(index_dir) / file_hash
    cache_path.mkdir(parents=True, exist_ok=True)

    index_file = cache_path / "index.faiss"
    pkl_file = cache_path / "index.pkl"

    # If cached, load from disk
    if index_file.exists() and pkl_file.exists():
        print(f"✓ Loading cached index from {cache_path}")
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        vector_store = FAISS.load_local(
            str(cache_path),
            embeddings,
            allow_dangerous_deserialization=True
        )
        return vector_store

    # Build fresh index
    print(f"✓ Building new index (file hash: {file_hash[:8]}...)")
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(str(cache_path))

    print(f"✓ Index saved to {cache_path}")
    return vector_store
