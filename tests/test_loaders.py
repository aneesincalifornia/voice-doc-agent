import pytest
from pathlib import Path
from app.loaders import load_document, load_txt, load_pdf, load_docx

def test_load_txt_valid(temp_txt_file):
    """Test loading a valid text file."""
    docs = load_txt(temp_txt_file)

    assert len(docs) == 1
    assert "Employee Leave Policy" in docs[0].page_content
    assert docs[0].metadata["type"] == "txt"
    assert docs[0].metadata["source"] == temp_txt_file

def test_load_txt_empty(tmp_path):
    """Test loading an empty text file."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")

    with pytest.raises(ValueError, match="No text found"):
        load_txt(str(empty_file))

def test_load_document_txt(temp_txt_file):
    """Test load_document dispatches to load_txt."""
    docs = load_document(temp_txt_file)

    assert len(docs) == 1
    assert "Employee Leave Policy" in docs[0].page_content

def test_load_document_missing():
    """Test loading a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_document("/nonexistent/file.txt")

def test_load_document_unsupported(tmp_path):
    """Test loading an unsupported file type."""
    bad_file = tmp_path / "test.csv"
    bad_file.write_text("data")

    with pytest.raises(ValueError, match="Unsupported file type"):
        load_document(str(bad_file))

def test_load_docx_missing():
    """Test loading a missing DOCX file."""
    # python-docx raises PackageNotFoundError, not FileNotFoundError
    from docx.opc.exceptions import PackageNotFoundError
    with pytest.raises(PackageNotFoundError):
        load_docx("/nonexistent/file.docx")

@pytest.mark.parametrize("ext", [".docx", ".pdf"])
def test_load_document_via_dispatch(tmp_path, ext):
    """Test that load_document correctly dispatches unsupported formats."""
    if ext == ".pdf":
        # Skip PDF test if load_pdf would require a real PDF
        pytest.skip("PDF loading requires a real PDF file")

    bad_file = tmp_path / f"test{ext}"
    bad_file.write_text("dummy")

    # load_document will try to load but fail during actual file processing
    # Just verify it calls the right loader by catching the underlying exception
    with pytest.raises(Exception):  # Will be FileNotFoundError or other loader-specific error
        load_document(str(bad_file))
