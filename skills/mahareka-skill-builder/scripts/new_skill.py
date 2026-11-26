#!/usr/bin/env python3
"""
new_skill.py: start a new Mahareka skill from the starters, in the right shape.

  PY scripts/new_skill.py --name mahareka-<domain>-<function> --type A|B|C --purpose "..."
        [--triggers-en "a, b"] [--triggers-bm "x, y"] [--title "..."]
        [--stages intake,work,report]     pipeline stages, in order (Type C; default: intake,work,report)
        [--skills <folder>]               default: the folder recorded in ~/.mahareka/skills-dir
        [--category mahareka]             the folder below the skills folder
        [--register]                      also stage a PORTFOLIO row (registry.py)

Type A -> one file. Type B -> shelves (SKILL.md + _shared/). Type C -> ICM Pipeline (router,
CONTEXT.md, one contract per stage, a run stamp, gates). Every shape gets README.md.
It refuses when a skill with that name already exists, fills name and description, leaves the
rest as <placeholders> to write, and runs icm_check.py on the result.
Exit 0 = created and icm_check passes. Exit 1 = refused, or icm_check found a blocker.
"""
import argparse, re, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _env  # noqa: E402

__version__ = "2.2"
ASSETS = _env.SKILL / "assets"
NAME_RE = re.compile(r"mahareka(-[a-z0-9]+){1,5}")

def description(a):
    d = a.purpose.strip().rstrip(".") + "."
    if a.triggers_en: d += f" Use whenever the user asks: {a.triggers_en.strip()}"
    if a.triggers_bm: d += " — " + ", ".join(f'"{t.strip()}"' for t in a.triggers_bm.split(",") if t.strip()) + "."
    return d.replace("\n", " ")

def entry(src, dst, a):
    """Copy a SKILL.entry.md as SKILL.md with name, description and title filled."""
    text = src.read_text(encoding="utf-8")
    text = re.sub(r"^name: .*$", f"name: {a.name}", text, count=1, flags=re.M)
    text = re.sub(r"^description: .*$", lambda m: f"description: {description(a)}", text, count=1, flags=re.M)
    text = text.replace("<Skill title>", a.title)
    dst.write_text(text, encoding="utf-8")

def readme(dst, a):
    text = (ASSETS / "icm" / "README.md").read_text(encoding="utf-8").replace("<skill-name>", a.name).replace("<x.y>", "1.0")
    text = text.replace("<One or two sentences: what this skill is for, in plain words.>", a.purpose.strip())
    (dst / "README.md").write_text(text, encoding="utf-8")

def pipeline(dst, a):
    stages = [s.strip() for s in a.stages.split(",") if s.strip()]
    if not stages or any(not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", s) for s in stages):
        sys.exit("STOP: --stages takes kebab-case names, e.g. intake,work,report")
    names = [f"{i:02d}_{s}" for i, s in enumerate(stages, 1)]
    icm = ASSETS / "icm"
    entry(icm / "SKILL.entry.md", dst / "SKILL.md", a)
    for d in ("_shared", "_tools", "_templates/run"): (dst / d).mkdir(parents=True)
    (dst / "_shared" / "rules.md").write_text((ASSETS / "type-b" / "_shared" / "rules.md").read_text(encoding="utf-8"), encoding="utf-8")
    for f in ("new_run.py", "gate.py"): shutil.copy2(icm / "_tools" / f, dst / "_tools" / f)
    short = a.name.replace("mahareka-", "", 1)
    (dst / "_templates" / "run" / "RUN.md").write_text((icm / "run" / "RUN.md").read_text(encoding="utf-8").replace("<short-name>", short).replace("<Skill>", a.title), encoding="utf-8")
    # the pipeline on one screen: one row per stage
    root = (icm / "CONTEXT.root.md").read_text(encoding="utf-8").replace("<Skill>", a.title).replace("<N>", str(len(names)))
    row = next(l for l in root.splitlines() if l.startswith("| `stages/01_<verb>/`"))
    rows = "\n".join(f"| `stages/{n}/` | <job> | `{n}/<file>` | {'Zaim reads it' if n in (names[0], names[-1]) else f'`gate.py RUN {n[:2]}`'} |" for n in names)
    (dst / "CONTEXT.md").write_text(root.replace(row, rows), encoding="utf-8")
    # one contract per stage, each pointing at the stage before it
    tpl = (icm / "stage-CONTEXT.md").read_text(encoding="utf-8")
    for i, n in enumerate(names):
        prev = "00_input" if i == 0 else names[i - 1]
        text = tpl.replace("NN_<verb>", n).replace("RUN/<previous stage>/<file>", f"RUN/{prev}/<file>").replace("SKILL/_shared/<rules>.md", "SKILL/_shared/rules.md").replace("gate.py RUN NN", f"gate.py RUN {n[:2]}")
        (dst / "stages" / n).mkdir(parents=True)
        (dst / "stages" / n / "CONTEXT.md").write_text(text, encoding="utf-8")
    # the entry's route table points at the first real stage
    e = dst / "SKILL.md"
    e.write_text(e.read_text(encoding="utf-8").replace("`stages/01_<verb>/`", f"`stages/{names[0]}/`"), encoding="utf-8")

def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(errors="replace")  # Windows consoles
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True); ap.add_argument("--type", required=True, choices=["A", "B", "C"])
    ap.add_argument("--purpose", required=True); ap.add_argument("--triggers-en", dest="triggers_en", default="")
    ap.add_argument("--triggers-bm", dest="triggers_bm", default=""); ap.add_argument("--title", default="")
    ap.add_argument("--stages", default="intake,work,report"); ap.add_argument("--skills"); ap.add_argument("--category", default="mahareka")
    ap.add_argument("--subtype", default=""); ap.add_argument("--register", action="store_true")
    a = ap.parse_args()
    if not NAME_RE.fullmatch(a.name): sys.exit("STOP: the name is mahareka-<domain>-<function>, lower case with hyphens.")
    if len(a.purpose.strip()) < 15: sys.exit("STOP: give the purpose in one clause. A skill without a stated purpose never fires.")
    a.title = a.title or a.name.replace("mahareka-", "", 1).replace("-", " ").title()
    root, how = _env.skills_dir(a.skills)
    if not root or not root.is_dir(): sys.exit("STOP: no skills folder on this machine. Give one with --skills <folder>.")
    taken = [p for p in _env.find_skills(root) if p.name == a.name]
    dst = root / a.category / a.name
    if taken or dst.exists(): sys.exit(f"STOP: {a.name} already exists at {taken[0] if taken else dst}. Nothing was written.")
    dst.mkdir(parents=True)
    if a.type == "A":
        entry(ASSETS / "type-a" / "SKILL.entry.md", dst / "SKILL.md", a)
    elif a.type == "B":
        entry(ASSETS / "type-b" / "SKILL.entry.md", dst / "SKILL.md", a)
        (dst / "_shared").mkdir()
        shutil.copy2(ASSETS / "type-b" / "_shared" / "rules.md", dst / "_shared" / "rules.md")
    else:
        pipeline(dst, a)
    readme(dst, a)
    print(f"created {dst}  [skills folder: {how}]")
    print("Every <placeholder> is still to be written: the body, the README, and for a pipeline each stage contract.")
    p = subprocess.run([sys.executable, str(_env.HERE / "icm_check.py"), str(dst)], capture_output=True, text=True, encoding="utf-8")
    print(p.stdout.rstrip())
    if a.register:
        try:
            import registry
            registry.add_skill(a.name, a.type, a.purpose.strip(), a.subtype)
        except ImportError:
            print("  ! not registered: this Python has no openpyxl. Run registry.py add-skill with the Python in ~/.mahareka/python.")
        except (FileNotFoundError, KeyError) as e:
            print(f"  ! not registered: {e}")
    sys.exit(p.returncode)

if __name__ == "__main__":
    main()
