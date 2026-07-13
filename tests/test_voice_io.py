import pytest
from io import BytesIO
from unittest.mock import MagicMock, patch, call, PropertyMock
import scipy.io.wavfile as wavfile
import numpy as np
import sounddevice as sd

from app.voice_io import (
    transcribe_audio,
    speak_response,
    has_mic_available,
    record_from_mic,
)

@patch("app.voice_io.sd._initialize")
@patch("app.voice_io.sd._terminate")
@patch("app.voice_io.sd.query_devices")
@patch("app.voice_io.sd.default")
def test_record_from_mic_retries_on_portaudio_error(mock_default, mock_query_devices, mock_terminate, mock_initialize):
    """Test that record_from_mic retries on PortAudioError and calls terminate/initialize."""
    mock_device = {
        "name": "Test Microphone",
        "max_input_channels": 1,
        "default_samplerate": 44100
    }
    mock_query_devices.return_value = mock_device
    mock_default.device = (0, 1)

    with patch("app.voice_io.sd.InputStream") as mock_stream:
        # All attempts fail — verify retry mechanism is triggered
        mock_stream.side_effect = sd.PortAudioError("Persistent error")

        with pytest.raises(RuntimeError) as exc_info:
            record_from_mic(max_retries=2)

        # Verify PortAudio was re-initialized once (after first attempt)
        assert mock_terminate.call_count == 1
        assert mock_initialize.call_count == 1

        error_msg = str(exc_info.value)
        assert "after 2 attempts" in error_msg

@patch("app.voice_io.sd.InputStream")
@patch("app.voice_io.sd.query_devices")
@patch("app.voice_io.sd.default")
def test_record_from_mic_raises_after_retries_exhausted(mock_default, mock_query_devices, mock_stream):
    """Test that record_from_mic raises RuntimeError after all retries fail."""
    mock_device = {
        "name": "Test Microphone",
        "max_input_channels": 1,
        "default_samplerate": 44100
    }
    mock_query_devices.return_value = mock_device
    mock_default.device = (0, 1)

    # All attempts fail
    mock_stream.side_effect = sd.PortAudioError("Persistent error")

    with pytest.raises(RuntimeError) as exc_info:
        record_from_mic(max_retries=3)

    error_msg = str(exc_info.value)
    assert "after 3 attempts" in error_msg
    assert "Microphone permission not granted" in error_msg
    assert "check_mic.py" in error_msg

@patch("app.voice_io.sd.InputStream")
@patch("app.voice_io.sd.query_devices")
@patch("app.voice_io.sd.default")
def test_record_from_mic_port_audio_error(mock_default, mock_query_devices, mock_stream):
    """Test that PortAudioError produces an actionable message."""
    mock_device = {
        "name": "Broken Mic",
        "max_input_channels": 1,
        "default_samplerate": 44100
    }
    mock_query_devices.return_value = mock_device
    mock_default.device = (0, 1)

    mock_stream.side_effect = sd.PortAudioError("Some PortAudio error")

    with pytest.raises(RuntimeError) as exc_info:
        record_from_mic()

    error_msg = str(exc_info.value)
    assert "Microphone permission not granted" in error_msg
    assert "check_mic.py" in error_msg

@patch("app.voice_io.sd.query_devices")
@patch("app.voice_io.sd.default")
def test_record_from_mic_no_input_channels(mock_default, mock_query_devices):
    """Test that device with zero input channels is rejected."""
    mock_device = {
        "name": "Speakers",
        "max_input_channels": 0,
        "default_samplerate": 44100
    }
    mock_query_devices.return_value = mock_device
    mock_default.device = (0, 1)

    with pytest.raises(RuntimeError) as exc_info:
        record_from_mic()

    error_msg = str(exc_info.value)
    assert "no input channels" in error_msg

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

@patch("app.voice_io.sd.query_devices")
@patch("app.voice_io.sd.default")
def test_has_mic_available_true(mock_default, mock_query):
    """Test detecting when mic is available."""
    # Mock a device with input channels
    mock_device = {
        "name": "Built-in Microphone",
        "max_input_channels": 1,
        "default_samplerate": 44100
    }
    mock_query.side_effect = [
        [mock_device],  # First call: query all devices
        mock_device     # Second call: query default device
    ]
    mock_default.device = (0, 1)

    result = has_mic_available()
    assert result is True

@patch("app.voice_io.sd.query_devices")
@patch("app.voice_io.sd.default")
def test_has_mic_available_false_no_input_channels(mock_default, mock_query):
    """Test detecting when device has zero input channels."""
    # Mock a device with NO input channels (output-only)
    mock_device = {
        "name": "Speakers",
        "max_input_channels": 0,
        "default_samplerate": 44100
    }
    mock_query.side_effect = [
        [mock_device],  # First call: query all devices
        mock_device     # Second call: query default device
    ]
    mock_default.device = (0, 1)

    result = has_mic_available()
    assert result is False

@patch("app.voice_io.sd.query_devices")
def test_has_mic_available_exception(mock_query):
    """Test mic check with exception."""
    mock_query.side_effect = Exception("Device error")

    result = has_mic_available()

    assert result is False
