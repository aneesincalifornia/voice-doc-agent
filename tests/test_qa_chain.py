import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.qa_chain import query_document

def test_query_document_found(mock_openai_key):
    """Test querying a document when answer is found."""
    # Mock retriever and vector store
    mock_vector_store = MagicMock(spec=FAISS)

    mock_docs = [
        Document(
            page_content="Leave policy: 20 days annually",
            metadata={"page": 1}
        ),
        Document(
            page_content="Sick leave: 5 days per year",
            metadata={"page": 2}
        ),
    ]

    # Mock similarity_search_with_score to return docs with high scores
    mock_vector_store.similarity_search_with_score.return_value = [
        (mock_docs[0], 0.95),
        (mock_docs[1], 0.85),
    ]

    with patch("app.qa_chain.ChatOpenAI") as mock_chat_openai:
        # Mock the LLM to return a message with the expected content
        mock_message = MagicMock()
        mock_message.content = "Employees get 20 days of annual leave."
        mock_chat_instance = MagicMock()
        mock_chat_instance.invoke.return_value = mock_message
        mock_chat_openai.return_value = mock_chat_instance

        with patch("app.qa_chain.PromptTemplate") as mock_prompt_template:
            # Mock the prompt template to return a mock that supports chaining
            mock_prompt = MagicMock()

            # Make the LCEL chain work: prompt | llm
            # When we do prompt | llm, it returns something that can be invoked
            mock_chain = MagicMock()
            mock_message_result = MagicMock()
            mock_message_result.content = "Employees get 20 days of annual leave."
            mock_chain.invoke.return_value = mock_message_result

            # Set up the chain to work with | operator
            mock_prompt.__or__.return_value = mock_chain

            mock_prompt_template.return_value = mock_prompt

            with patch("app.qa_chain.os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda k, default=None: {
                    "CHAT_MODEL": "gpt-4o-mini",
                    "OPENAI_API_KEY": "sk-test"
                }.get(k, default)

                answer, found, sources = query_document(
                    mock_vector_store,
                    "How much leave do employees get?",
                    threshold=0.5
                )

    assert found is True
    assert "20 days" in str(answer)
    assert len(sources) == 2
    assert sources[0]["page"] == 1

@patch("app.qa_chain.ChatOpenAI")
def test_query_document_below_threshold(mock_chat_openai, mock_openai_key):
    """Test that low-confidence queries don't call the LLM."""
    mock_vector_store = MagicMock(spec=FAISS)

    mock_doc = Document(page_content="Unrelated content", metadata={"page": 1})
    mock_vector_store.similarity_search_with_score.return_value = [
        (mock_doc, 0.2),  # Below 0.5 threshold
    ]

    with patch("app.qa_chain.os.getenv") as mock_getenv:
        mock_getenv.side_effect = lambda k, default=None: {
            "CHAT_MODEL": "gpt-4o-mini",
            "OPENAI_API_KEY": "sk-test"
        }.get(k, default)

        answer, found, sources = query_document(
            mock_vector_store,
            "What is quantum physics?",
            threshold=0.5
        )

    # Should return "not found" without calling LLM
    assert found is False
    assert "No such information found" in answer
    assert len(sources) == 0
    # LLM should NOT have been called
    mock_chat_openai.assert_not_called()

def test_query_document_llm_returns_sentinel(mock_openai_key):
    """Test when LLM returns the 'not found' sentinel phrase."""
    mock_vector_store = MagicMock(spec=FAISS)

    mock_doc = Document(page_content="Some content", metadata={"page": 1})
    mock_vector_store.similarity_search_with_score.return_value = [
        (mock_doc, 0.7),
    ]

    # LLM returns the sentinel
    with patch("app.qa_chain.ChatOpenAI") as mock_chat_openai:
        mock_message = MagicMock()
        mock_message.content = "No such information found in the document."
        mock_chat_instance = MagicMock()
        mock_chat_instance.invoke.return_value = mock_message
        mock_chat_openai.return_value = mock_chat_instance

        with patch("app.qa_chain.PromptTemplate") as mock_prompt_template:
            # Mock the chain
            mock_prompt = MagicMock()
            mock_chain = MagicMock()
            mock_message_result = MagicMock()
            mock_message_result.content = "No such information found in the document."
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
                    "Specific detail X?",
                    threshold=0.5
                )

    assert found is False
    assert "No such information found" in str(answer)

@patch("app.qa_chain.ChatOpenAI")
def test_query_document_empty_retrieval(mock_chat_openai, mock_openai_key):
    """Test when retrieval returns no documents."""
    mock_vector_store = MagicMock(spec=FAISS)
    mock_vector_store.similarity_search_with_score.return_value = []

    with patch("app.qa_chain.os.getenv") as mock_getenv:
        mock_getenv.side_effect = lambda k, default=None: {
            "CHAT_MODEL": "gpt-4o-mini",
            "OPENAI_API_KEY": "sk-test"
        }.get(k, default)

        answer, found, sources = query_document(
            mock_vector_store,
            "Any question?",
            threshold=0.5
        )

    assert found is False
    assert "No such information found" in answer
    assert sources == []

@patch("app.qa_chain.ChatOpenAI")
def test_query_document_custom_threshold(mock_chat_openai, mock_openai_key):
    """Test that custom threshold is respected."""
    mock_vector_store = MagicMock(spec=FAISS)

    mock_doc = Document(page_content="Content", metadata={"page": 1})
    mock_vector_store.similarity_search_with_score.return_value = [
        (mock_doc, 0.6),  # Above 0.5 but below 0.7
    ]

    with patch("app.qa_chain.os.getenv") as mock_getenv:
        mock_getenv.side_effect = lambda k, default=None: {
            "CHAT_MODEL": "gpt-4o-mini",
            "OPENAI_API_KEY": "sk-test"
        }.get(k, default)

        # With threshold 0.7, should not find
        answer, found, sources = query_document(
            mock_vector_store,
            "Question?",
            threshold=0.7
        )

    assert found is False
    mock_chat_openai.assert_not_called()
