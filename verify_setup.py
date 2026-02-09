#!/usr/bin/env python3
"""Verify that all Beaky dependencies are correctly installed."""

import sys
from typing import Tuple


def check_python_version() -> Tuple[bool, str]:
    """Check Python version is 3.9+."""
    if sys.version_info >= (3, 9):
        return True, f"✓ Python {sys.version_info.major}.{sys.version_info.minor}"
    return False, f"✗ Python {sys.version_info.major}.{sys.version_info.minor} (need 3.9+)"


def check_import(module: str, optional: bool = False) -> Tuple[bool, str]:
    """Check if a Python module can be imported."""
    try:
        __import__(module)
        return True, f"✓ {module}"
    except ImportError:
        prefix = "⚠" if optional else "✗"
        suffix = " (optional)" if optional else ""
        return optional, f"{prefix} {module}{suffix}"


def check_ollama() -> Tuple[bool, str]:
    """Check if Ollama is running and models are available."""
    try:
        import ollama
        client = ollama.Client()
        models = client.list()
        model_names = {m["name"] for m in models["models"]}

        llm_ok = any("llama3.1" in m for m in model_names)
        vision_ok = "moondream:latest" in model_names

        if llm_ok and vision_ok:
            return True, "✓ Ollama (llama3.1 + moondream)"
        elif llm_ok:
            return False, "⚠ Ollama (llama3.1 found, moondream missing)"
        elif vision_ok:
            return False, "⚠ Ollama (moondream found, llama3.1 missing)"
        else:
            return False, "⚠ Ollama (models not pulled)"
    except Exception as e:
        return False, f"✗ Ollama ({str(e)[:50]})"


def check_piper() -> Tuple[bool, str]:
    """Check if Piper TTS is available."""
    import shutil
    if shutil.which("piper"):
        return True, "✓ Piper TTS"
    return False, "✗ Piper TTS (not on PATH)"


def check_audio() -> Tuple[bool, str]:
    """Check if PyAudio can access audio devices."""
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        input_devices = sum(1 for i in range(pa.get_device_count())
                           if pa.get_device_info_by_index(i)["maxInputChannels"] > 0)
        output_devices = sum(1 for i in range(pa.get_device_count())
                            if pa.get_device_info_by_index(i)["maxOutputChannels"] > 0)
        pa.terminate()

        if input_devices > 0 and output_devices > 0:
            return True, f"✓ Audio ({input_devices} input, {output_devices} output devices)"
        return False, f"⚠ Audio (input: {input_devices}, output: {output_devices})"
    except Exception as e:
        return False, f"✗ Audio ({str(e)[:50]})"


def check_webcam() -> Tuple[bool, str]:
    """Check if webcam is accessible."""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.release()
            return True, "✓ Webcam"
        return False, "⚠ Webcam (can't open device 0)"
    except Exception as e:
        return False, f"✗ Webcam ({str(e)[:50]})"


def main():
    print("=" * 60)
    print("Beaky Setup Verification")
    print("=" * 60)

    checks = [
        ("Python version", check_python_version),
        ("Core dependencies", lambda: check_import("ollama")),
        ("", lambda: check_import("faster_whisper")),
        ("", lambda: check_import("cv2")),
        ("", lambda: check_import("PIL")),
        ("", lambda: check_import("pyaudio")),
        ("", lambda: check_import("numpy")),
        ("Optional: face recognition", lambda: check_import("face_recognition", optional=True)),
        ("Ollama connection", check_ollama),
        ("Piper TTS", check_piper),
        ("Audio devices", check_audio),
        ("Webcam", check_webcam),
    ]

    results = []
    for label, check_fn in checks:
        ok, msg = check_fn()
        results.append(ok)
        if label:
            print(f"\n{label}:")
        print(f"  {msg}")

    print("\n" + "=" * 60)

    required_ok = all(results[:-3])  # Exclude optional checks
    if required_ok and all(results):
        print("✓ All checks passed! Ready to run Beaky.")
        print("\nRun: python main.py")
        return 0
    elif required_ok:
        print("⚠ Required checks passed. Some optional features may not work.")
        print("\nRun: python main.py")
        return 0
    else:
        print("✗ Some required checks failed. Fix the issues above before running.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
