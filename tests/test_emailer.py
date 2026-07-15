import pytest
from unittest.mock import Mock, patch, MagicMock
import smtplib
from app.emailer import send_transcript_email


def test_send_transcript_email_success(monkeypatch):
    """Test successful email sending."""
    # Set env vars
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "test@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "apppassword")

    # Mock SMTP
    mock_smtp = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp) as mock_smtp_class:
        mock_smtp.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp.__exit__ = Mock(return_value=None)

        send_transcript_email("recipient@example.com", "Q: Test?\nA: Test answer", "test.pdf")

        # Verify SMTP was called correctly
        mock_smtp_class.assert_called_once_with("smtp.gmail.com", 587)
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("test@gmail.com", "apppassword")
        mock_smtp.send_message.assert_called_once()


def test_send_transcript_email_missing_credentials(monkeypatch):
    """Test that missing SMTP credentials raise RuntimeError."""
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_PORT", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="Email configuration incomplete"):
        send_transcript_email("user@example.com", "transcript", "doc.pdf")


def test_send_transcript_email_invalid_port(monkeypatch):
    """Test that invalid SMTP_PORT raises RuntimeError."""
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "not_a_number")
    monkeypatch.setenv("SMTP_USER", "test@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "password")

    with pytest.raises(RuntimeError, match="SMTP_PORT must be a number"):
        send_transcript_email("recipient@example.com", "transcript", "doc.pdf")


def test_send_transcript_email_auth_error(monkeypatch):
    """Test that SMTP authentication error is handled."""
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "wrong@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "wrongpass")

    mock_smtp = MagicMock()
    mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, "5.7.8 Authentication failed")

    with patch("smtplib.SMTP", return_value=mock_smtp) as mock_smtp_class:
        mock_smtp.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp.__exit__ = Mock(return_value=None)

        with pytest.raises(RuntimeError, match="SMTP login failed"):
            send_transcript_email("recipient@example.com", "transcript", "doc.pdf")


def test_send_transcript_email_smtp_error(monkeypatch):
    """Test that other SMTP errors are handled."""
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "test@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "password")

    mock_smtp = MagicMock()
    mock_smtp.send_message.side_effect = smtplib.SMTPException("Server error")

    with patch("smtplib.SMTP", return_value=mock_smtp) as mock_smtp_class:
        mock_smtp.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp.__exit__ = Mock(return_value=None)

        with pytest.raises(RuntimeError, match="SMTP error"):
            send_transcript_email("recipient@example.com", "transcript", "doc.pdf")


def test_send_transcript_email_format(monkeypatch):
    """Test that email is formatted correctly."""
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "sender@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "password")

    mock_smtp = MagicMock()

    with patch("smtplib.SMTP", return_value=mock_smtp) as mock_smtp_class:
        mock_smtp.__enter__ = Mock(return_value=mock_smtp)
        mock_smtp.__exit__ = Mock(return_value=None)

        send_transcript_email("recipient@example.com", "Test transcript", "test_doc.pdf")

        # Check that send_message was called
        mock_smtp.send_message.assert_called_once()

        # Get the message that was sent
        sent_message = mock_smtp.send_message.call_args[0][0]

        # Verify message headers
        assert sent_message["To"] == "recipient@example.com"
        assert sent_message["From"] == "sender@gmail.com"
        assert "test_doc.pdf" in sent_message["Subject"]

        # Verify message body contains transcript
        # For MIMEMultipart, get the first part's payload
        message_body = sent_message.get_payload()[0].get_payload()
        assert "Test transcript" in message_body
