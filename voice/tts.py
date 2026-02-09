"""Text-to-speech using Piper TTS with non-blocking playback."""

import io
import logging
import subprocess
import threading
import wave

import pyaudio

import config

log = logging.getLogger(__name__)


class TTS:
    def __init__(self):
        self.model = config.TTS_MODEL
        self.speaker_id = config.TTS_SPEAKER_ID
        self.length_scale = config.TTS_LENGTH_SCALE
        self._pa = pyaudio.PyAudio()
        self._playback_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def synthesize(self, text: str) -> bytes:
        """Run Piper TTS and return raw WAV bytes."""
        cmd = ["piper", "--model", self.model, "--output-raw"]
        if self.speaker_id is not None:
            cmd += ["--speaker", str(self.speaker_id)]
        cmd += ["--length-scale", str(self.length_scale)]

        log.info("Synthesizing: %s", text[:80])
        result = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            capture_output=True,
        )
        if result.returncode != 0:
            log.error("Piper TTS failed: %s", result.stderr.decode())
            raise RuntimeError(f"Piper TTS error: {result.stderr.decode()}")
        return result.stdout

    def _play_raw(self, raw_audio: bytes, sample_rate: int = 22050, channels: int = 1, sample_width: int = 2):
        """Play raw PCM audio through PyAudio."""
        stream = self._pa.open(
            format=self._pa.get_format_from_width(sample_width),
            channels=channels,
            rate=sample_rate,
            output=True,
        )
        chunk_size = 4096
        try:
            for i in range(0, len(raw_audio), chunk_size):
                if self._stop_event.is_set():
                    break
                stream.write(raw_audio[i:i + chunk_size])
        finally:
            stream.stop_stream()
            stream.close()

    def speak(self, text: str, blocking: bool = False):
        """Synthesize and play text. Non-blocking by default."""
        raw_audio = self.synthesize(text)

        self._stop_event.clear()
        if blocking:
            self._play_raw(raw_audio)
        else:
            self._playback_thread = threading.Thread(
                target=self._play_raw, args=(raw_audio,), daemon=True
            )
            self._playback_thread.start()

    def stop(self):
        """Stop any current playback."""
        self._stop_event.set()
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=2)

    def wait(self):
        """Wait for current playback to finish."""
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join()

    def shutdown(self):
        self.stop()
        self._pa.terminate()
