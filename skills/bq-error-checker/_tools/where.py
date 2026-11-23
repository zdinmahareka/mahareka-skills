#!/usr/bin/env python3
"""
Where this machine keeps things. Hermes only: nothing here is a Claude path. Standard library
only, so any Python runs it.
  PY         the Python for every other command (needs openpyxl): $MAHAREKA_PYTHON, else the one
             install-hermes.sh recorded in ~/.mahareka/python, else this Python if it has openpyxl
  KNOWLEDGE  $MAHAREKA_KNOWLEDGE; else ~/mahareka-knowledge if it holds qs_boot.py; else the
             folder of qs_boot.py in an installed skill next to this one (mahareka-qs-agent keeps
             it in its scripts/); else the first qs_boot.py found under home. Never copied or moved.
  Rate_History  newest Rate_History*.xlsx in KNOWLEDGE, else the newest one under home
  RUNS       $MAHAREKA_RUNS, else ~/mahareka-runs (one folder per audit, made by new_run.py)
Usage: python where.py          prints the paths and how each was found
       python where.py --json   the same as JSON
"""
import fnmatch, importlib.util, json, os, subprocess, sys
from pathlib import Path

SKIP = {"mc-backups", "mahareka-runs", "node_modules", "AppData", "Library", "__pycache__",
        "venv", ".venv", "venvs", "site-packages", "qs_outputs", "cache", "scratch", "temp", "Temp"}
MAX_DEPTH = 9
SKILL = Path(__file__).resolve().parent.parent
PY_FILE = Path.home() / ".mahareka" / "python"

def search(pattern, root=None, max_depth=MAX_DEPTH):
    """Files under root (home) matching pattern, newest first; skips hidden folders (except
    .hermes), backups, runs, virtualenvs, caches and temp folders (test leftovers live there)."""
    root = Path(root or Path.home())
    hits, base = [], len(root.parts)
    for d, dirs, files in os.walk(root):
        depth = len(Path(d).parts) - base
        dirs[:] = [x for x in dirs if depth < max_depth and x not in SKIP and not x.startswith("tmp")
                   and (not x.startswith(".") or x == ".hermes")]
        hits += [Path(d) / f for f in files if fnmatch.fnmatch(f, pattern)]
    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)

def skills_root():
    for p in SKILL.parents:
        if p.name == "skills": return p
    return None

def has_openpyxl(py):
    try:
        return subprocess.run([py, "-c", "import openpyxl"], capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False

def python():
    """(interpreter, how)"""
    env = os.environ.get("MAHAREKA_PYTHON")
    if env: return os.path.expanduser(env), "env"
    if PY_FILE.is_file():
        rec = PY_FILE.read_text(encoding="utf-8").strip()
        if rec: return rec, "recorded by install"
    if importlib.util.find_spec("openpyxl"): return sys.executable, "this python"
    return None, None

def knowledge():
    """(folder, how)"""
    env = os.environ.get("MAHAREKA_KNOWLEDGE")
    if env: return Path(env).expanduser(), "env"
    default = Path.home() / "mahareka-knowledge"
    if (default / "qs_boot.py").is_file(): return default, "default"
    root = skills_root()
    if root:
        found = [p for p in search("qs_boot.py", root, 5) if SKILL not in p.parents]
        if found: return found[0].parent, "skill " + found[0].parent.parent.name
    found = search("qs_boot.py")
    return (found[0].parent, "search") if found else (default, "default")

def runs():
    return Path(os.environ.get("MAHAREKA_RUNS") or Path.home() / "mahareka-runs").expanduser()

def rate_history(k):
    near = sorted(k.glob("Rate_History*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True) if k.is_dir() else []
    if near: return near[0], "knowledge"
    found = search("Rate_History*.xlsx")
    return (found[0], "search") if found else (None, None)

def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(errors="replace")  # Windows consoles
    py, py_how = python()
    k, how = knowledge(); qs = k / "qs_boot.py"; rh, rh_how = rate_history(k)
    info = {"python": py, "python_found_by": py_how,
            "knowledge": str(k), "knowledge_found_by": how, "qs_boot": str(qs) if qs.is_file() else None,
            "rate_history": str(rh) if rh else None, "rate_history_found_by": rh_how, "runs": str(runs())}
    if "--json" in sys.argv: print(json.dumps(info, indent=1)); return
    print(f"PY            {(py + '  (' + py_how + ')') if py else 'MISSING: no Python with openpyxl (rerun install-hermes.sh)'}")
    print(f"KNOWLEDGE     {k}  ({how}{'' if k.is_dir() else ', missing'})")
    print(f"qs_boot.py    {info['qs_boot'] or 'MISSING'}")
    print(f"Rate_History  {(str(rh) + '  (' + rh_how + ')') if rh else 'absent (Layer F skipped)'}")
    print(f"RUNS          {info['runs']}")

if __name__ == "__main__":
    main()
