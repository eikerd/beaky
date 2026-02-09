# Running Beaky on Windows (Recommended for Kiosk)

Since you're developing on WSL2, here's how to run Beaky natively on Windows for full hardware access (webcam, microphone, speakers, GPU).

## Why Windows?

WSL2 limitations:
- ❌ No webcam access
- ❌ No microphone/speaker access without complex PulseAudio setup
- ❌ No direct GPU passthrough for optimal performance
- ✅ Windows has native access to all hardware

## Setup Steps

### 1. Install Python 3.13 on Windows

Download from [python.org](https://www.python.org/downloads/) and install.

Check installation:
```powershell
python --version
# Should show Python 3.13.x
```

### 2. Install Ollama for Windows

Download from [ollama.ai](https://ollama.ai/download/windows) and install.

Pull models:
```powershell
ollama pull llama3.1:8b
ollama pull moondream
```

Verify GPU usage:
```powershell
ollama run llama3.1:8b
# Should show CUDA/GPU info if RTX 5060 Ti is detected
```

### 3. Install Piper TTS

1. Download Piper for Windows from [rhasspy/piper releases](https://github.com/rhasspy/piper/releases)
2. Extract to `C:\Program Files\piper\` (or anywhere)
3. Add the directory to your PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" under User variables
   - Add the piper directory

4. Download the voice model:
   ```powershell
   # In the piper directory
   Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -OutFile "en_US-lessac-medium.onnx"
   Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" -OutFile "en_US-lessac-medium.onnx.json"
   ```

### 4. Install Python dependencies

In PowerShell or Command Prompt (in the beaky directory):
```powershell
pip install -r requirements.txt
```

**Note**: PyAudio should install cleanly on Windows. If it fails:
```powershell
pip install pipwin
pipwin install pyaudio
```

### 5. Verify setup

```powershell
python verify_setup.py
```

All checks should pass ✓

### 6. Run Beaky

```powershell
python main.py
```

## GPU Configuration

To ensure Ollama uses your RTX 5060 Ti:

1. Install latest NVIDIA drivers
2. Verify CUDA is available:
   ```powershell
   nvidia-smi
   ```
3. Ollama will automatically detect and use the GPU

## Troubleshooting

**Webcam not working**: Check if other apps can access it. May need to grant camera permissions in Windows Settings > Privacy > Camera.

**No audio**: Check Windows audio settings, ensure correct input/output devices are selected.

**Ollama not using GPU**: Install [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) if not already installed.

## Development Workflow

You can:
- Edit code in WSL2 (since the `/mnt/d/beaky` directory is shared)
- Run Beaky on Windows for testing with real hardware
- Use `git` from either WSL2 or Windows (same repo)

This gives you the best of both worlds: Linux dev tools + Windows hardware access.
