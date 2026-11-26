#!/usr/bin/env python3
"""
registry.py: append-only updates to SKILL_REGISTRY.xlsx, staged for Zaim.

The registry lives in the KNOWLEDGE folder and is replaced only by Zaim. This tool never writes
it. It copies it to SKILL_REGISTRY.staged.xlsx beside it (or continues a staged copy that is
already newer), appends there, and prints what Zaim must replace.

  PY scripts/registry.py add-skill --name N --type A|B|C [--subtype S] --purpose "..." [--notes "..."]
  PY scripts/registry.py log-audit --name N --verdict PASS|"NEEDS WORK"|BLOCKED --blockers 0 --warnings 2 --info 1 --summary "..."
  PY scripts/registry.py lesson --name N --what "..." --cause "..." --fix "..." [--principle P3]
Rows are only ever added. A retired skill stays in PORTFOLIO, marked SUPERSEDED by hand.
"""
import argparse, datetime, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _env  # noqa: E402

__version__ = "2.2"
FIRST_DATA_ROW = 4          # row 1 title, row 3 column headings

def staged_copy(know):
    """Open the workbook to append to: the staged copy when it is the newer one, else a fresh copy of the registry."""
    from openpyxl import load_workbook
    reg, staged = know / _env.REGISTRY, know / _env.STAGED
    if not reg.is_file(): raise FileNotFoundError(f"{_env.REGISTRY} is not in the KNOWLEDGE folder ({know})")
    if not (staged.is_file() and staged.stat().st_mtime > reg.stat().st_mtime):
        shutil.copy2(reg, staged)
    return load_workbook(staged), staged

def append(ws, values):
    r = max(ws.max_row + 1, FIRST_DATA_ROW)
    while r > FIRST_DATA_ROW and ws.cell(r - 1, 1).value in (None, ""): r -= 1      # no gap below the last row
    for c, v in enumerate(values, 1): ws.cell(r, c, v)
    return r

def stage(tab, values, know=None):
    know = Path(know) if know else _env.knowledge()[0]
    if not know: raise FileNotFoundError("the KNOWLEDGE folder was not found (set MAHAREKA_KNOWLEDGE)")
    wb, staged = staged_copy(know)
    if tab not in wb.sheetnames: raise KeyError(f"the registry has no {tab} tab")
    row = append(wb[tab], values)
    wb.save(staged)
    print(f"  staged: {tab} row {row} -> {staged}")
    print(f"  ACTION ZAIM: replace {_env.REGISTRY} in the KNOWLEDGE folder with {_env.STAGED}.")
    return staged

def add_skill(name, typ, purpose, subtype="", notes="", know=None):
    layer = {"A": "SKILL.md only", "B": "SKILL.md + _shared/", "C": "ICM pipeline: stages, _shared/, _tools/"}[typ]
    live = "KNOWLEDGE folder" if typ == "C" else "none needed"
    memory = "see KNOWLEDGE folder" if typ == "C" else "none: stateless by design"
    today = datetime.date.today().isoformat()
    return stage("PORTFOLIO", [name, typ, subtype, purpose, layer, live, memory, "NEW", 0, today,
                               notes or f"Built with mahareka-skill-builder v{__version__}. Not yet audited in place."], know)

def log_audit(name, verdict, blockers, warnings, info, summary, know=None):
    return stage("AUDIT_LOG", [datetime.date.today().isoformat(), name, verdict, blockers, warnings, info, summary], know)

def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("add-skill"); s.add_argument("--name", required=True); s.add_argument("--type", required=True, choices=["A", "B", "C"])
    s.add_argument("--subtype", default=""); s.add_argument("--purpose", required=True); s.add_argument("--notes", default="")
    s = sub.add_parser("log-audit"); s.add_argument("--name", required=True); s.add_argument("--verdict", required=True)
    for n in ("blockers", "warnings", "info"): s.add_argument(f"--{n}", type=int, default=0)
    s.add_argument("--summary", default="")
    s = sub.add_parser("lesson"); s.add_argument("--name", required=True); s.add_argument("--what", required=True)
    s.add_argument("--cause", default=""); s.add_argument("--fix", default=""); s.add_argument("--principle", default="")
    a = ap.parse_args()
    try:
        if a.cmd == "add-skill": add_skill(a.name, a.type, a.purpose, a.subtype, a.notes)
        elif a.cmd == "log-audit": log_audit(a.name, a.verdict, a.blockers, a.warnings, a.info, a.summary)
        else: stage("LESSONS", [datetime.date.today().isoformat(), a.name, a.what, a.cause, a.fix, a.principle])
    except ImportError:
        sys.exit("STOP: this Python has no openpyxl. Run with the Python in ~/.mahareka/python.")
    except (FileNotFoundError, KeyError) as e:
        sys.exit(f"STOP: {e}")

if __name__ == "__main__":
    main()
