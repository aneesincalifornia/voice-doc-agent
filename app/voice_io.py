import os
import sys
import time
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

def record_from_mic(duration: int = 30, max_retries: int = 3) -> bytes:
    """
    Record audio from the microphone with automatic retry on PortAudio errors.

    Automatically uses the current default input device's native sample rate
    to avoid PortAudio format mismatch errors.

    On PortAudioError (which can be transient on macOS due to AUHAL state issues),
    retries up to max_retries times with PortAudio re-initialization between
    attempts. Only raises RuntimeError after all retries exhausted.

    Press Enter to stop recording (or max duration_seconds).
    Returns WAV bytes.
    """
    import numpy as np

    last_error = None

    for attempt in range(max_retries):
        try:
            # Freshly query the current default input device at record time
            # (not cached) to handle device changes (e.g., headphones plugged/unplugged)
            try:
                default_input_idx = sd.default.device[0]
                device_info = sd.query_devices(default_input_idx)

                if device_info["max_input_channels"] == 0:
                    raise RuntimeError(
                        f"Default input device '{device_info['name']}' has no input channels. "
                        "Please check System Settings → Sound or select a different microphone."
                    )

                # Use the device's native sample rate to prevent CoreAudio resampling issues
                sample_rate = int(device_info["default_samplerate"])
            except RuntimeError:
                # Re-raise RuntimeError (device has no input channels) — don't retry
                raise
            except Exception as e:
                # Device query error — this is a hard error, don't retry
                raise RuntimeError(
                    f"Failed to query microphone device: {e}\n"
                    "Check: (1) System Settings → Privacy & Security → Microphone (allow this app)\n"
                    "       (2) Run 'python check_mic.py' for detailed device diagnostics"
                )

            if attempt > 0:
                print(f"Recording... (attempt {attempt + 1}/{max_retries}, using {sample_rate} Hz). Press Enter to stop.")
            else:
                print(f"Recording... (using {sample_rate} Hz). Press Enter to stop.")

            audio_data = []

            def audio_callback(indata, frames, time, status):
                if status:
                    print(f"Audio warning: {status}", file=sys.stderr)
                audio_data.append(indata.copy())

            # Record in a stream with callback
            stream = sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                callback=audio_callback,
                blocksize=1024,
                device=default_input_idx
            )

            with stream:
                # Wait for user to press Enter to stop
                input()

            if not audio_data:
                raise ValueError("No audio data captured. Please speak into your microphone.")

            # Concatenate all audio frames
            audio_array = np.concatenate(audio_data, axis=0)
            audio_array = (audio_array * 32767).astype('int16')

            # Write to WAV bytes
            wav_buffer = BytesIO()
            wavfile.write(wav_buffer, sample_rate, audio_array)
            wav_buffer.seek(0)
            return wav_buffer.getvalue()

        except sd.PortAudioError as e:
            last_error = e
            if attempt < max_retries - 1:
                # Transient PortAudio error — try to recover by re-initializing PortAudio
                print(f"\n⚠️  Audio system transient error (attempt {attempt + 1}/{max_retries}). Retrying...")
                try:
                    # Force PortAudio to rebuild its internal state
                    sd._terminate()
                    time.sleep(0.3)  # Give CoreAudio a moment to release resources
                    sd._initialize()
                except Exception as init_error:
                    print(f"⚠️  Re-initialization warning: {init_error}")
            else:
                # All retries exhausted — raise final error
                raise RuntimeError(
                    f"Microphone recording failed after {max_retries} attempts: {e}\n"
                    "This usually means:\n"
                    "  (1) Microphone permission not granted\n"
                    "      → System Settings → Privacy & Security → Microphone\n"
                    "      → Add Terminal/iTerm/VS Code to allowed apps\n"
                    "  (2) Microphone device unavailable or disconnected\n"
                    "      → Run 'python check_mic.py' to diagnose"
                )
        except Exception as e:
            # Non-PortAudio error — don't retry, raise immediately
            raise RuntimeError(f"Microphone recording failed: {e}")

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

def generate_speech_bytes(text: str, voice: str = "alloy") -> bytes:
    """
    Generate TTS audio for the given text and return raw MP3 bytes.

    Used by callers that handle playback themselves (e.g. a browser via
    Streamlit's st.audio()). Returns empty bytes for blank/whitespace text.
    """
    if not text or not text.strip():
        return b""

    client = get_client()
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text[:4096]  # TTS has a 4096 char limit
    )
    return response.content

def speak_response(text: str, voice: str = "alloy") -> None:
    """Speak response text out loud using OpenAI TTS, played via macOS afplay."""
    try:
        audio_bytes = generate_speech_bytes(text, voice=voice)
    except Exception as e:
        print(f"⚠ Text-to-speech failed: {e}")
        return

    if not audio_bytes:
        return

    try:
        # Save to temp file and play
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # Play using macOS afplay (available on all Macs)
        subprocess.run(["afplay", tmp_path], check=True)
        os.unlink(tmp_path)
    except FileNotFoundError:
        print("⚠ 'afplay' not found (macOS only). Skipping speech output.")
    except Exception as e:
        print(f"⚠ Text-to-speech failed: {e}")

def has_mic_available() -> bool:
    """Check if a working input device is available (with input channels)."""
    try:
        # Query all input devices
        devices = sd.query_devices()
        input_devices = [
            d for d in devices
            if isinstance(d, dict) and d.get("max_input_channels", 0) > 0
        ]

        if not input_devices:
            return False

        # Check if the default input device has input channels
        default_input_idx = sd.default.device[0]
        default_device = sd.query_devices(default_input_idx)

        return default_device.get("max_input_channels", 0) > 0
    except Exception:
        return False
