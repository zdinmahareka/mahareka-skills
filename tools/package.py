#!/usr/bin/env python3
"""Zip each skill for upload to Claude: dist/<name>.zip with the skill folder at the top.
Usage: python3 tools/package.py [name ...]. Refuses a package that fails icm_check.py,
holds a workbook (nested zip) or a second SKILL.md."""
import subprocess, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {"__pycache__", ".DS_Store"}

def main():
    names = sys.argv[1:] or sorted(p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())
    (ROOT / "dist").mkdir(exist_ok=True)
    for name in names:
        skill = ROOT / "skills" / name
        chk = subprocess.run([sys.executable, "-I", str(ROOT / "skills/mahareka-skill-builder/scripts/icm_check.py"), str(skill)],
                             capture_output=True, text=True)
        if chk.returncode: sys.exit(chk.stdout)
        files = [f for f in sorted(skill.rglob("*")) if f.is_file() and not SKIP & set(f.parts)]
        bad = [f for f in files if f.suffix.lower() in (".xlsx", ".xlsm", ".zip")]
        if bad: sys.exit(f"{name}: data/zip files cannot ship in a skill: {[str(b.relative_to(skill)) for b in bad]}")
        out = ROOT / "dist" / f"{name}.zip"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in files: z.write(f, Path(name) / f.relative_to(skill))
        print(f"{out.relative_to(ROOT)}  {len(files)} files  {out.stat().st_size // 1024} KB")

if __name__ == "__main__":
    main()
