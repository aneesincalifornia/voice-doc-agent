import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from typing import List

def load_document(path: str) -> List[Document]:
    """
    Load a document by file extension: .pdf, .docx, or .txt.

    Returns a list of Document objects with page_content and metadata.
    Raises FileNotFoundError if the file doesn't exist.
    Raises ValueError if the file type is unsupported.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Document not found at: {path}")

    file_ext = path.suffix.lower()

    if file_ext == ".pdf":
        return load_pdf(str(path))
    elif file_ext == ".docx":
        return load_docx(str(path))
    elif file_ext == ".txt":
        return load_txt(str(path))
    else:
        raise ValueError(
            f"Unsupported file type: {file_ext}. "
            f"Supported types: .pdf, .docx, .txt"
        )

def load_pdf(pdf_path: str) -> List[Document]:
    """Load a PDF file using PyPDFLoader."""
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    print(f"✓ Loaded {len(pages)} pages from PDF")
    return pages

def load_docx(docx_path: str) -> List[Document]:
    """Load a DOCX file."""
    from docx import Document as DocxDocument

    doc = DocxDocument(docx_path)

    # Extract all paragraphs into a single or per-paragraph Documents
    full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    if not full_text.strip():
        raise ValueError(f"No extractable text found in DOCX: {docx_path}")

    documents = [
        Document(
            page_content=full_text,
            metadata={
                "source": docx_path,
                "page": 0,
                "type": "docx"
            }
        )
    ]

    print(f"✓ Loaded DOCX document from {docx_path}")
    return documents

def load_txt(txt_path: str) -> List[Document]:
    """Load a plain text file."""
    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.strip():
        raise ValueError(f"No text found in file: {txt_path}")

    documents = [
        Document(
            page_content=content,
            metadata={
                "source": txt_path,
                "page": 0,
                "type": "txt"
            }
        )
    ]

    print(f"✓ Loaded text file from {txt_path}")
    return documents
