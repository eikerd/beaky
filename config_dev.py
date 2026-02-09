"""Development config for WSL2 - simulates hardware without actual devices."""

from config import *

# Override webcam to use a mock/placeholder
WEBCAM_INDEX = None  # Disable webcam

# Use CPU for STT (no CUDA in WSL2 usually)
STT_DEVICE = "cpu"
STT_COMPUTE_TYPE = "int8"

# Disable fullscreen for WSL2 X server
UI_FULLSCREEN = False

# Note: This won't work for a real kiosk, just for testing the code structure
