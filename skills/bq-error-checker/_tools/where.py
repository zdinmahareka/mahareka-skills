#!/usr/bin/env python3
"""
Where this machine keeps things. Hermes only: nothing here is a Claude path.
  KNOWLEDGE  $MAHAREKA_KNOWLEDGE if set; else ~/mahareka-knowledge if it holds qs_boot.py;
             else the folder under home that already holds qs_boot.py (found by search,
             nothing is copied or moved)
  Rate_History  newest Rate_History*.xlsx in KNOWLEDGE, else the newest one under home
  RUNS       $MAHAREKA_RUNS, else ~/mahareka-runs (one folder per audit, made by new_run.py)
Usage: python3 where.py          prints the paths and how each was found
       python3 where.py --json   the same as JSON
"""
import fnmatch, json, os, sys
from pathlib import Path

SKIP = {"mc-backups", "mahareka-runs", "node_modules", "AppData", "Library", "__pycache__", "venv", ".venv"}
MAX_DEPTH = 6

def search(pattern, root=None):
    """Files under home matching pattern; skips hidden folders (except .hermes), backups and runs."""
    root = Path(root or Path.home())
    hits, base = [], len(root.parts)
    for d, dirs, files in os.walk(root):
        depth = len(Path(d).parts) - base
        dirs[:] = [x for x in dirs if depth < MAX_DEPTH and x not in SKIP and (not x.startswith(".") or x == ".hermes")]
        hits += [Path(d) / f for f in files if fnmatch.fnmatch(f, pattern)]
    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)

def knowledge():
    """(folder, how) — how is env, default or search."""
    env = os.environ.get("MAHAREKA_KNOWLEDGE")
    if env: return Path(env).expanduser(), "env"
    default = Path.home() / "mahareka-knowledge"
    if (default / "qs_boot.py").is_file(): return default, "default"
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
    k, how = knowledge(); qs = k / "qs_boot.py"; rh, rh_how = rate_history(k)
    info = {"knowledge": str(k), "knowledge_found_by": how, "qs_boot": str(qs) if qs.is_file() else None,
            "rate_history": str(rh) if rh else None, "rate_history_found_by": rh_how, "runs": str(runs())}
    if "--json" in sys.argv: print(json.dumps(info, indent=1)); return
    print(f"KNOWLEDGE     {k}  ({how}{'' if k.is_dir() else ', missing'})")
    print(f"qs_boot.py    {info['qs_boot'] or 'MISSING'}")
    print(f"Rate_History  {(str(rh) + '  (' + rh_how + ')') if rh else 'absent'}")
    print(f"RUNS          {info['runs']}")

if __name__ == "__main__":
    main()
