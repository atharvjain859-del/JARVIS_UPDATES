import speech_recognition as sr


def listen(timeout=5, phrase_time_limit=8):
    """Listen through the default Windows microphone and return recognized text."""
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 0.7
    recognizer.non_speaking_duration = 0.35
    recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            print("🎙 Listening...")
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
            text = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            print("JARVIS: I didn't catch that.")
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
