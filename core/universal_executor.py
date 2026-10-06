"""
JARVIS Universal Executor
Future-proof Windows application and project launcher.
"""
import json
import os
import re
import subprocess
import shlex
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
PROJECT_FILE = BASE / "data" / "projects.json"

def _normalise(text):
    text = str(text).lower().strip()
    text = re.sub(r"\.(lnk|url|exe)$", "", text)
    text = re.sub(r"[_\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def _load_projects():
    if not PROJECT_FILE.exists():
        return {}
    try:
        data = json.loads(PROJECT_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def extract_target(command):
    text = command.strip()
    patterns = [
        r"^(?:please\s+)?open\s+(?:the\s+)?application\s+(.+)$",
        r"^(?:please\s+)?open\s+(.+)$",
        r"^(?:please\s+)?launch\s+(?:the\s+)?application\s+(.+)$",
        r"^(?:please\s+)?launch\s+(.+)$",
        r"^(?:please\s+)?start\s+(?:the\s+)?application\s+(.+)$",
        r"^(?:please\s+)?start\s+(.+)$",
        r"^(?:please\s+)?run\s+(?:the\s+)?application\s+(.+)$",
        r"^(?:please\s+)?run\s+(.+)$",
        r"^bring\s+up\s+(.+)$",
        r"^get\s+(.+)\s+open$",
    ]
    for pattern in patterns:
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            target = match.group(1).strip()
            target = re.sub(r"\s+(?:please|for me)$", "", target, flags=re.I)
            return target.strip()
    return None

def _start_apps():
    script = "Get-StartApps | Select-Object Name,AppID | ConvertTo-Json -Compress"
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", script],
            capture_output=True, text=True, timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        if isinstance(data, dict):
            data = [data]
        return data if isinstance(data, list) else []
    except Exception:
        return []

def _find_windows_app(target):
    wanted = _normalise(target)
    if not wanted:
        return None
    best = None
    best_score = 0
    for app in _start_apps():
        name = app.get("Name", "")
        app_id = app.get("AppID", "")
        candidate = _normalise(name)
        if not candidate:
            continue
        if candidate == wanted:
            score = 100
        elif candidate.startswith(wanted):
            score = 90
        elif wanted in candidate:
            score = 80
        elif candidate in wanted:
            score = 70
        else:
            common = set(wanted.split()) & set(candidate.split())
            score = 50 + len(common) * 10 if common else 0
        if score > best_score:
            best_score = score
            best = (name, app_id)
    return best if best_score >= 50 else None

def _launch_windows_app(name, app_id):
    try:
        command = "Start-Process 'shell:AppsFolder\\\\" + app_id + "'"
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            capture_output=True, text=True, timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode == 0:
            return True, f"Opening {name}."
    except Exception:
        pass
    return False, f"I couldn't launch {name}."

def _find_registered_project(target):
    wanted = _normalise(target)
    for name, info in _load_projects().items():
        if _normalise(name) == wanted:
            return name, info
    return None

def _launch_project(name, info):
    path = Path(str(info.get("path", ""))).expanduser()
    if not path.exists():
        return False, f"I found {name}, but its configured path does not exist."
    command = info.get("command")
    try:
        if command:
            cwd = path if path.is_dir() else path.parent
            parts = shlex.split(str(command), posix=False)
            if not parts:
                return False, f"No launch command is configured for {name}."
            subprocess.Popen(parts, cwd=str(cwd))
        else:
            os.startfile(str(path))
        return True, f"Launching {name}."
    except Exception as exc:
        return False, f"I couldn't launch {name}: {exc}"

def execute(command):
    target = extract_target(command)
    if not target:
        return False, None
    project = _find_registered_project(target)
    if project:
        success, message = _launch_project(*project)
        return True, message
    app = _find_windows_app(target)
    if app:
        success, message = _launch_windows_app(*app)
        return True, message
    path = Path(target).expanduser()
    if path.exists():
        try:
            os.startfile(str(path))
            return True, f"Opening {target}."
        except Exception as exc:
            return True, f"I couldn't open {target}: {exc}"
    return False, None
