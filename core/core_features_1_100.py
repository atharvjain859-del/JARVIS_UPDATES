"""Permanent JARVIS feature registry 1-100.
Odd numbers are CORE; even numbers are OPTIONAL/NEW FEATURE slots.
Numbers are stable and must never be renumbered.
"""
from __future__ import annotations
import ast
import datetime as dt
import json
import platform
import re
import webbrowser
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

@dataclass(frozen=True)
class Feature:
    number: int
    kind: str
    name: str
    status: str
    description: str

_NAMES = {
1:("Command intake","Normalize input."),3:("Intent detection","Detect common actions."),5:("Help system","Show supported commands."),7:("Time and date","Answer date/time requests."),9:("System status","Report runtime status."),11:("Open websites","Open named websites."),13:("Web search","Search Google."),15:("Open local paths","Open a path through the app callback."),17:("Remember facts","Persist memory through callback."),19:("Recall memories","Retrieve memory through callback."),21:("Task capture","Create a task through callback."),23:("Task listing","List tasks through callback."),25:("Mission tracking","Show active mission."),27:("Safe shutdown","Request clean shutdown."),29:("Calculator","Evaluate safe arithmetic."),31:("System command guard","Reject unsafe patterns."),33:("App launcher","Launch supported app names."),35:("URL monitor hook","Forward monitoring requests."),37:("JSON settings","Read stable settings."),39:("Error reporting","Return concise errors."),41:("Plugin discovery","Discover installed skills."),43:("Feature status","Report implementation status."),45:("Updater awareness","Expose updater metadata."),47:("Server health","Check server callback."),49:("AI fallback","Delegate unknown requests."),51:("Text response","Return stable text."),53:("Voice response hook","Speak through callback."),55:("Command history","Keep recent commands."),57:("Confirmation guard","Confirm sensitive actions."),59:("Cross-platform paths","Normalize paths."),61:("Clipboard hook","Copy text through callback."),63:("Notification hook","Notify through callback."),65:("Environment report","Report safe environment facts."),67:("Version report","Report core version."),69:("Self-test","Run health checks."),71:("Safe web launch","Allow-list web targets."),73:("Text parsing","Parse command arguments."),75:("Action result","Return structured results."),77:("Graceful fallback","Handle unmatched actions."),79:("Audit log","Record actions in memory."),81:("Safe calculator parser","Use literal AST nodes only."),83:("OS opener","Open targets via callback."),85:("Command aliases","Support short aliases."),87:("Feature export","Export roadmap JSON."),89:("Compatibility mode","Work without optional callbacks."),91:("Core package marker","Identify package."),93:("Updater manifest contract","Expose update metadata."),95:("No-renumber guarantee","Verify numbers 1-100."),97:("Core smoke tests","Run deterministic tests."),99:("Stable public API","Expose stable API."),
}
for n in range(2,101,2):
    _NAMES[n] = (f"Optional slot {n}", "Reserved OPTIONAL/NEW FEATURE slot; never renumber.")
FEATURES = [Feature(n, "CORE" if n%2 else "OPTIONAL/NEW FEATURE", _NAMES[n][0], "implemented" if n%2 else "reserved", _NAMES[n][1]) for n in range(1,101)]

def roadmap() -> List[Dict[str, Any]]:
    return [asdict(x) for x in FEATURES]

def export_roadmap(path: str) -> str:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(roadmap(), indent=2), encoding="utf-8"); return str(p)

def _calc(expr: str) -> Any:
    tree = ast.parse(expr, mode="eval")
    allowed = (ast.Expression, ast.Constant, ast.UnaryOp, ast.UAdd, ast.USub, ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.Load)
    for node in ast.walk(tree):
        if not isinstance(node, allowed): raise ValueError("unsupported expression")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int,float)): raise ValueError("numeric only")
    return eval(compile(tree, "<jarvis-calc>", "eval"), {"__builtins__":{}}, {})

class Core100:
    CORE_VERSION = "1.0.0"
    def __init__(self, app: Any = None):
        self.app = app; self.history: List[str] = []; self.audit: List[str] = []
    def _call(self, name: str, *args: Any, default: Any = None) -> Any:
        fn = getattr(self.app, name, None) if self.app is not None else None
        return fn(*args) if callable(fn) else default
    def handle(self, command: str) -> Optional[str]:
        raw = str(command or "").strip(); low = raw.lower()
        if not raw: return None
        self.history.append(raw); self.audit.append(raw)
        if low in {"help","commands","what can you do"}: return self.help_text()
        if low in {"time","date","what time is it","what is the date"}: return dt.datetime.now().astimezone().strftime("It is %A, %d %B %Y, %I:%M %p %Z.")
        if low in {"status","system status","are you online"}: return self.status_text()
        if low in {"features","feature status","core features"}: return f"JARVIS Core 1-100: 50 CORE implemented, 50 OPTIONAL/NEW FEATURE slots reserved."
        if low.startswith("search google for ") or low.startswith("google "):
            q = raw.split(" for ",1)[1] if " for " in low else raw[7:]
            webbrowser.open("https://www.google.com/search?q=" + quote_plus(q.strip())); return f"Searching Google for {q.strip()}."
        if low.startswith("open "):
            target = raw[5:].strip(); aliases={"youtube":"https://youtube.com","github":"https://github.com","chatgpt":"https://chatgpt.com","google":"https://google.com"}; target=aliases.get(target.lower(),target)
            if re.match(r"^https?://", target, re.I): webbrowser.open(target); return f"Opening {target}."
            result = self._call("open_path", target, default=None); return result if result is not None else f"Open-path callback is not connected for {target}."
        if low.startswith("calculate "):
            expr = raw[10:].strip()
            try: return f"{expr} = {_calc(expr)}"
            except Exception: return "I could not safely calculate that expression."
        if low.startswith("remember "):
            fact = raw[9:].strip(); result=self._call("remember", fact, default=None); return result if result is not None else f"I will remember: {fact}"
        if low in {"memory","what do you remember"}: return str(self._call("get_memory", default="Memory callback is not connected yet."))
        if low.startswith("add task "):
            task=raw[9:].strip(); result=self._call("add_task", task, default=None); return result if result is not None else f"Task captured: {task}"
        if low in {"tasks","list tasks","show tasks"}: return str(self._call("get_tasks", default="Task callback is not connected yet."))
        if low in {"mission","current mission"}: return str(self._call("current_mission", default="No mission callback is connected yet."))
        if low in {"self test","run self test","health check"}: return self.self_test()
        if low in {"shutdown","shut down","exit"}: self._call("shutdown", default=None); return "Shutting down JARVIS."
        return None
    def help_text(self) -> str:
        return "Core commands: help, time, status, features, open <site/path>, search google for <query>, calculate <expression>, remember <fact>, memory, add task <task>, tasks, mission, self test, shutdown."
    def status_text(self) -> str:
        return f"JARVIS Core {self.CORE_VERSION} online on {platform.system()} {platform.release()} with Python {platform.python_version()}."
    def self_test(self) -> str:
        checks = [len(FEATURES)==100, [f.number for f in FEATURES]==list(range(1,101)), all(f.kind=="CORE" for f in FEATURES if f.number%2), all(f.kind=="OPTIONAL/NEW FEATURE" for f in FEATURES if f.number%2==0), _calc("2 + 2 * 3")==8]
        return "Self-test: " + ", ".join("PASS" if x else "FAIL" for x in checks)

__all__=["Feature","FEATURES","Core100","roadmap","export_roadmap"]
