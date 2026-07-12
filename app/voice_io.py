import os
import sys
import tempfile
import subprocess
from io import BytesIO
import sounddevice as sd
import scipy.io.wavfile as wavfile
from openai import OpenAI
import threading

def get_client():
    """Lazily initialize OpenAI client to allow test mocking."""
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def record_from_mic(duration: int = 30, sample_rate: int = 16000) -> bytes:
    """
    Record audio from the microphone.

    Press Enter to start, Enter again to stop (or max duration_seconds).
    Returns WAV bytes.
    """
    print("Press Enter to start recording (max 30 seconds)...")
    input()

    print("Recording... press Enter to stop.")

    audio_data = []
    recording = True

    def audio_callback(indata, frames, time, status):
        if status:
            print(f"Audio error: {status}", file=sys.stderr)
        audio_data.append(indata.copy())

    try:
        # Record in a thread with a callback
        stream = sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            callback=audio_callback,
            blocksize=1024
        )

        with stream:
            # Wait for user to press Enter
            input()
            recording = False
    except Exception as e:
        raise RuntimeError(f"Microphone recording failed: {e}")

    if not audio_data:
        raise ValueError("No audio data captured")

    # Concatenate all audio frames
    import numpy as np
    audio_array = np.concatenate(audio_data, axis=0)
    audio_array = (audio_array * 32767).astype('int16')

    # Write to WAV bytes
    wav_buffer = BytesIO()
    wavfile.write(wav_buffer, sample_rate, audio_array)
    wav_buffer.seek(0)
    return wav_buffer.getvalue()

def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio bytes using OpenAI Whisper."""
    wav_buffer = BytesIO(audio_bytes)

    try:
        client = get_client()
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.wav", wav_buffer, "audio/wav"),
            language="en"
        )
        text = transcript.text.strip()

        if not text:
            raise ValueError("Whisper returned empty transcription")

        return text
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}")

def speak_response(text: str, voice: str = "alloy") -> None:
    """Speak response text using OpenAI TTS."""
    if not text or not text.strip():
        return

    try:
        client = get_client()
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text[:4096]  # TTS has a 4096 char limit
        )

        # Save to temp file and play
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        # Play using macOS afplay (available on all Macs)
        subprocess.run(["afplay", tmp_path], check=True)
        os.unlink(tmp_path)
    except FileNotFoundError:
        print("⚠ 'afplay' not found (macOS only). Skipping speech output.")
    except Exception as e:
        print(f"⚠ Text-to-speech failed: {e}")

def has_mic_available() -> bool:
    """Check if a microphone is available."""
    try:
        device_info = sd.default.device
        return device_info is not None
    except Exception:
        return False
