# Microphone Fix - PortAudio Error Resolution

## The Problem

You hit this error when trying to record:
```
⚠ Error: Microphone recording failed: Error opening InputStream: Internal PortAudio error [PaErrorCode -9986]
```

**What it means:** PortAudio (the underlying audio library) failed to open a recording stream. On macOS, this generic error code hides the real problem, which is usually:

1. **Microphone permission not granted** to Terminal/iTerm/VS Code
2. **Sample rate mismatch** (hardcoded 16000 Hz vs device's native rate, e.g., 44100/48000 Hz)
3. **Device unavailable** (disconnected headset, disabled microphone)

---

## The Fix (What Changed)

I've updated the code with **3 major improvements**:

### 1. **Dynamic Device Detection** (`app/voice_io.py`)
- **Before:** Hardcoded 16000 Hz sample rate (doesn't match most Mac mics)
- **After:** Query the device's native sample rate at record time (44100, 48000, etc.)
- This eliminates the CoreAudio resampling failure

### 2. **Better Error Messages** (`app/voice_io.py`)
- **Before:** Generic "Microphone recording failed"
- **After:** Actionable messages that tell you exactly what to check:
  - System Settings → Privacy & Security → Microphone
  - Run `python check_mic.py` for detailed diagnostics

### 3. **Diagnostic Tool** (New: `check_mic.py`)
- Run this tool to see what's really happening on your Mac
- Lists all audio devices, sample rates, and permission status
- Tests a 2-second recording to confirm audio is flowing

---

## How to Fix Your Mic (Step by Step)

### **Step 1: Run the Diagnostic**

```bash
cd /Users/aneesfatima/genai-projects/voice_doc_agent
source venv/bin/activate
python check_mic.py
```

### **What to Look For**

**Output Example:**
```
====================================================================
MICROPHONE DIAGNOSTIC TOOL
====================================================================

📡 AVAILABLE INPUT DEVICES:
  [0] Built-in Microphone
      Max Input Channels: 1
      Default Sample Rate: 44100 Hz
      ...
      ⭐ DEFAULT

📍 CURRENT DEFAULT INPUT DEVICE:
  Device Index: 0
  Name: Built-in Microphone
  Max Input Channels: 1
  Native Sample Rate: 44100 Hz

🎙️ TEST RECORDING (2 seconds):
  Recording 2s at 44100 Hz...
  Speak into your microphone...

  ✅ Recording successful!
     Samples captured: 88200
     Peak amplitude: 0.2543 (good level!)
     RMS level: 0.045321

====================================================================
✅ DIAGNOSIS: Microphone appears to be working correctly!
   Try running: python voice_agent.py data/sample_policy.txt
====================================================================
```

### **Step 2: Check Your System Settings**

If `check_mic.py` shows **very low audio** or **test recording failed**, do this:

**On macOS:**
1. Open **System Settings** (not System Preferences)
2. Go to **Privacy & Security** → **Microphone**
3. Look for **Terminal**, **iTerm**, or **VS Code** in the list
4. If missing → Click **+** → Add your terminal app
5. If there → Check the toggle is **ON**

### **Step 3: Try Recording Again**

Once `check_mic.py` shows your microphone working:

```bash
python voice_agent.py data/sample_policy.txt
```

When prompted:
```
[Press Enter to speak, or type a question, or 'exit']: 
```

Just press **Enter** (don't type anything) to trigger recording.

---

## Troubleshooting

### Scenario 1: "No input devices found"
**Problem:** Your Mac's audio system isn't detecting any microphone.

**Fix:**
- Check if your built-in mic is working: System Settings → Sound
- If using headphones with a mic, plug them in and re-run `check_mic.py`
- Try a USB headset/microphone

### Scenario 2: "Peak amplitude: 0.0001 (very low)"
**Problem:** Mic is detected but capturing silence or very low audio.

**Fix:**
1. Check the microphone isn't muted:
   - System Settings → Sound → Input → Built-in Microphone (selected?)
   - Try another app (Voice Memos) to confirm Mac mic works
2. If using headphones with mic:
   - Make sure the mic isn't covered
   - Try plugging headphones fully in
3. Grant permission to Terminal/iTerm/VS Code (see Step 2 above)

### Scenario 3: "PortAudio Error: [specific error]"
**Problem:** Still getting an audio error after diagnostic.

**Fix:**
1. Restart Terminal/VS Code
2. Restart your Mac (clear audio device state)
3. If using USB headset, try the built-in mic first (or vice versa)
4. Check System Settings → Sound → Input:
   - Make sure a device is **selected** (highlighted in blue)
   - Not "No input device selected"

---

## What the Agent Now Does

**When you press Enter to speak:**

1. ✅ Queries your Mac for the current default microphone
2. ✅ Reads that device's native sample rate (44100, 48000 Hz, etc.)
3. ✅ Records using the device's native rate (no resampling)
4. ✅ Sends raw audio to OpenAI Whisper for transcription
5. ✅ If anything fails, gives you a clear, actionable error

**No more generic "PortAudio -9986" errors** — you'll see exactly what's wrong.

---

## Quick Verification

**Before you report a problem, run these in order:**

```bash
# 1. Check your microphone setup
python check_mic.py

# 2. If that shows ✅, try the agent
python voice_agent.py data/sample_policy.txt

# 3. At the prompt, press Enter to record (not 'type')
# 4. Speak a question, press Enter to stop
```

If all 3 work, **recording is fixed!** ✅

---

## Advanced: What Changed Under the Hood

If you're curious, here's what I fixed:

**`app/voice_io.py` before:**
```python
stream = sd.InputStream(
    samplerate=16000,  # ❌ Hardcoded, unsupported on most Macs
    channels=1,
    callback=audio_callback,
    blocksize=1024
)
```

**`app/voice_io.py` after:**
```python
device_info = sd.query_devices(default_input_idx)
sample_rate = int(device_info["default_samplerate"])  # ✅ Device's native rate

stream = sd.InputStream(
    samplerate=sample_rate,  # ✅ Uses 44100, 48000, etc. (device's native)
    channels=1,
    callback=audio_callback,
    blocksize=1024,
    device=default_input_idx
)
```

This prevents CoreAudio from trying to resample (which fails with -9986).

---

## Summary

| Step | Command | What It Does |
|------|---------|-------------|
| 1 | `python check_mic.py` | Diagnose your mic setup |
| 2 | System Settings | Grant permission if needed |
| 3 | `python voice_agent.py data/sample_policy.txt` | Run the agent |
| 4 | Press Enter at prompt | Start recording |
| 5 | Speak + press Enter | Send question, hear answer |

**Good luck! Recording should work now.** 🎙️ ✨
