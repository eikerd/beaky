"""Speech-to-text using faster-whisper with voice activity detection."""

import io
import logging
import struct
import tempfile
import wave

import numpy as np
import pyaudio
from faster_whisper import WhisperModel

import config

log = logging.getLogger(__name__)


class STT:
    def __init__(self):
        log.info("Loading faster-whisper model '%s' ...", config.STT_MODEL)
        self.model = WhisperModel(
            config.STT_MODEL,
            device=config.STT_DEVICE,
            compute_type=config.STT_COMPUTE_TYPE,
        )
        self.sample_rate = config.SAMPLE_RATE
        self.chunk_size = config.CHUNK_SIZE
        self.silence_threshold = config.SILENCE_THRESHOLD
        self.silence_duration = config.SILENCE_DURATION
        self._pa = pyaudio.PyAudio()

    @staticmethod
    def _rms(data: bytes) -> float:
        """Compute RMS of 16-bit PCM audio data."""
        count = len(data) // 2
        if count == 0:
            return 0.0
        shorts = struct.unpack(f"<{count}h", data)
        return (sum(s * s for s in shorts) / count) ** 0.5 / 32768.0

    def listen(self, status_callback=None) -> str | None:
        """
        Block until speech is detected, record until silence, transcribe, and return text.
        Returns None if nothing meaningful was captured.

        Args:
            status_callback: Optional function(status_msg: str) called on status changes
        """
        stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
        )

        log.info("Listening for speech...")
        frames: list[bytes] = []
        speaking = False
        silent_chunks = 0
        silence_limit = int(self.silence_duration * self.sample_rate / self.chunk_size)

        try:
            while True:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                rms = self._rms(data)

                if not speaking:
                    if rms > self.silence_threshold:
                        speaking = True
                        silent_chunks = 0
                        frames.append(data)
                        log.info("Speech detected (RMS=%.4f)", rms)
                        if status_callback:
                            status_callback("🎤 Voice detected - speak now!")
                else:
                    frames.append(data)
                    if rms < self.silence_threshold:
                        silent_chunks += 1
                        if silent_chunks >= silence_limit:
                            log.info("Silence detected, processing...")
                            if status_callback:
                                status_callback("Processing speech...")
                            break
                    else:
                        silent_chunks = 0
        finally:
            stream.stop_stream()
            stream.close()

        if not frames:
            return None

        # Write to a temporary WAV file for faster-whisper
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            with wave.open(tmp.name, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(b"".join(frames))
            tmp_path = tmp.name

        segments, info = self.model.transcribe(tmp_path, beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments).strip()

        if text:
            log.info("Transcribed: %s", text)
        else:
            log.info("No speech transcribed")
            return None

        return text

    def shutdown(self):
        self._pa.terminate()
