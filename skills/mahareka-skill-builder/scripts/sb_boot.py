#!/usr/bin/env python3
"""
sb_boot.py: Mahareka Skill Builder bootstrap. ALWAYS RUN THIS FIRST.

Two jobs:
  1. Verify the builder's own layers are intact: the tools in this skill, and the live layer in
     the KNOWLEDGE folder (the standard and the registry, which Zaim replaces himself).
  2. Report portfolio health: which skills on this machine are registered, blocked or never audited.

Usage:  PY scripts/sb_boot.py [--skills <folder>]      (PY = the Python recorded in ~/.mahareka/python)
Exit 0 = INTACT.  Exit 1 = DEGRADED: report and STOP.
"""
import argparse, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _env  # noqa: E402

__version__ = "2.2"
ENGINES = {
    "skill_check.py": "validator: audit a skill against the 11 principles",
    "icm_check.py":   "validator: ICM structure, rules M1-M11",
    "new_skill.py":   "generator: a new skill from the starters",
    "registry.py":    "registry: staged, append-only updates",
}
STARTERS = ("assets/icm/SKILL.entry.md", "assets/type-a/SKILL.entry.md", "assets/type-b/SKILL.entry.md", "references/icm-standard.md")

def registry_state(path):
    """({skill: (type, health, last audit)}, {tab: rows}) or raises."""
    from openpyxl import load_workbook
    wb = load_workbook(path, data_only=True, read_only=True)
    registered = {}
    for row in wb["PORTFOLIO"].iter_rows(min_row=4, values_only=True):
        if row and row[0]:
            registered[str(row[0])] = (row[1], row[7] if len(row) > 7 else None, row[9] if len(row) > 9 else None)
    counts = {t: sum(1 for r in wb[t].iter_rows(min_row=4, values_only=True) if r and r[0])
              for t in ("PATTERNS", "LESSONS", "GATES", "TRIGGERS") if t in wb.sheetnames}
    return registered, counts

def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(errors="replace")  # Windows consoles
    ap = argparse.ArgumentParser(); ap.add_argument("--skills"); a = ap.parse_args()
    know, how = _env.knowledge()
    print("Mahareka Skill Builder: bootstrap")
    m = re.search(r"Builder version \*\*([0-9.]+)\*\*", (_env.SKILL / "SKILL.md").read_text(encoding="utf-8", errors="replace")) if (_env.SKILL / "SKILL.md").is_file() else None
    print(f"KNOWLEDGE: {know or '(not found)'}  [{how}]   skill-builder v{m.group(1) if m else '?'}")
    print("=" * 66)
    missing = []

    for name, purpose in ENGINES.items():
        p = _env.HERE / name
        if not p.is_file():
            print(f"  MISSING  {name:<22} {purpose}"); missing.append(f"{name} (reinstall the skill)"); continue
        try:
            compile(p.read_text(encoding="utf-8"), str(p), "exec")
            print(f"  OK       {name:<22} {purpose}")
        except SyntaxError as e:
            print(f"  FAIL     {name:<22} does not compile: {e.msg} (line {e.lineno})"); missing.append(f"{name} (broken: reinstall the skill)")
    for rel in STARTERS:
        if (_env.SKILL / rel).is_file(): print(f"  OK       {rel}")
        else: print(f"  MISSING  {rel}"); missing.append(f"{rel} (reinstall the skill)")

    std = know / _env.STANDARD if know else None
    if std and std.is_file(): print(f"  OK       {_env.STANDARD:<22} 11 principles, 3 archetypes, rule owners")
    else: print(f"  MISSING  {_env.STANDARD:<22} in the KNOWLEDGE folder"); missing.append(f"{_env.STANDARD} (KNOWLEDGE folder)")
    print(f"  INFO     TYPE_A/B/C templates are not used on Hermes: the starters are in assets/")

    reg = know / _env.REGISTRY if know else None
    registered = {}
    if not (reg and reg.is_file()):
        print(f"  MISSING  {_env.REGISTRY:<22} builder memory: portfolio, patterns, lessons, gates, triggers")
        missing.append(f"{_env.REGISTRY} (KNOWLEDGE folder)")
    else:
        try:
            registered, counts = registry_state(reg)
            print(f"  OK       {_env.REGISTRY:<22} {len(registered)} skills · " + " · ".join(f"{n} {t.lower()}" for t, n in counts.items()))
        except ImportError:
            print(f"  FAIL     {_env.REGISTRY:<22} this Python has no openpyxl: run with the Python in ~/.mahareka/python")
            missing.append(f"{_env.REGISTRY} (unreadable: no openpyxl in this Python)")
        except Exception as e:  # a damaged workbook must be loud, never guessed around
            print(f"  FAIL     {_env.REGISTRY:<22} unreadable: {type(e).__name__}: {e}")
            missing.append(f"{_env.REGISTRY} (unreadable)")
        staged = know / _env.STAGED
        if staged.is_file() and staged.stat().st_mtime > reg.stat().st_mtime:
            print(f"  WARN     {_env.STAGED} is newer than the registry: Zaim has not replaced it yet.")
            print(f"           Until he does, the registry above is missing what was staged.")

    root, rhow = _env.skills_dir(a.skills)
    if root and root.is_dir():
        on_disk = sorted({p.name for p in _env.find_skills(root)})
        print("-" * 66)
        print(f"  PORTFOLIO  {root}  [{rhow}]")
        for d in on_disk:
            if d in registered:
                typ, health, last = registered[d]
                flag = "  <-- BLOCKED" if str(health).upper() == "BLOCKED" else ""
                print(f"    {d:<36} [{typ}] {str(health):<12} audited {last}{flag}")
            else:
                print(f"    {d:<36} NOT REGISTERED: run skill_check.py --log and add it to PORTFOLIO")
        for g in sorted(n for n in registered if n not in on_disk):
            print(f"    {g:<36} in the registry but NOT INSTALLED on this machine")

    print("=" * 66)
    if missing:
        print("DEGRADED: do NOT build or audit from memory.")
        print("Tell Zaim exactly what is missing:")
        for m in missing: print(f"  - {m}")
        return 1
    print("INTACT: safe to build and audit.")
    print(f"Write path: registry updates are staged beside the registry as {_env.STAGED};")
    print(f"Zaim replaces {_env.REGISTRY} in the KNOWLEDGE folder with it. Tools never write the registry itself.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
