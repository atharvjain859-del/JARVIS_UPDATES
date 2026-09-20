"""Safe intent policy helpers for JARVIS action routing.

This module is deliberately side-effect free. It classifies text and identifies
commands that should require explicit confirmation before execution.
"""

from __future__ import annotations

import re


_CONFIRM_PATTERNS = (
    r"\b(shutdown|restart|reboot|power off)\b",
    r"\b(delete|remove|erase|wipe|format)\b",
    r"\b(send|post|publish|message|email)\b",
    r"\b(install|uninstall|upgrade|downgrade)\b",
)


def normalize_command(text: str) -> str:
    """Return compact, case-folded text suitable for routing."""
    return re.sub(r"\s+", " ", str(text or "").strip().casefold())


def requires_confirmation(text: str) -> bool:
    """Return True for actions that can cause external or destructive effects."""
    command = normalize_command(text)
    return any(re.search(pattern, command) for pattern in _CONFIRM_PATTERNS)


def classify_intent(text: str) -> str:
    """Return a conservative intent label for the upcoming action layer."""
    command = normalize_command(text)
    if not command:
        return "empty"
    if requires_confirmation(command):
        return "confirm_required"
    if command.startswith(("open ", "launch ")):
        return "open"
    if command.startswith(("search ", "google ", "look up ")):
        return "search"
    if command.startswith(("remember ", "save ")):
        return "memory"
    return "chat_or_local_command"
