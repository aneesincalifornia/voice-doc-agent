import pytest
from io import BytesIO
from unittest.mock import MagicMock, patch, call, PropertyMock
import scipy.io.wavfile as wavfile
import numpy as np

from app.voice_io import (
    transcribe_audio,
    speak_response,
    has_mic_available,
)

def test_transcribe_audio_success():
    """Test successful transcription."""
    # Create a dummy WAV file
    sample_rate = 16000
    duration = 1
    t = np.linspace(0, duration, sample_rate * duration)
    audio = np.sin(2 * np.pi * 440 * t) * 0.3  # 440 Hz tone
    audio = (audio * 32767).astype('int16')

    wav_buffer = BytesIO()
    wavfile.write(wav_buffer, sample_rate, audio)
    audio_bytes = wav_buffer.getvalue()

    with patch("app.voice_io.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_transcript = MagicMock()
        mock_transcript.text = "hello world"
        mock_client.audio.transcriptions.create.return_value = mock_transcript

        result = transcribe_audio(audio_bytes)

        assert result == "hello world"
        mock_client.audio.transcriptions.create.assert_called_once()

def test_transcribe_audio_empty_result():
    """Test transcription that returns empty string."""
    sample_rate = 16000
    silence = np.zeros(sample_rate, dtype='int16')

    wav_buffer = BytesIO()
    wavfile.write(wav_buffer, sample_rate, silence)
    audio_bytes = wav_buffer.getvalue()

    with patch("app.voice_io.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_transcript = MagicMock()
        mock_transcript.text = "   "  # Whitespace only
        mock_client.audio.transcriptions.create.return_value = mock_transcript

        with pytest.raises(RuntimeError, match="empty transcription"):
            transcribe_audio(audio_bytes)

def test_transcribe_audio_api_error():
    """Test transcription API error handling."""
    audio_bytes = b"dummy"

    with patch("app.voice_io.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.audio.transcriptions.create.side_effect = Exception("API Error")

        with pytest.raises(RuntimeError, match="Transcription failed"):
            transcribe_audio(audio_bytes)

@patch("app.voice_io.subprocess.run")
@patch("app.voice_io.os.unlink")
def test_speak_response_success(mock_unlink, mock_subprocess):
    """Test successful text-to-speech."""
    with patch("app.voice_io.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = b"mp3_data"
        mock_client.audio.speech.create.return_value = mock_response

        speak_response("Hello world", voice="alloy")

        mock_client.audio.speech.create.assert_called_once()
        mock_subprocess.assert_called_once()
        assert "afplay" in str(mock_subprocess.call_args)
        mock_unlink.assert_called_once()

@patch("app.voice_io.subprocess.run")
@patch("app.voice_io.os.unlink")
def test_speak_response_long_text_truncated(mock_unlink, mock_subprocess):
    """Test that long text is truncated to 4096 chars."""
    long_text = "a" * 5000

    with patch("app.voice_io.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = b"mp3_data"
        mock_client.audio.speech.create.return_value = mock_response

        speak_response(long_text)

        # Check that input was truncated
        call_kwargs = mock_client.audio.speech.create.call_args
        assert len(call_kwargs[1]["input"]) <= 4096

def test_speak_response_empty_text():
    """Test that empty text doesn't call TTS."""
    with patch("app.voice_io.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        speak_response("")

        # Should not call TTS
        mock_client.audio.speech.create.assert_not_called()

@patch("app.voice_io.subprocess.run", side_effect=FileNotFoundError)
def test_speak_response_afplay_not_found(mock_subprocess):
    """Test graceful fallback when afplay is not available."""
    with patch("app.voice_io.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = b"mp3_data"
        mock_client.audio.speech.create.return_value = mock_response

        # Should not raise, just print warning
        speak_response("Test")

        # afplay error should be caught
        assert True  # Just verify no exception

def test_speak_response_tts_error():
    """Test TTS API error handling."""
    with patch("app.voice_io.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.audio.speech.create.side_effect = Exception("TTS Error")

        # Should not raise, just print warning
        speak_response("Test")

        assert True

def test_has_mic_available_true():
    """Test detecting when mic is available."""
    with patch("app.voice_io.sd.default") as mock_default:
        mock_default.device = 0

        result = has_mic_available()

        assert result is True

def test_has_mic_available_false():
    """Test detecting when mic is not available."""
    with patch("app.voice_io.sd.default") as mock_default:
        mock_default.device = None

        result = has_mic_available()

        assert result is False

def test_has_mic_available_exception():
    """Test mic check with exception."""
    with patch("app.voice_io.sd.default") as mock_default:
        # Make accessing .device raise an exception
        type(mock_default).device = PropertyMock(side_effect=Exception("Device error"))

        result = has_mic_available()

        assert result is False
