# Beaky 🦜

A local AI-powered interactive kiosk with voice I/O, webcam vision, and a conversation display. Beaky is a quirky, friendly guide and dance music expert who can recognize regulars, remember names, and comment on what it sees through the camera.

## Features

- **Voice interaction**: Speak to Beaky and hear responses via local speech-to-text and text-to-speech
- **Vision**: Beaky can see you through the webcam and comment on the scene
- **Face recognition**: Introduce yourself once and Beaky will greet you by name next time
- **Streaming display**: Full-screen Tkinter UI showing the conversation in real-time
- **Dance music expert**: Ask Beaky about drum & bass, house, techno, and more
- **100% local**: All models run on your machine via Ollama — no cloud dependencies

## Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| LLM | Llama 3.1 8B via Ollama | ~5GB VRAM, 100+ tok/s |
| Vision | Moondream2 via Ollama | ~2GB VRAM, modular/swappable |
| STT | faster-whisper | Fast local speech-to-text |
| TTS | Piper TTS | Lightweight local text-to-speech |
| UI | Tkinter | Full-screen conversation display |
| Face recognition | face_recognition | Optional, graceful degradation |

**Hardware target**: RTX 5060 Ti (16GB VRAM) or similar

## Installation

### 1. Install Ollama

Download and install Ollama from [ollama.ai](https://ollama.ai/), then pull the required models:

```bash
ollama pull llama3.1:8b
ollama pull moondream
```

Verify models load:
```bash
ollama run llama3.1:8b
ollama run moondream
```

### 2. Install Piper TTS

Download Piper TTS from [github.com/rhasspy/piper](https://github.com/rhasspy/piper/releases) and ensure the `piper` binary is on your PATH.

Download the voice model:
```bash
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

Place the `.onnx` and `.onnx.json` files in the same directory as the `piper` binary or configure the path in `config.py`.

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

**Note**: `face_recognition` is optional. If installation fails, Beaky will still work but face recognition will be disabled.

## Usage

```bash
python main.py
```

- The full-screen UI will appear showing the conversation
- Speak into your microphone
- Beaky will respond with voice and text
- Press **ESC** to exit

### Introducing yourself

Say **"My name is Alex"** or **"Call me Alex"** and Beaky will remember your face. Next time you appear on camera, Beaky will greet you by name.

Face encodings are stored in `memory/people.json`.

## Configuration

All settings are in `config.py`:

- **LLM model**: Change `LLM_MODEL` to swap models (e.g., `"llama3.2:3b"`)
- **Vision model**: Change `VISION_MODEL` to use a different vision model (e.g., `"llava"`)
- **TTS voice**: Change `TTS_MODEL` to use a different Piper voice
- **UI appearance**: Customize colors, fonts, and fullscreen mode
- **Beaky's personality**: Edit `SYSTEM_PROMPT` to change behavior

## Architecture

```
main.py              # Entry point
├── Worker thread    # Voice pipeline: STT → Vision → LLM → TTS
└── Main thread      # Tkinter UI (thread-safe queue updates)

brain/
├── llm.py          # Ollama chat with streaming + history
└── vision.py       # Webcam capture + scene description

voice/
├── stt.py          # faster-whisper with voice activity detection
└── tts.py          # Piper TTS with non-blocking playback

ui/
└── display.py      # Full-screen Tkinter conversation display

memory/
└── people.py       # Face recognition + JSON storage
```

## Troubleshooting

**No audio output**: Ensure PyAudio can access your speakers. On Linux, you may need to install `portaudio19-dev`.

**Webcam not detected**: Check `config.py` and set `WEBCAM_INDEX` to the correct device number (0, 1, 2...).

**Ollama connection failed**: Ensure Ollama is running (`ollama serve`) and `OLLAMA_HOST` in `config.py` matches the server address.

**Slow responses**: Reduce model sizes or adjust `LLM_TEMPERATURE` in `config.py`. Consider using `llama3.2:3b` for faster inference.

## License

MIT
