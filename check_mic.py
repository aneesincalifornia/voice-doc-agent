#!/usr/bin/env python3
"""
Microphone Diagnostic Tool

Run this to check your audio device configuration and test recording.
If the voice agent fails with a PortAudio error, this will help diagnose why.

Usage:
    python check_mic.py
"""

import sounddevice as sd
import numpy as np
import sys


def check_mic():
    """Diagnose microphone setup."""
    print("=" * 70)
    print("MICROPHONE DIAGNOSTIC TOOL")
    print("=" * 70)
    print()

    # 1. List all input devices
    print("📡 AVAILABLE INPUT DEVICES:")
    print("-" * 70)
    try:
        devices = sd.query_devices()
        input_devices = []

        for i, device in enumerate(devices):
            if device["max_input_channels"] > 0:
                input_devices.append((i, device))
                is_default = " ⭐ DEFAULT" if i == sd.default.device[0] else ""
                print(f"  [{i}] {device['name']}")
                print(f"      Max Input Channels: {device['max_input_channels']}")
                print(f"      Default Sample Rate: {device['default_samplerate']} Hz")
                print(f"      Latency (input): {device['default_low_input_latency']:.3f}s")
                print(f"      {is_default}")
                print()

        if not input_devices:
            print("  ❌ No input devices found!")
            print()
    except Exception as e:
        print(f"  ❌ Error querying devices: {e}")
        print()
        return False

    # 2. Check current default device
    print("📍 CURRENT DEFAULT INPUT DEVICE:")
    print("-" * 70)
    try:
        default_idx = sd.default.device[0]
        default_device = sd.query_devices(default_idx)
        print(f"  Device Index: {default_idx}")
        print(f"  Name: {default_device['name']}")
        print(f"  Max Input Channels: {default_device['max_input_channels']}")
        print(f"  Native Sample Rate: {int(default_device['default_samplerate'])} Hz")

        if default_device["max_input_channels"] == 0:
            print(f"\n  ⚠️  WARNING: This device has 0 input channels (output-only)")
            print(f"      Cannot record from this device!")
            return False
        print()
    except Exception as e:
        print(f"  ❌ Error reading default device: {e}")
        print()
        return False

    # 3. Test recording
    print("🎙️  TEST RECORDING (2 seconds):")
    print("-" * 70)
    try:
        sample_rate = int(default_device["default_samplerate"])
        duration = 2
        channels = 1

        print(f"  Recording {duration}s at {sample_rate} Hz ({channels} channel)...")
        print(f"  Speak into your microphone (or make a sound)...\n")

        audio = sd.rec(
            frames=int(sample_rate * duration),
            samplerate=sample_rate,
            channels=channels,
            dtype="float32"
        )
        sd.wait()

        # Analyze the recording
        audio = audio.flatten()
        peak = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio ** 2))

        print(f"  ✅ Recording successful!")
        print(f"     Samples captured: {len(audio)}")
        print(f"     Peak amplitude: {peak:.4f} (0.0 = silent, 1.0 = max)")
        print(f"     RMS level: {rms:.6f}")

        if peak < 0.01:
            print(f"\n  ⚠️  WARNING: Very low audio level detected (peak={peak:.4f})")
            print(f"      Check that your microphone is:")
            print(f"      1. Plugged in / switched on")
            print(f"      2. Not muted in System Settings → Sound")
            print(f"      3. Permitted in System Settings → Privacy & Security → Microphone")
            return False
        else:
            print(f"\n  ✅ Audio levels look good! Microphone is working.")
            return True

    except sd.PortAudioError as e:
        print(f"  ❌ PortAudio Error: {e}")
        print(f"\n  This usually means one of:")
        print(f"  1. Microphone permission not granted to Terminal/iTerm/VS Code")
        print(f"     → Fix: System Settings → Privacy & Security → Microphone")
        print(f"     → Add Terminal/iTerm/VS Code to the allowed apps list")
        print(f"  2. Sample rate mismatch (device doesn't support {sample_rate} Hz)")
        print(f"  3. The microphone device is disabled or unavailable")
        print()
        return False
    except Exception as e:
        print(f"  ❌ Error during recording: {e}")
        print()
        return False


if __name__ == "__main__":
    print()
    success = check_mic()
    print()
    print("=" * 70)
    if success:
        print("✅ DIAGNOSIS: Microphone appears to be working correctly!")
        print("   Try running: python voice_agent.py data/sample_policy.txt")
    else:
        print("❌ DIAGNOSIS: Microphone has issues (see above for details)")
        print("   Fix the issue and run this script again to verify.")
    print("=" * 70)
    print()

    sys.exit(0 if success else 1)
