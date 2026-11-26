#!/usr/bin/env python3
"""
Stage gates for a run. Writes RUN/<stage>/check.md, first line `pass` or `fail: <why>`.
Usage: python gate.py RUN 01|02|...    check that stage
       python gate.py RUN status       print every stage's verdict (status lives on disk)
Exit 1 on fail. This starter passes a stage when its folder holds at least one output that is
not empty. Replace `check_stage` with what each stage must really prove.
"""
import sys
from pathlib import Path

def stage_dir(run, n):
    hits = sorted(p for p in run.glob(f"{n}_*") if p.is_dir())
    return hits[0] if hits else None

def check_stage(d):
    """None when the stage passes, else why it fails."""
    outputs = [p for p in d.iterdir() if p.is_file() and p.name != "check.md"]
    if not outputs: return "no output in this stage's folder"
    empty = [p.name for p in outputs if p.stat().st_size == 0]
    if empty: return "empty output: " + ", ".join(empty)
    return None

def main():
    if len(sys.argv) != 3: sys.exit(__doc__)
    run, what = Path(sys.argv[1]), sys.argv[2]
    if not run.is_dir(): sys.exit(f"fail: no run folder at {run}")
    if what == "status":
        for d in sorted(p for p in run.iterdir() if p.is_dir() and p.name[:2].isdigit() and p.name != "00_input"):
            c = d / "check.md"
            print(f"{d.name:<24} {c.read_text(encoding='utf-8').splitlines()[0] if c.is_file() and c.read_text(encoding='utf-8').strip() else 'not checked'}")
        return
    d = stage_dir(run, what)
    if not d: sys.exit(f"fail: no stage {what} in {run}")
    why = check_stage(d)
    (d / "check.md").write_text(("pass" if not why else f"fail: {why}") + "\n", encoding="utf-8")
    print(f"{d.name}: {'pass' if not why else 'fail: ' + why}")
    sys.exit(1 if why else 0)

if __name__ == "__main__":
    main()
