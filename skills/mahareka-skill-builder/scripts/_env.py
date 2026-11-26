"""
Where this machine keeps things, for the skill builder's tools. Hermes only: nothing here is a
Claude path. Standard library only.
  KNOWLEDGE   the live layer Zaim replaces himself (SKILL_REGISTRY.xlsx, MAHAREKA_STANDARD.md):
              $MAHAREKA_KNOWLEDGE, else ~/mahareka-knowledge, else
              ~/mahareka-shared/Work/mahareka-knowledge (on the laptop: Mahareka-Shared\\Work\\...).
              Never an archive or download copy. Never copied, moved or written by a tool.
  SKILLS      the folder this machine recorded at its first install (~/.mahareka/skills-dir),
              else the `skills` folder this skill sits in.
"""
import os
from pathlib import Path

__version__ = "2.2"
HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
REGISTRY, STAGED, STANDARD = "SKILL_REGISTRY.xlsx", "SKILL_REGISTRY.staged.xlsx", "MAHAREKA_STANDARD.md"
SKIP_PARTS = {"assets", "_templates", "__pycache__", "node_modules"}

def knowledge():
    """(folder or None, how it was found)"""
    env = os.environ.get("MAHAREKA_KNOWLEDGE")
    if env:
        return Path(env).expanduser(), "$MAHAREKA_KNOWLEDGE"
    home = Path.home()
    for p, how in ((home / "mahareka-knowledge", "~/mahareka-knowledge"),
                   (home / "mahareka-shared" / "Work" / "mahareka-knowledge", "shared folder"),
                   (home / "Mahareka-Shared" / "Work" / "mahareka-knowledge", "shared folder")):
        if (p / REGISTRY).is_file() or (p / STANDARD).is_file():
            return p, how
    return None, "not found"

def skills_dir(arg=None):
    """(folder or None, how it was found)"""
    if arg:
        return Path(arg).expanduser(), "given"
    rec = Path.home() / ".mahareka" / "skills-dir"
    if rec.is_file():
        d = rec.read_text(encoding="utf-8").strip()
        if d and Path(d).is_dir():
            return Path(d), "recorded at install"
    for p in SKILL.parents:
        if p.name == "skills":
            return p, "this skill's own skills folder"
    return None, "not found"

def find_skills(root):
    """Every skill folder below root: a folder holding SKILL.md, outside templates and hidden folders."""
    out = []
    for f in sorted(Path(root).rglob("SKILL.md")):
        rel = f.relative_to(root).parts[:-1]
        if SKIP_PARTS & set(rel) or any(p.startswith(".") for p in rel):
            continue
        out.append(f.parent)
    return out
