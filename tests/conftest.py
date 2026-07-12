import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    Employee Leave Policy

    Annual Leave:
    Employees are entitled to 20 days of annual leave per year.
    Leave must be taken in agreement with the manager.

    Sick Leave:
    Employees can take up to 5 days of sick leave per year.
    Medical documentation may be required.

    Public Holidays:
    The company observes 10 public holidays per year.
    These are listed in the company calendar.

    Remote Work:
    Remote work is allowed 2 days per week.
    Core hours are 10 AM to 3 PM.

    Health Insurance:
    The company provides comprehensive health insurance.
    Coverage includes dental and vision.
    """

@pytest.fixture
def temp_txt_file(sample_text):
    """Create a temporary text file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(sample_text)
        f.flush()
        yield f.name
    Path(f.name).unlink()

@pytest.fixture
def temp_pdf_file():
    """Create a minimal PDF file for testing."""
    try:
        from pypdf import PdfWriter
        from io import BytesIO
        import tempfile

        writer = PdfWriter()
        page_data = {
            "font_name_a": "F1"
        }
        writer.add_blank_page(width=200, height=200)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            writer.write(f)
            f.flush()
            yield f.name
        Path(f.name).unlink()
    except ImportError:
        pytest.skip("pypdf not available")

@pytest.fixture
def mock_openai_key(monkeypatch):
    """Mock OPENAI_API_KEY environment variable."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")
