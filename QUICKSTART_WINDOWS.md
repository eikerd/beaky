# Windows Quick Start

## Prerequisites

1. **Python 3.9+** - Download from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation

2. **GPU Drivers** - Make sure your RTX 5060 Ti has latest NVIDIA drivers
   - Download from [nvidia.com](https://www.nvidia.com/download/index.aspx)

## Automatic Installation (Recommended)

1. **Open PowerShell as Administrator**
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

2. **Navigate to Beaky directory**
   ```powershell
   cd D:\beaky
   ```

3. **Run the setup script**
   ```powershell
   .\setup_windows.ps1
   ```

   Or double-click `INSTALL_WINDOWS.bat` (must run as Administrator)

4. **Wait for installation** (5-10 minutes)
   - Downloads and installs Ollama
   - Pulls AI models (~7GB download)
   - Installs Piper TTS
   - Installs Python packages

5. **Run Beaky**
   ```powershell
   python main.py
   ```

## Manual Installation

If the automatic setup fails, see [WINDOWS_SETUP.md](WINDOWS_SETUP.md) for detailed manual instructions.

## Troubleshooting

**"cannot be loaded because running scripts is disabled"**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Python not found**
- Reinstall Python and check "Add Python to PATH"
- Or add Python manually to PATH

**Ollama models fail to download**
- Check your internet connection
- Try pulling manually: `ollama pull llama3.1:8b`

**Import errors when running**
- Make sure you're in the correct directory: `cd D:\beaky`
- Verify packages installed: `pip list`

## Testing

After setup, verify everything works:
```powershell
python verify_setup.py
```

All checks should pass ✓

## First Run

1. Grant permissions if Windows asks for:
   - Camera access
   - Microphone access

2. Speak into your microphone when Beaky is listening

3. Press `ESC` to exit

## Need Help?

See [WINDOWS_SETUP.md](WINDOWS_SETUP.md) for detailed documentation.
