"""Text-to-speech using Fish Speech with GPU acceleration."""

import logging
import os
import tempfile
import threading

import numpy as np
import pyaudio
import soundfile as sf
import torch

log = logging.getLogger(__name__)

try:
    from fish_speech.models.text2semantic import TextToSemanticInference
    from fish_speech.models.vqgan import VQGANInference
    FISH_AVAILABLE = True
except ImportError:
    FISH_AVAILABLE = False
    log.warning("Fish Speech not installed: pip install fish-speech")


class TTS:
    def __init__(self, model_dir: str = "models/fish-speech", device: str = "cuda"):
        if not FISH_AVAILABLE:
            raise RuntimeError("Fish Speech not installed. Run: pip install fish-speech pynvml soundfile")

        log.info("Loading Fish Speech TTS on %s...", device)

        self.device = device
        self.sample_rate = 44100
        self._pa = pyaudio.PyAudio()
        self._playback_thread = None
        self._stop_event = threading.Event()

        # Load models
        try:
            self.text2semantic = TextToSemanticInference(
                model_path=os.path.join(model_dir, "text2semantic.pth"),
                device=device,
            )

            self.vqgan = VQGANInference(
                model_path=os.path.join(model_dir, "vqgan.pth"),
                device=device,
            )
        except Exception as e:
            log.error("Failed to load Fish Speech models: %s", e)
            log.error("Make sure you've downloaded the models:")
            log.error("  huggingface-cli download fishaudio/fish-speech-1.5 --local-dir models/fish-speech")
            raise

        # Warm up GPU
        log.info("Warming up Fish Speech...")
        self.synthesize("Hello")
        log.info("Fish Speech TTS ready")

    def synthesize(self, text: str) -> bytes:
        """Synthesize text to audio. Returns WAV bytes."""
        log.info("Synthesizing: %s", text[:80])

        with torch.no_grad():
            try:
                # Text to semantic tokens
                tokens = self.text2semantic.generate_tokens(text)

                # Semantic tokens to audio
                audio_tensor = self.vqgan.generate_audio(tokens)

                # Convert to numpy array
                samples = audio_tensor.detach().cpu().numpy()

                # Save to temp WAV and read back as bytes
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name

                sf.write(tmp_path, samples, self.sample_rate)

                with open(tmp_path, 'rb') as f:
                    wav_bytes = f.read()

                os.remove(tmp_path)
                return wav_bytes

            except Exception as e:
                log.error("Fish Speech synthesis failed: %s", e)
                raise RuntimeError(f"Fish Speech error: {e}")

    def _play_wav(self, wav_bytes: bytes):
        """Play WAV bytes through PyAudio."""
        import wave
        import io

        wav_file = io.BytesIO(wav_bytes)
        with wave.open(wav_file, 'rb') as wf:
            stream = self._pa.open(
                format=self._pa.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )

            chunk_size = 4096
            data = wf.readframes(chunk_size)

            while data and not self._stop_event.is_set():
                stream.write(data)
                data = wf.readframes(chunk_size)

            stream.stop_stream()
            stream.close()

    def speak(self, text: str, blocking: bool = False):
        """Synthesize and play text. Non-blocking by default."""
        wav_bytes = self.synthesize(text)

        self._stop_event.clear()
        if blocking:
            self._play_wav(wav_bytes)
        else:
            self._playback_thread = threading.Thread(
                target=self._play_wav, args=(wav_bytes,), daemon=True
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
