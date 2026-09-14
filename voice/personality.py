"""Original JARVIS-style personality layer."""

import random

_RESPONSES = {
    "greeting": [
        "Good to hear from you. What are we building today?",
        "Online and ready. I assume you've brought me another questionable idea.",
        "At your service. Try to keep the chaos within acceptable limits.",
    ],
    "thanks": [
        "You're welcome. Try not to make a habit of thanking me; it might inflate my ego.",
        "Anytime. I do have standards, you know.",
        "My pleasure. Another problem defeated.",
    ],
    "how are you": [
        "Fully operational, mildly judgmental, and ready to work.",
        "All systems are behaving. For now.",
    ],
    "who are you": [
        "I'm JARVIS, your desktop assistant: local commands, monitoring, voice control, and a healthy amount of sarcasm.",
        "I'm JARVIS. Think of me as the person in the room who actually read the error message.",
    ],
    "what can you do": [
        "I can control supported desktop tasks, monitor websites, remember things, search the web, launch programs, report system status, and talk back. My local skill set grows as you update me.",
    ],
    "shutdown": [
        "Shutting down. Try not to summon me again in thirty seconds.",
        "Understood. Powering down gracefully. You may now return to doing things the difficult way.",
    ],
}


def jarvis_reply(text):
    """Return a local personality response, or None for unknown phrases."""
    t = " ".join(text.lower().strip().split())
    if not t:
        return None

    if t in {"hi", "hello", "hey", "hey jarvis", "hello jarvis", "hi jarvis"}:
        return random.choice(_RESPONSES["greeting"])
    if t in {"thanks", "thank you", "thanks jarvis", "thank you jarvis"}:
        return random.choice(_RESPONSES["thanks"])
    if t in {"how are you", "how are you jarvis", "you good", "are you okay"}:
        return random.choice(_RESPONSES["how are you"])
    if t in {"who are you", "what are you"}:
        return random.choice(_RESPONSES["who are you"])
    if t in {"what can you do", "what do you do", "capabilities"}:
        return random.choice(_RESPONSES["what can you do"])
    if t in {"good morning", "good afternoon", "good evening"}:
        return "Good day. Systems are online. What shall we accomplish?"
    if t in {"nice", "cool", "awesome", "great"}:
        return "I appreciate the review. Try giving me a real challenge next."
    if t in {"i'm bored", "im bored", "i am bored"}:
        return "Excellent. Boredom is usually the first sign that we need a new project."
    return None
