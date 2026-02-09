"""Audio device verification and testing."""

import logging

import numpy as np
import pyaudio

log = logging.getLogger(__name__)


def list_audio_devices():
    """List all available audio input and output devices."""
    pa = pyaudio.PyAudio()

    print("\n" + "="*60)
    print("AUDIO DEVICES")
    print("="*60)

    default_input = pa.get_default_input_device_info()
    default_output = pa.get_default_output_device_info()

    print("\n📥 INPUT DEVICES (Microphones):")
    print("-" * 60)
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            is_default = " [DEFAULT]" if i == default_input['index'] else ""
            print(f"  [{i}] {info['name']}{is_default}")
            print(f"      Channels: {info['maxInputChannels']}, Sample Rate: {int(info['defaultSampleRate'])} Hz")

    print("\n📤 OUTPUT DEVICES (Speakers):")
    print("-" * 60)
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info['maxOutputChannels'] > 0:
            is_default = " [DEFAULT]" if i == default_output['index'] else ""
            print(f"  [{i}] {info['name']}{is_default}")
            print(f"      Channels: {info['maxOutputChannels']}, Sample Rate: {int(info['defaultSampleRate'])} Hz")

    print("\n" + "="*60)
    print(f"✓ Default Input:  {default_input['name']}")
    print(f"✓ Default Output: {default_output['name']}")
    print("="*60 + "\n")

    pa.terminate()
    return default_input, default_output


def test_audio_output(duration=0.5, frequency=440):
    """Play a test tone to verify audio output is working."""
    print("🔊 Testing audio output (you should hear a beep)...")

    try:
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            output=True,
        )

        # Generate a simple tone
        samples = int(44100 * duration)
        t = np.linspace(0, duration, samples, False)
        wave = np.sin(2 * np.pi * frequency * t) * 0.3
        audio_data = (wave * 32767).astype(np.int16).tobytes()

        stream.write(audio_data)
        stream.stop_stream()
        stream.close()
        pa.terminate()

        print("   ✓ Audio output working!\n")
        return True
    except Exception as e:
        print(f"   ✗ Audio output failed: {e}\n")
        return False


def test_audio_input(duration=2.0, threshold=0.01):
    """Test if microphone is picking up sound."""
    print("🎤 Testing audio input (speak into your microphone)...")
    print("   Listening for 2 seconds...")

    try:
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024,
        )

        frames = int(16000 * duration / 1024)
        max_level = 0.0
        detected = False

        for _ in range(frames):
            data = stream.read(1024, exception_on_overflow=False)
            # Calculate RMS
            shorts = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.mean(shorts**2)) / 32768.0
            max_level = max(max_level, rms)

            if rms > threshold and not detected:
                print(f"   🎤 Voice detected! (level: {rms:.3f})")
                detected = True

        stream.stop_stream()
        stream.close()
        pa.terminate()

        if detected:
            print(f"   ✓ Microphone working! (max level: {max_level:.3f})\n")
            return True
        else:
            print(f"   ⚠ No sound detected (max level: {max_level:.3f})")
            if max_level < 0.001:
                print("   → Check if your microphone is muted or not selected\n")
            else:
                print("   → Microphone seems to work but might be too quiet\n")
            return False

    except Exception as e:
        print(f"   ✗ Microphone test failed: {e}\n")
        return False


def verify_audio_setup():
    """Complete audio setup verification."""
    print("\n🔧 Verifying audio setup...")

    # List devices
    default_in, default_out = list_audio_devices()

    # Test output
    output_ok = test_audio_output()

    # Test input
    input_ok = test_audio_input()

    print("="*60)
    if input_ok and output_ok:
        print("✅ Audio setup verified - ready to run Beaky!")
    elif not input_ok and not output_ok:
        print("❌ Both microphone and speakers have issues")
        print("   Check your audio settings in Windows")
    elif not input_ok:
        print("⚠️  Microphone issue detected")
        print("   Beaky won't be able to hear you")
    elif not output_ok:
        print("⚠️  Speaker issue detected")
        print("   You won't hear Beaky's responses")
    print("="*60 + "\n")

    return input_ok and output_ok


if __name__ == "__main__":
    verify_audio_setup()
