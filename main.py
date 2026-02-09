"""Beaky — AI Art Kiosk entry point.

Thread A (worker): Voice listening → STT → Vision snapshot → LLM → TTS
Thread B (main):   Tkinter display (must run on the main thread)
"""

import logging
import signal
import sys
import threading

from brain.llm import LLM
from brain.vision import Vision
from memory.people import PeopleMemory
from ui.display import Display, MSG_USER, MSG_BEAKY, MSG_BEAKY_STREAM, MSG_BEAKY_DONE, MSG_STATUS, MSG_VOLUME
from voice.stt import STT
from voice.tts import TTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("beaky")

# Global shutdown flag
_shutdown = threading.Event()


def worker_loop(display: Display, llm: LLM, vision: Vision, stt: STT, tts: TTS, people: PeopleMemory):
    """Main conversation loop running in a background thread."""
    log.info("Worker thread started")
    display.post(MSG_STATUS, "Ready — speak to Beaky!")

    while not _shutdown.is_set():
        try:
            # 1. Listen for speech
            display.post(MSG_STATUS, "Listening...")
            text = stt.listen(
                status_callback=lambda msg: display.post(MSG_STATUS, msg),
                volume_callback=lambda level: display.post(MSG_VOLUME, str(level))
            )
            if text is None or _shutdown.is_set():
                continue

            display.post(MSG_USER, text)
            display.post(MSG_STATUS, "Thinking...")

            # 2. Capture a snapshot and describe the scene
            scene = None
            person = None
            try:
                frame = vision.capture_frame_raw()
                scene = vision.describe_scene()
                person = people.recognise(frame)
            except Exception as e:
                log.warning("Vision/people failed: %s", e)

            # 3. Check for "remember me" commands
            lower = text.lower()
            if lower.startswith("my name is ") or lower.startswith("call me "):
                name = text.split(maxsplit=3)[-1].strip().rstrip(".")
                if name:
                    try:
                        frame = vision.capture_frame_raw()
                        if people.remember(name, frame):
                            log.info("Remembered: %s", name)
                            person = name
                    except Exception as e:
                        log.warning("Failed to remember face: %s", e)

            # 4. Stream LLM response
            display.post(MSG_STATUS, "Beaky is speaking...")
            full_response = []
            for token in llm.chat_stream(text, scene=scene, person=person):
                full_response.append(token)
                display.post(MSG_BEAKY_STREAM, token)
            display.post(MSG_BEAKY_DONE)

            # 5. Speak the response
            response_text = "".join(full_response)
            tts.speak(response_text, blocking=True)

        except Exception as e:
            if _shutdown.is_set():
                break
            log.error("Worker error: %s", e, exc_info=True)
            display.post(MSG_STATUS, f"Error: {e}")

    log.info("Worker thread exiting")


def main():
    log.info("Starting Beaky...")

    # Verify audio setup first
    from audio_check import verify_audio_setup
    audio_ok = verify_audio_setup()

    if not audio_ok:
        response = input("\n⚠️  Audio issues detected. Continue anyway? (y/n): ")
        if response.lower() != 'y':
            log.info("Startup cancelled by user")
            return

    # Initialize components
    display = Display()
    llm = LLM()
    vision = Vision()
    stt = STT()
    tts = TTS()
    people = PeopleMemory()

    def shutdown():
        log.info("Shutting down...")
        _shutdown.set()
        tts.shutdown()
        stt.shutdown()
        vision.close_camera()

    # Handle Ctrl+C
    signal.signal(signal.SIGINT, lambda *_: shutdown())

    # Startup greeting
    log.info("Playing startup greeting...")
    tts.speak("Hello! I'm Beaky. Speak to me and I'll respond!", blocking=True)

    # Start the worker thread
    worker = threading.Thread(target=worker_loop, args=(display, llm, vision, stt, tts, people), daemon=True)
    worker.start()

    # Run Tkinter on the main thread (blocks until window is closed)
    display.run(on_close=shutdown)

    # Wait for worker to finish
    _shutdown.set()
    worker.join(timeout=3)
    log.info("Beaky stopped.")


if __name__ == "__main__":
    main()
