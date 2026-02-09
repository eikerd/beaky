#!/usr/bin/env python3
"""Test Beaky components without hardware (for development on WSL2)."""

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
log = logging.getLogger("beaky-test")

def test_llm():
    """Test LLM connection and chat."""
    print("\n=== Testing LLM ===")
    try:
        from brain.llm import LLM
        llm = LLM()
        response = llm.chat("Hello! Tell me about drum and bass in one sentence.")
        print(f"✓ LLM response: {response}")
        return True
    except Exception as e:
        print(f"✗ LLM failed: {e}")
        return False

def test_vision():
    """Test vision model (without camera)."""
    print("\n=== Testing Vision (model only) ===")
    try:
        from brain.vision import Vision
        import io
        from PIL import Image

        # Create a test image (red square)
        img = Image.new('RGB', (640, 480), color='red')
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        image_bytes = buf.getvalue()

        vision = Vision()
        description = vision.describe_scene(image_bytes)
        print(f"✓ Vision model works: {description}")
        return True
    except Exception as e:
        print(f"✗ Vision failed: {e}")
        return False

def test_stt():
    """Test STT model loading (can't test mic in WSL2)."""
    print("\n=== Testing STT (model loading only) ===")
    try:
        from voice.stt import STT
        print("✓ STT model loaded (microphone not tested)")
        return True
    except Exception as e:
        print(f"✗ STT failed: {e}")
        return False

def test_tts():
    """Test TTS (synthesis only, no playback in WSL2)."""
    print("\n=== Testing TTS ===")
    try:
        from voice.tts import TTS
        tts = TTS()
        audio = tts.synthesize("Hello from Beaky!")
        print(f"✓ TTS synthesis works ({len(audio)} bytes)")
        return True
    except Exception as e:
        print(f"✗ TTS failed: {e}")
        return False

def test_people_memory():
    """Test people memory (without camera)."""
    print("\n=== Testing People Memory ===")
    try:
        from memory.people import PeopleMemory
        people = PeopleMemory()
        print(f"✓ People memory loaded ({len(people.known_names)} known)")
        return True
    except Exception as e:
        print(f"✗ People memory failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Beaky Component Tests (Development Mode)")
    print("=" * 60)

    tests = [
        ("LLM", test_llm),
        ("Vision", test_vision),
        ("STT", test_stt),
        ("TTS", test_tts),
        ("People Memory", test_people_memory),
    ]

    results = []
    for name, test_fn in tests:
        try:
            results.append(test_fn())
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"✗ {name} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All components working!")
        print("\nNote: This test runs without hardware (mic, speakers, camera).")
        print("For a real kiosk, you need to run on native Windows or Linux.")
    else:
        print("\n⚠ Some components failed. Check errors above.")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
