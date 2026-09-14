try:
    import pyttsx3
    _engine = pyttsx3.init()
    _engine.setProperty("rate", 178)
    _engine.setProperty("volume", 1.0)
    AVAILABLE = True
except Exception:
    _engine = None
    AVAILABLE = False


def speak(text):
    """Speak text using the installed Windows TTS voice."""
    if not AVAILABLE or not text:
        return
    try:
        _engine.say(str(text)[:1500])
        _engine.runAndWait()
    except Exception:
        pass
