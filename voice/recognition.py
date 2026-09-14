import speech_recognition as sr

# Your working BH900 PRO microphone. The index can change on Windows, so
# we prefer the device name and fall back to this index if necessary.
MICROPHONE_NAME = "Microphone (BH900 PRO)"
MICROPHONE_INDEX = 1


def _find_microphone():
    try:
        names = sr.Microphone.list_microphone_names()
        for index, name in enumerate(names):
            if name.strip().lower() == MICROPHONE_NAME.lower():
                return index
        for index, name in enumerate(names):
            if MICROPHONE_NAME.lower() in name.lower():
                return index
    except Exception:
        pass
    return MICROPHONE_INDEX


def listen(timeout=5, phrase_time_limit=8):
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 0.7
    recognizer.non_speaking_duration = 0.35
    recognizer.dynamic_energy_threshold = True
    device_index = _find_microphone()

    try:
        with sr.Microphone(device_index=device_index) as source:
            print(f"🎙 Listening... (microphone {device_index})")
            # Calibrate briefly so normal room noise isn't interpreted as speech.
            recognizer.adjust_for_ambient_noise(source, duration=0.6)
            try:
                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
            except sr.WaitTimeoutError:
                return ""

        print("🧠 Processing...")
        try:
            # en-IN is a better fit for Indian English while still handling
            # ordinary English commands naturally.
            text = recognizer.recognize_google(audio, language="en-IN")
        except sr.UnknownValueError:
            print("JARVIS: I heard the microphone, but could not understand the speech.")
            return ""
        except sr.RequestError as exc:
            print(f"JARVIS: Speech recognition service unavailable: {exc}")
            return ""
        return text.strip()
    except OSError as exc:
        print(f"JARVIS: Microphone unavailable: {exc}")
        return ""
    except Exception as exc:
        print(f"JARVIS: Voice input error: {exc}")
        return ""
