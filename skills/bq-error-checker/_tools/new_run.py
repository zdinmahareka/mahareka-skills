#!/usr/bin/env python3
"""
Stamp a new run folder (the product) from this skill's _templates/run/ (the factory).
Usage: python new_run.py --project N050 --input BQ.xlsx [--input quote.pdf] [--root DIR]
Root: --root, else $MAHAREKA_RUNS, else ~/mahareka-runs.
Makes ROOT/<runs_dir>/<date>_<project>/ with 00_input/ (copies, never edited), one folder per
stage in stages/, and the stamped templates. Prints the run path (RUN).
"""
import argparse, datetime, os, re, shutil, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent

def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(errors="replace")  # Windows consoles
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True); ap.add_argument("--input", action="append", default=[])
    ap.add_argument("--root")
    a = ap.parse_args()
    tpl = SKILL / "_templates" / "run"
    m = re.search(r"^runs_dir:\s*(\S+)", (tpl / "RUN.md").read_text(encoding="utf-8"), re.M)
    runs_dir = m.group(1) if m else SKILL.name + "-runs"
    root = Path(a.root or os.environ.get("MAHAREKA_RUNS") or Path.home() / "mahareka-runs").expanduser()
    date = datetime.date.today().isoformat()
    slug = re.sub(r"[^a-z0-9]+", "-", a.project.lower()).strip("-") or "run"
    run = root / runs_dir / f"{date}_{slug}"
    n = 2
    while run.exists():
        run = root / runs_dir / f"{date}_{slug}-{n}"; n += 1
    (run / "00_input").mkdir(parents=True)
    for st in sorted(p.name for p in (SKILL / "stages").iterdir() if p.is_dir()):
        (run / st).mkdir()
    names = []
    for f in a.input:
        src = Path(f)
        if not src.is_file(): sys.exit(f"input not found: {f}")
        shutil.copy2(src, run / "00_input" / src.name); names.append(src.name)
    subs = {"{project}": a.project, "{date}": date, "{input}": ", ".join(names)}
    for src in tpl.rglob("*"):
        if src.is_dir(): continue
        dst = run / src.relative_to(tpl); dst.parent.mkdir(parents=True, exist_ok=True)
        text = src.read_text(encoding="utf-8")
        for k, v in subs.items(): text = text.replace(k, v)
        dst.write_text(text, encoding="utf-8")
    print(run)

if __name__ == "__main__":
    main()
