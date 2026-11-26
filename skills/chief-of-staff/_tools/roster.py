#!/usr/bin/env python3
"""
Find the Virtual Office roster on this machine and print one staff card.
The roster is `office/roster.md` in the shared wiki folder that Mission Control keeps on every
agent (the folder whose INDEX.md starts "# Shared wiki (from Zaim"). Read-only.
Usage: python roster.py --list                 names, roles and desks
       python roster.py --staff hakim          how to use + that staff member's card
       python roster.py --staff "commercial"   also matches a desk or role
       python roster.py --staff pm             a desk code (the card's "Kod meja" line)
       python roster.py --staff pm --since ab12cd34ef56
                                               the card again only if it changed since that version
       python roster.py --path                 where the roster is
Every card ends with "CARD-VERSION <id>": a fingerprint of what was printed. A conversation that
already holds a card asks with --since <id>; "UNCHANGED" means the card it holds is still right.
Standard library only. $MAHAREKA_ROSTER names the file directly.
"""
import argparse, hashlib, os, re, sys
from pathlib import Path

SKIP = {"node_modules", "__pycache__", "venv", ".venv", "venvs", "site-packages", "mc-backups", "cache", "scratch", "sessions", "logs"}

def find_roster():
    env = os.environ.get("MAHAREKA_ROSTER")
    if env: return Path(env).expanduser() if Path(env).expanduser().is_file() else None
    home = Path.home()
    roots = [home / ".hermes", home / "AppData" / "Local" / "hermes", home]
    for root in roots:
        if not root.is_dir(): continue
        base = len(root.parts)
        for d, dirs, files in os.walk(root):
            depth = len(Path(d).parts) - base
            dirs[:] = [x for x in dirs if depth < 6 and x not in SKIP and not x.startswith("tmp") and (not x.startswith(".") or x == ".hermes")]
            if Path(d).name == "office" and "roster.md" in files:
                index = Path(d).parent / "INDEX.md"
                try:
                    if index.is_file() and index.read_text(encoding="utf-8", errors="replace").startswith("# Shared wiki (from Zaim"):
                        return Path(d) / "roster.md"
                except OSError: pass
    return None

def sections(text):
    """(intro, [(heading, body)]) — staff cards are the ### sections."""
    parts = re.split(r"(?m)^### ", text)
    return parts[0], [(p.split("\n", 1)[0].strip(), "### " + p.rstrip()) for p in parts[1:]]

def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(); ap.add_argument("--list", action="store_true"); ap.add_argument("--staff"); ap.add_argument("--path", action="store_true")
    ap.add_argument("--since", help="a CARD-VERSION read earlier: print the card only if it changed")
    a = ap.parse_args()
    f = find_roster()
    if not f: print("NO ROSTER: office/roster.md is not in a shared wiki folder on this machine yet."); sys.exit(2)
    if a.path: print(f); return
    intro, cards = sections(f.read_text(encoding="utf-8", errors="replace"))
    if a.list or not a.staff:
        for h, _ in cards: print("- " + h)
        return
    want = a.staff.strip().lower()
    # a desk code (qs, pm, cos, ...) matches the card's own "Kod meja" line first; a name, role or desk matches the heading
    hit = [c for h, c in cards if re.search(rf"(?mi)^- Kod meja:\s*{re.escape(want)}\s*$", c)] or [c for h, c in cards if want in h.lower()]
    if not hit: print(f"NO STAFF matches '{a.staff}'. Staff:"); [print("- " + h) for h, _ in cards]; sys.exit(3)
    how = re.search(r"(?ms)^## Cara guna\n.*?(?=^## )", intro)
    card = (how.group(0).rstrip() + "\n\n" if how else "") + "\n\n".join(hit)
    version = hashlib.sha256(card.encode("utf-8")).hexdigest()[:12]
    if a.since and a.since.strip().lower() == version:
        print(f"UNCHANGED {version}: the card you hold is still right."); return
    if a.since: print("CARD CHANGED: this card replaces the one you read before. Follow it from this answer on.\n")
    print(card + f"\n\nCARD-VERSION {version}")

if __name__ == "__main__":
    main()
