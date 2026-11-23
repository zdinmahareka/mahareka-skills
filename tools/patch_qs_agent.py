#!/usr/bin/env python3
"""
Two approved changes to the installed mahareka-qs-agent skill (Zaim, 23 Nov 2026). The skill
itself is not in this repo (it carries the ratebase), so the change is applied in place:
  1. `platforms` gains `windows`, so the QS agent is usable on the laptop.
  2. Rule R-MASTER: the master ratebase is on MatDuo; elsewhere it is a read-only copy and new
     rates are staged, never published.
Safe to run again (it changes nothing the second time). The old SKILL.md is backed up to
~/mc-backups/skills/ first. Touches SKILL.md only: never the ratebase or the engines.
Usage: python patch_qs_agent.py <hermes skills dir>
"""
import datetime, os, re, sys
from pathlib import Path

MARK = "<!-- mahareka:ratebase-master-rule v1 (added by mahareka-skills; keep) -->"
RULE = MARK + """
## Ratebase master and copies (R-MASTER)

The master QS_RATEBASE is the one on MatDuo (the Linux VPS). Every other machine holds a
read-only copy.

- **On MatDuo:** nothing changes. Publish and install ratebase updates exactly as this skill
  already says.
- **On any other machine** (for example Mattigo, the Windows laptop): never save, publish or
  overwrite the ratebase or its published outputs. A new rate or rule learned there is
  **staged**: end the answer with `Staged for master:` and list each item (trade, item, UOM,
  rate, source, date). Zaim approves it and MatDuo adds it to the master.
- If this machine's ratebase version differs from the master's (Mission Control → Virtual Office
  shows both), say so before quoting a rate from the copy.
"""

def add_windows(text):
    """Add windows to `platforms` inside the frontmatter. Returns (text, changed)."""
    m = re.match(r"(---\r?\n)(.*?)(\r?\n---)", text, re.S)
    if not m: return text, False
    fm, nl = m.group(2), "\r\n" if "\r\n" in m.group(2) else "\n"
    lines = fm.split(nl)
    for i, line in enumerate(lines):
        k = re.match(r"^(\s*)platforms:\s*(.*)$", line)
        if not k: continue
        indent, val = k.group(1), k.group(2).strip()
        if val.startswith("["):                                   # platforms: [macos, linux]
            items = [x.strip().strip("'\"") for x in val.strip("[]").split(",") if x.strip()]
            if "windows" in items or "all" in items: return text, False
            lines[i] = f"{indent}platforms: [{', '.join(items + ['windows'])}]"
        elif val:                                                 # platforms: macos, linux
            items = [x.strip() for x in val.split(",") if x.strip()]
            if "windows" in items or "all" in items: return text, False
            lines[i] = f"{indent}platforms: {', '.join(items + ['windows'])}"
        else:                                                     # block list: "  - macos"
            j, items, item_indent = i + 1, [], None
            while j < len(lines) and re.match(r"^\s*-\s+", lines[j]):
                item_indent = item_indent or re.match(r"^(\s*)-", lines[j]).group(1)
                items.append(lines[j].split("-", 1)[1].strip().strip("'\"")); j += 1
            if not items or "windows" in items or "all" in items: return text, False
            lines.insert(j, f"{item_indent}- windows")
        return text[:m.start(2)] + nl.join(lines) + text[m.end(2):], True
    return text, False

def patch(text):
    """Returns (new text, [what changed])."""
    done = []
    text, ch = add_windows(text)
    if ch: done.append("platforms: added windows")
    if MARK not in text:
        nl = "\r\n" if "\r\n" in text else "\n"
        text = text.rstrip("\r\n") + nl + nl + RULE.replace("\n", nl)
        done.append("rule R-MASTER added")
    return text, done

def find_skill(root):
    root = Path(root); base = len(root.parts)
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if len(Path(d).parts) - base < 4 and not x.startswith(".")]
        if Path(d).name == "mahareka-qs-agent" and "SKILL.md" in files: return Path(d) / "SKILL.md"
    return None

def main():
    if len(sys.argv) != 2: sys.exit(__doc__)
    f = find_skill(sys.argv[1])
    if not f: print("[qs-agent] not installed here; nothing to change"); return
    old = f.read_bytes().decode("utf-8")
    new, done = patch(old)
    if not done: print("[qs-agent] already has windows and rule R-MASTER; nothing to change"); return
    if not os.access(f, os.W_OK): print(f"[qs-agent] SKILL.md is read-only; not changed ({', '.join(done)} still to do)"); return
    bk = Path.home() / "mc-backups" / "skills"; bk.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    (bk / f"mahareka-qs-agent-SKILL-{stamp}.md").write_bytes(old.encode("utf-8"))
    tmp = f.with_suffix(".md.tmp"); tmp.write_bytes(new.encode("utf-8")); os.replace(tmp, f)
    print(f"[qs-agent] {', '.join(done)} (old SKILL.md in {bk})")

if __name__ == "__main__":
    main()
