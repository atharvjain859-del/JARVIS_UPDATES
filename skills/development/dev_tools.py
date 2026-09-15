import ast
import json
import subprocess
from pathlib import Path


def scan_python(path):
    p = Path(path).expanduser()
    if not p.exists():
        return f"File not found: {p}"
    if p.suffix.lower() != ".py":
        return "This scanner currently checks Python files."
    try:
        source = p.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(p))
        funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        imports = [n.name for n in ast.walk(tree) if isinstance(n, ast.Import)]
        return json.dumps({"file": str(p), "lines": len(source.splitlines()), "functions": funcs, "classes": classes, "imports": imports}, indent=2)
    except SyntaxError as exc:
        return f"Python syntax error at line {exc.lineno}: {exc.msg}"
    except Exception as exc:
        return f"Scan failed: {exc}"


def syntax_check(path):
    p = Path(path).expanduser()
    if not p.exists():
        return f"File not found: {p}"
    try:
        ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        return f"Syntax check passed: {p.name}"
    except SyntaxError as exc:
        return f"Syntax error in {p.name}, line {exc.lineno}: {exc.msg}"
    except Exception as exc:
        return f"Check failed: {exc}"


def run_python(path, args=""):
    p = Path(path).expanduser()
    if not p.exists():
        return f"File not found: {p}"
    try:
        result = subprocess.run(["python", str(p), *args.split()], capture_output=True, text=True, timeout=30)
        output = (result.stdout + "\n" + result.stderr).strip()
        return f"Exit code {result.returncode}\n{output[-4000:]}"
    except subprocess.TimeoutExpired:
        return "The Python program exceeded the 30-second safety timeout."
    except Exception as exc:
        return f"Run failed: {exc}"


def find_python_files(folder):
    p = Path(folder).expanduser()
    if not p.exists():
        return f"Folder not found: {p}"
    files = list(p.rglob("*.py"))[:100]
    if not files:
        return "No Python files found."
    return "\n".join(str(x) for x in files)
