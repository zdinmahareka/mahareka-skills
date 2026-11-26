#!/usr/bin/env python3
"""
Mahareka ICM Standard checker (references/icm-standard.md, rules M1-M11).
Usage: python icm_check.py <skill folder>        one skill
       python icm_check.py --all <folder>         every skill (folder holding SKILL.md) below it
Prints BLOCKER / WARN / INFO lines. Exit 1 on any blocker. Standard library only.
Complements skill_check.py (the 11 principles); it does not replace it.
"""
import re, sys
from pathlib import Path

__version__ = "2.2"
TOKEN_BUDGET = 8000          # M6, approximated as characters / 4
ENTRY_LINES = 60             # M1, pipeline skills only
PATH_RE = re.compile(r"`(?:SKILL/)?((?:_shared|_templates|_tools|stages|references|assets|scripts)/[^`\s]+)`")
LINK_RE = re.compile(r"\]\(([^)#\s]+)\)")
README_MUST = ("Purpose", "What", "Why", "When", "How")     # M11: a heading starts with each
README_SHOULD = ("Using it", "Maintaining it")

def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n?", text, re.S)
    return (m.group(1), text[m.end():]) if m else ("", text)

def section(text, name):
    m = re.search(rf"^## {name}\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1) if m else None

def readme_findings(skill):
    """M11: the page for people. [(level, message)] for one skill folder."""
    out, readme = [], Path(skill) / "README.md"
    if not readme.is_file():
        return [("BLOCKER", "M11: no README.md (the page for people: Purpose, What, Why, When, How)")]
    heads = [h.strip() for h in re.findall(r"^##\s+(.+?)\s*$", readme.read_text(encoding="utf-8", errors="replace"), re.M)]
    has = lambda name: any(re.match(rf"{re.escape(name)}\b", h, re.I) for h in heads)
    out += [("BLOCKER", f"M11: README.md has no '## {name} ...' section") for name in README_MUST if not has(name)]
    out += [("WARN", f"M11: README.md has no '## {name}' section") for name in README_SHOULD if not has(name)]
    return out

def check(skill):
    out = []
    add = lambda level, msg: out.append((level, msg))
    entry = skill / "SKILL.md"
    if not entry.is_file():
        return [("BLOCKER", "no SKILL.md")]
    fm, body = frontmatter(entry.read_text(encoding="utf-8"))
    if not re.search(r"^name:\s*\S", fm, re.M): add("BLOCKER", "SKILL.md frontmatter has no name")
    if not re.search(r"^description:\s*\S", fm, re.M): add("BLOCKER", "SKILL.md frontmatter has no description")
    out += readme_findings(skill)
    for extra in skill.rglob("SKILL.md"):
        if extra != entry:
            add("BLOCKER", f"M9: second SKILL.md at {extra.relative_to(skill)} (counted as a skill by Hermes and Mission Control; name it SKILL.entry.md)")

    # routing files and contracts: every backticked skill path must resolve; any .md: links resolve
    routing = {entry, skill / "CONTEXT.md", *skill.glob("stages/*/CONTEXT.md")}
    for md in skill.rglob("*.md"):
        rel = md.relative_to(skill)
        if rel.parts[0] in ("_templates", "assets"): continue   # stamps hold placeholders
        text = md.read_text(encoding="utf-8")
        for p in (PATH_RE.findall(text) if md in routing else []):
            p = p.rstrip(".,;:)")
            if any(ch in p for ch in "<>*{}") or p.endswith("/"):
                if p.endswith("/") and not (skill / p).is_dir() and "<" not in p and "*" not in p:
                    add("BLOCKER", f"{rel}: folder `{p}` does not exist")
                continue
            if not (skill / p).exists():
                add("BLOCKER", f"{rel}: path `{p}` does not exist")
        for link in LINK_RE.findall(text):
            if "://" in link or link.startswith("mailto:"): continue
            if not (md.parent / link).exists():
                add("BLOCKER", f"{rel}: link ({link}) does not resolve")

    stages_dir = skill / "stages"
    if not stages_dir.is_dir():
        add("INFO", "no stages/: Type A or B shape; pipeline rules (M1, M3-M6, M8) not applied")
        return out

    # pipeline rules
    n_body = len(body.strip().splitlines())
    if n_body > ENTRY_LINES:
        add("WARN", f"M1: SKILL.md body is {n_body} lines (pipeline entry should be <= {ENTRY_LINES}); move content to a shelf")
    if not (skill / "CONTEXT.md").is_file(): add("BLOCKER", "M2: no root CONTEXT.md (the pipeline on one screen)")
    if not (skill / "_templates" / "run" / "RUN.md").is_file(): add("BLOCKER", "M4: no _templates/run/RUN.md (the run stamp)")
    if not (skill / "_tools" / "new_run.py").is_file(): add("WARN", "M4: no _tools/new_run.py to stamp runs")

    stages = sorted(p for p in stages_dir.iterdir() if p.is_dir())
    for i, st in enumerate(stages, 1):
        m = re.fullmatch(r"(\d\d)_[a-z0-9]+(?:-[a-z0-9]+)*", st.name)
        if not m: add("BLOCKER", f"M9: stage folder '{st.name}' is not NN_kebab-name"); continue
        if int(m.group(1)) != i: add("BLOCKER", f"M9: stage '{st.name}' breaks the numbering (expected {i:02d})")
        c = st / "CONTEXT.md"
        if not c.is_file(): add("BLOCKER", f"M3: {st.name} has no CONTEXT.md"); continue
        text = c.read_text(encoding="utf-8")
        for name in ("Inputs", "Process", "Outputs", "Check"):
            if section(text, name) is None: add("BLOCKER", f"M3: {st.name}/CONTEXT.md has no '## {name}'")
        if len(re.findall(r"^## Check\s*$", text, re.M)) > 1: add("BLOCKER", f"M3: {st.name} has more than one Check")
        if "Do NOT load" not in text: add("WARN", f"M6: {st.name} has no 'Do NOT load:' line")
        inputs = (section(text, "Inputs") or "").split("Do NOT load")[0]
        if inputs and not re.search(r"Working|Reference", inputs):
            add("WARN", f"M3: {st.name} inputs are not split into Working / Reference")
        # budget: contract + the skill files it lists as inputs (run files are unknown in advance)
        chars = len(text)
        for p in set(PATH_RE.findall(inputs)):
            f = skill / p.rstrip(".,;:)")
            if f.is_file(): chars += len(f.read_text(errors="ignore", encoding="utf-8"))
        tokens = chars // 4
        if tokens > TOKEN_BUDGET: add("BLOCKER", f"M6: {st.name} loads ~{tokens} tokens of skill files (> {TOKEN_BUDGET})")
        else: add("INFO", f"{st.name}: ~{tokens} tokens of skill files + this run's inputs")
    if not stages: add("BLOCKER", "stages/ is empty")
    return out

def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(errors="replace")  # Windows consoles
    args = sys.argv[1:]
    if not args: sys.exit(__doc__)
    if args[0] == "--all":
        root = Path(args[1] if len(args) > 1 else ".")
        skills = sorted({p.parent for p in root.rglob("SKILL.md") if not {"_templates", "assets"} & set(p.parts)})
    else:
        skills = [Path(args[0])]
    blockers = 0
    for s in skills:
        res = check(s)
        b = sum(1 for lvl, _ in res if lvl == "BLOCKER")
        blockers += b
        print(f"== {s.name}: {'FAIL' if b else 'PASS'} ({b} blocker{'s' if b != 1 else ''})")
        for lvl, msg in res: print(f"  {lvl:<7} {msg}")
    sys.exit(1 if blockers else 0)

if __name__ == "__main__":
    main()
