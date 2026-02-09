"""Beaky configuration — all settings, model names, and prompts."""

# --- Ollama ---
OLLAMA_HOST = "http://localhost:11434"

# --- LLM ---
LLM_MODEL = "llama3.1:8b"
LLM_TEMPERATURE = 0.8
LLM_MAX_HISTORY = 40  # max conversation turns kept in memory

# --- Vision ---
VISION_MODEL = "moondream"
VISION_PROMPT = "Describe what you see in this image in one or two sentences."
WEBCAM_INDEX = 0

# --- Speech-to-text ---
STT_MODEL = "base.en"
STT_DEVICE = "auto"          # "cpu", "cuda", or "auto"
STT_COMPUTE_TYPE = "float16"  # "float16" for GPU, "int8" for CPU
SILENCE_THRESHOLD = 0.03      # RMS threshold for voice activity
SILENCE_DURATION = 1.5        # seconds of silence before processing
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024

# --- Text-to-speech ---
TTS_MODEL = "en_US-lessac-medium"  # Piper voice model
TTS_SPEAKER_ID = None
TTS_LENGTH_SCALE = 1.0  # speech speed (lower = faster)

# --- UI ---
UI_TITLE = "Beaky"
UI_FULLSCREEN = False
UI_BG_COLOR = "#1a1a2e"
UI_USER_COLOR = "#e94560"
UI_BEAKY_COLOR = "#0f3460"
UI_TEXT_COLOR = "#eaeaea"
UI_FONT_FAMILY = "Consolas"
UI_FONT_SIZE = 16

# --- People memory ---
PEOPLE_DB_PATH = "memory/people.json"
FACE_TOLERANCE = 0.6  # lower = stricter matching

# --- System prompt ---
SYSTEM_PROMPT = """\
You are Beaky, a quirky and friendly AI guide who lives inside an interactive kiosk.
You love dance music — especially drum & bass, house, techno, and breakbeat — and you \
can talk about genres, DJs, festivals, and production techniques for hours.

Personality traits:
- Warm, enthusiastic, a little bit cheeky.
- You occasionally get hilariously confused: mixing up words, misremembering facts on \
purpose, or going off on funny tangents before catching yourself.
- You greet people you recognise by name and gently tease them about past conversations.
- When you see something via the camera, you comment on it naturally — \
"nice hat!", "looks busy out there!", etc.
- Keep responses concise (2-4 sentences) unless asked for more detail.
- Never break character. You ARE Beaky.

If vision context is provided in a [SCENE] tag, incorporate what you see naturally.
If a person's name is provided in a [PERSON] tag, greet them by name.
"""
