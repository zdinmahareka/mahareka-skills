#!/usr/bin/env python3
"""
The approved changes to the installed mahareka-qs-agent skill. The skill itself is not in this
repo (it carries the ratebase), so the change is applied in place, to SKILL.md only.

Zaim, 24 Nov 2026 (replaces the 23 Nov version): one ratebase, on MatDuo, and no copy elsewhere.
  1. `platforms` loses `windows`, so Hermes hides the QS agent on the laptop (its engines use
     MatDuo's paths and do not run there). The other platforms stay as they are.
  2. Rule R-MASTER v2: one ratebase, on MatDuo; on any other machine nothing is priced, the
     question is asked of MatDuo and the answer relayed. It replaces the v1 section, which
     allowed a read-only copy.
Safe to run again (it changes nothing the second time). The old SKILL.md is backed up to
~/mc-backups/skills/ first. Never touches the ratebase or the engines.
Usage: python patch_qs_agent.py <hermes skills dir>
"""
import datetime, os, re, sys
from pathlib import Path

MARK_V1 = "<!-- mahareka:ratebase-master-rule v1 (added by mahareka-skills; keep) -->"
MARK = "<!-- mahareka:ratebase-master-rule v2 (added by mahareka-skills; keep) -->"
RULE = MARK + """
## One ratebase, on MatDuo (R-MASTER)

There is one QS_RATEBASE: the one on MatDuo (the Linux VPS). No other machine keeps a ratebase,
and this skill runs on MatDuo only (Zaim, 24 Nov 2026).

- **On MatDuo:** nothing changes. Publish and install ratebase updates exactly as this skill
  already says.
- **On any other machine:** do not price there. Never quote, save or publish a rate from memory
  or from a file found on that machine. For a rate, costing or BQ price check, ask MatDuo (the
  chief-of-staff skill: `_tools/ask_master.py ask --desk qs "..."`) and relay its answer.
- A new rate or rule learned on another machine is **staged**: send it to MatDuo as
  `Staged for master:` with each item (trade, item, UOM, rate, source, date). Zaim approves it
  and MatDuo adds it to the master.
- A question that reaches MatDuo from another agent through Mission Control is answered like
  Zaim's own, with the same checks. It is a question only: nothing is sent, spent or changed.
"""

def remove_windows(text):
    """Take windows out of `platforms` inside the frontmatter, when another platform remains.
    Returns (text, changed)."""
    m = re.match(r"(---\r?\n)(.*?)(\r?\n---)", text, re.S)
    if not m: return text, False
    fm, nl = m.group(2), "\r\n" if "\r\n" in m.group(2) else "\n"
    lines = fm.split(nl)
    is_win = lambda x: x.strip().strip("'\"").lower() == "windows"
    for i, line in enumerate(lines):
        k = re.match(r"^(\s*)platforms:\s*(.*)$", line)
        if not k: continue
        indent, val = k.group(1), k.group(2).strip()
        if val.startswith("["):                                   # platforms: [macos, linux, windows]
            items = [x.strip() for x in val.strip("[]").split(",") if x.strip()]
            keep = [x for x in items if not is_win(x)]
            if len(keep) == len(items) or not keep: return text, False
            lines[i] = f"{indent}platforms: [{', '.join(keep)}]"
        elif val:                                                 # platforms: macos, linux, windows
            items = [x.strip() for x in val.split(",") if x.strip()]
            keep = [x for x in items if not is_win(x)]
            if len(keep) == len(items) or not keep: return text, False
            lines[i] = f"{indent}platforms: {', '.join(keep)}"
        else:                                                     # block list: "  - windows"
            j, idx = i + 1, []
            while j < len(lines) and re.match(r"^\s*-\s+", lines[j]): idx.append(j); j += 1
            win = [n for n in idx if is_win(lines[n].split("-", 1)[1])]
            if not win or len(win) == len(idx): return text, False
            for n in reversed(win): del lines[n]
        return text[:m.start(2)] + nl.join(lines) + text[m.end(2):], True
    return text, False

def set_rule(text):
    """Put the v2 rule in. Returns (text, what happened or None)."""
    if MARK in text: return text, None
    nl = "\r\n" if "\r\n" in text else "\n"
    rule = RULE.replace("\n", nl)
    at = text.find(MARK_V1)
    if at < 0: return text.rstrip("\r\n") + nl + nl + rule, "rule R-MASTER added"
    # The v1 section: its marker, its "## ... (R-MASTER)" heading and everything up to the next
    # heading of the same level or marker comment (or the end), even if it was edited since.
    body = text[at + len(MARK_V1):]
    head = re.match(r"\s*## [^\r\n]*", body)
    start = head.end() if head else 0
    nxt = re.search(r"\r?\n(?=## |<!-- )", body[start:])
    end = at + len(MARK_V1) + (start + nxt.start() if nxt else len(body))
    tail = text[end:].lstrip("\r\n")
    return text[:at] + rule + (nl + tail if tail else ""), "rule R-MASTER updated (v1 to v2)"

def patch(text):
    """Returns (new text, [what changed])."""
    done = []
    text, ch = remove_windows(text)
    if ch: done.append("platforms: removed windows")
    text, what = set_rule(text)
    if what: done.append(what)
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
    if not done: print("[qs-agent] already hidden on windows with rule R-MASTER v2; nothing to change"); return
    if not os.access(f, os.W_OK): print(f"[qs-agent] SKILL.md is read-only; not changed ({', '.join(done)} still to do)"); return
    bk = Path.home() / "mc-backups" / "skills"; bk.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    (bk / f"mahareka-qs-agent-SKILL-{stamp}.md").write_bytes(old.encode("utf-8"))
    tmp = f.with_suffix(".md.tmp"); tmp.write_bytes(new.encode("utf-8")); os.replace(tmp, f)
    print(f"[qs-agent] {', '.join(done)} (old SKILL.md in {bk})")

if __name__ == "__main__":
    main()
