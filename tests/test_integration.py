import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from app.loaders import load_document
from app.chunker import chunk_documents
from app.indexer import get_or_build_index
from app.qa_chain import query_document

@patch("app.indexer.FAISS.from_documents")
@patch("app.indexer.OpenAIEmbeddings")
def test_full_pipeline_found(mock_embeddings, mock_from_docs, sample_text, tmp_path, mock_openai_key):
    """Test full end-to-end pipeline when answer is found."""
    # Create a sample doc
    txt_file = tmp_path / "test.txt"
    txt_file.write_text(sample_text)

    # Load
    documents = load_document(str(txt_file))
    assert len(documents) > 0

    # Chunk
    chunks = chunk_documents(documents)
    assert len(chunks) > 0

    # Mock vector store
    mock_vector_store = MagicMock()
    mock_from_docs.return_value = mock_vector_store

    mock_doc = MagicMock()
    mock_doc.page_content = "Annual Leave: 20 days per year"
    mock_doc.metadata = {"page": 1}

    mock_vector_store.similarity_search_with_score.return_value = [
        (mock_doc, 0.95)
    ]

    with patch("app.indexer.os.getenv", return_value="sk-test-key"):
        index = get_or_build_index(str(txt_file), chunks, index_dir=str(tmp_path / "indexes"))

    # Query
    with patch("app.qa_chain.ChatOpenAI") as mock_chat:
        mock_message = MagicMock()
        mock_message.content = "Employees are entitled to 20 days of annual leave per year."
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_message
        mock_chat.return_value = mock_llm

        with patch("app.qa_chain.PromptTemplate") as mock_prompt_template:
            mock_prompt = MagicMock()
            mock_chain = MagicMock()
            mock_message_result = MagicMock()
            mock_message_result.content = "Employees are entitled to 20 days of annual leave per year."
            mock_chain.invoke.return_value = mock_message_result
            mock_prompt.__or__.return_value = mock_chain
            mock_prompt_template.return_value = mock_prompt

            with patch("app.qa_chain.os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda k, default=None: {
                    "CHAT_MODEL": "gpt-4o-mini",
                    "OPENAI_API_KEY": "sk-test"
                }.get(k, default)

                answer, found, sources = query_document(
                    mock_vector_store,
                    "How much annual leave do employees get?"
                )

    assert found is True
    assert "20 days" in str(answer)
    assert len(sources) > 0

@patch("app.indexer.FAISS.from_documents")
@patch("app.indexer.OpenAIEmbeddings")
def test_full_pipeline_not_found(mock_embeddings, mock_from_docs, sample_text, tmp_path, mock_openai_key):
    """Test full pipeline when answer is NOT found."""
    # Create sample doc
    txt_file = tmp_path / "test.txt"
    txt_file.write_text(sample_text)

    # Load and chunk
    documents = load_document(str(txt_file))
    chunks = chunk_documents(documents)

    # Mock vector store with low relevance
    mock_vector_store = MagicMock()
    mock_from_docs.return_value = mock_vector_store

    mock_doc = MagicMock()
    mock_doc.page_content = "Unrelated content"
    mock_doc.metadata = {"page": 1}

    mock_vector_store.similarity_search_with_score.return_value = [
        (mock_doc, 0.2)  # Below threshold
    ]

    with patch("app.indexer.os.getenv", return_value="sk-test-key"):
        index = get_or_build_index(str(txt_file), chunks, index_dir=str(tmp_path / "indexes"))

    # Query
    with patch("app.qa_chain.ChatOpenAI") as mock_chat:
        with patch("app.qa_chain.os.getenv") as mock_getenv:
            mock_getenv.side_effect = lambda k, default=None: {
                "CHAT_MODEL": "gpt-4o-mini",
                "OPENAI_API_KEY": "sk-test"
            }.get(k, default)

            answer, found, sources = query_document(
                mock_vector_store,
                "What is quantum computing?",
                threshold=0.5
            )

    assert found is False
    assert "No such information found" in answer
    # LLM should not have been called for low-relevance query
    mock_chat.assert_not_called()

@patch("app.indexer.FAISS.from_documents")
@patch("app.indexer.OpenAIEmbeddings")
def test_multiple_formats(mock_embeddings, mock_from_docs, tmp_path):
    """Test that different document formats can be loaded."""
    # Create a TXT file
    txt_file = tmp_path / "doc.txt"
    txt_file.write_text("This is a text document.")

    # Load TXT
    docs = load_document(str(txt_file))
    assert len(docs) == 1

    # Create a DOCX file (skip if python-docx not available)
    try:
        from docx import Document as DocxDocument

        docx_file = tmp_path / "doc.docx"
        doc = DocxDocument()
        doc.add_paragraph("This is a DOCX document.")
        doc.save(str(docx_file))

        docs = load_document(str(docx_file))
        assert len(docs) == 1
    except ImportError:
        pytest.skip("python-docx not available")

@patch("app.qa_chain.ChatOpenAI")
def test_web_fallback_integration(mock_chat, mock_openai_key, tmp_path):
    """Test web fallback flow when document query finds nothing."""
    from app.web_fallback import search_web_for_answer

    # Mock vector store with no match
    mock_vector_store = MagicMock()
    mock_vector_store.similarity_search_with_score.return_value = []

    # Query document (no match)
    with patch("app.qa_chain.os.getenv") as mock_getenv:
        mock_getenv.side_effect = lambda k, default=None: {
            "CHAT_MODEL": "gpt-4o-mini",
            "OPENAI_API_KEY": "sk-test"
        }.get(k, default)

        answer, found, sources = query_document(
            mock_vector_store,
            "Specific question?"
        )

    assert found is False

    # Now web fallback would be offered
    with patch("app.web_fallback.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Web answer"
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client.beta.chat.completions.create.return_value = mock_response

        web_result = search_web_for_answer("Specific question?")

    assert "[From the web, not your document]:" in web_result
    assert "Web answer" in web_result
