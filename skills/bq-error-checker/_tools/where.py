#!/usr/bin/env python3
"""
Where this machine keeps things. Hermes only: nothing here is a Claude path.
  KNOWLEDGE  $MAHAREKA_KNOWLEDGE, else ~/mahareka-knowledge  (QS_RATEBASE, qs_boot.py, Rate_History.xlsx)
  RUNS       $MAHAREKA_RUNS, else ~/mahareka-runs            (one folder per audit, made by new_run.py)
Usage: python3 where.py          prints the paths and what was found
       python3 where.py --json   the same as JSON
"""
import json, os, sys
from pathlib import Path

def knowledge():
    return Path(os.environ.get("MAHAREKA_KNOWLEDGE") or Path.home() / "mahareka-knowledge").expanduser()

def runs():
    return Path(os.environ.get("MAHAREKA_RUNS") or Path.home() / "mahareka-runs").expanduser()

def rate_history(k=None):
    k = k or knowledge()
    hits = sorted(k.glob("Rate_History*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True) if k.is_dir() else []
    return hits[0] if hits else None

def main():
    k = knowledge(); qs = k / "qs_boot.py"; rh = rate_history(k)
    info = {"knowledge": str(k), "knowledge_exists": k.is_dir(), "qs_boot": str(qs) if qs.is_file() else None,
            "rate_history": str(rh) if rh else None, "runs": str(runs())}
    if "--json" in sys.argv: print(json.dumps(info, indent=1)); return
    print(f"KNOWLEDGE     {k}{'' if k.is_dir() else '  (missing)'}")
    print(f"qs_boot.py    {info['qs_boot'] or 'MISSING'}")
    print(f"Rate_History  {info['rate_history'] or 'absent'}")
    print(f"RUNS          {info['runs']}")

if __name__ == "__main__":
    main()
