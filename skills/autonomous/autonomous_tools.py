import json
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)
TASK_FILE = DATA / "autonomous_tasks.json"


def _load():
    if not TASK_FILE.exists():
        return []
    try:
        return json.loads(TASK_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    TASK_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")


def add_task(text):
    items = _load()
    item = {"id": int(time.time()), "task": text.strip(), "created": time.strftime("%Y-%m-%d %H:%M:%S"), "done": False}
    items.append(item)
    _save(items)
    return f"Autonomous task queued: {text.strip()}"


def list_tasks():
    items = _load()
    pending = [x for x in items if not x.get("done")]
    if not pending:
        return "No pending autonomous tasks."
    return "\n".join(f"{x['id']}: {x['task']}" for x in pending[-25:])


def complete_task(task_id):
    items = _load()
    for x in items:
        if str(x.get("id")) == str(task_id):
            x["done"] = True
            _save(items)
            return f"Task {task_id} marked complete."
    return f"No task found with id {task_id}."


def clear_completed():
    items = [x for x in _load() if not x.get("done")]
    _save(items)
    return "Completed autonomous tasks cleared."
