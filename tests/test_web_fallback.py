import pytest
from unittest.mock import MagicMock, patch

from app.web_fallback import search_web_for_answer

@patch("app.web_fallback.get_client")
def test_search_web_success(mock_get_client):
    """Test successful web search."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "The capital of France is Paris."
    mock_response.choices = [MagicMock(message=mock_message)]

    mock_client.beta.chat.completions.create.return_value = mock_response

    result = search_web_for_answer("What is the capital of France?")

    assert "[From the web, not your document]:" in result
    assert "Paris" in result
    mock_client.beta.chat.completions.create.assert_called_once()

@patch("app.web_fallback.get_client")
def test_search_web_api_error(mock_get_client):
    """Test web search API error with graceful fallback."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.beta.chat.completions.create.side_effect = Exception("API Error")

    result = search_web_for_answer("What is X?")

    assert "[General knowledge, unverified]:" in result
    # Should not raise, just fall back

@patch("app.web_fallback.get_client")
def test_search_web_result_labeled(mock_get_client):
    """Test that web results are clearly labeled."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Some web result"
    mock_response.choices = [MagicMock(message=mock_message)]

    mock_client.beta.chat.completions.create.return_value = mock_response

    result = search_web_for_answer("Question?")

    # Result should have clear label
    assert "[From the web, not your document]:" in result
    assert "Some web result" in result

@patch("app.web_fallback.os.getenv")
@patch("app.web_fallback.get_client")
def test_search_web_uses_env_model(mock_get_client, mock_getenv):
    """Test that custom model is used from env."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Result"
    mock_response.choices = [MagicMock(message=mock_message)]

    mock_client.beta.chat.completions.create.return_value = mock_response

    mock_getenv.side_effect = lambda k, default=None: {
        "CHAT_MODEL": "gpt-4o",
        "OPENAI_API_KEY": "sk-test"
    }.get(k, default)

    search_web_for_answer("Question?")

    # Check that the model parameter was used
    call_kwargs = mock_client.beta.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "gpt-4o"
