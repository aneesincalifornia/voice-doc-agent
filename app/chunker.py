from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List

def chunk_documents(documents: List[Document]) -> List[Document]:
    """
    Split documents into chunks for embedding.

    Uses RecursiveCharacterTextSplitter to split at paragraph/sentence
    boundaries first, avoiding arbitrary mid-meaning cuts.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = splitter.split_documents(documents)

    print(f"✓ Created {len(chunks)} chunks from {len(documents)} document(s)")
    return chunks
