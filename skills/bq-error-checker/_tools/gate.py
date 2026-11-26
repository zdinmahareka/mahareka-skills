#!/usr/bin/env python3
"""
Stage gates for a BQ audit run. Writes RUN/<stage>/check.md, first line `pass` or `fail: <why>`.
Usage: python gate.py RUN 01|02|03     check that stage
       python gate.py RUN status       print every stage's verdict (status lives on disk)
Exit 1 on fail. Stage 04 is checked by Zaim, so it has no script gate.
"""
import json, re, sys
from pathlib import Path

DECISIONS = ("KEEP", "DOWNGRADE", "DROP", "ASK")

def front(path):
    """Frontmatter as a dict; inline '# comments' stripped."""
    m = re.match(r"---\n(.*?)\n---", path.read_text(encoding="utf-8", errors="replace"), re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.split("#", 1)[0].strip()
    return out

def stage_dir(run, n):
    hits = sorted(run.glob(f"{n}_*"))
    return hits[0] if hits else None

def g01(run):
    p = run / "01_intake" / "intake.md"
    if not p.is_file(): return "intake.md missing"
    f = front(p)
    missing = [k for k in ("file", "sheet", "mode", "depth", "basis") if not f.get(k)]
    if missing: return "not set: " + ", ".join(missing)
    if f["mode"] not in ("1", "2"): return f"mode must be 1 or 2, not '{f['mode']}'"
    if f["depth"] not in ("management", "full"): return f"depth must be management or full, not '{f['depth']}'"
    if f["basis"].upper() not in ("SELL", "COST"): return f"basis must be SELL or COST, not '{f['basis']}'"
    if f.get("open_questions", "0") not in ("", "0"): return f"{f['open_questions']} open question(s) waiting for Zaim"
    return None

def g02(run):
    d = run / "02_checks"
    boot = d / "boot.txt"
    if not boot.is_file(): return "boot.txt missing: run qs_boot.py first"
    if "DEGRADED" in boot.read_text(encoding="utf-8", errors="replace").upper(): return "rate authority DEGRADED: name the files to re-upload, then rerun"
    fj = d / "findings.json"
    try: data = json.loads(fj.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError): return "findings.json missing or not valid JSON"
    sheet = front(run / "01_intake" / "intake.md").get("sheet")
    if data.get("info", {}).get("sheet") != sheet:
        return f"findings.json checked sheet '{data.get('info', {}).get('sheet')}', intake says '{sheet}'"
    if any("id" not in f for f in data.get("findings", [])): return "findings without ids: rerun check_bq.py v2.0"
    return None

def ids_from_02(run):
    d = run / "02_checks"
    return [f["id"] for f in json.loads((d / "findings.json").read_text(encoding="utf-8", errors="replace")).get("findings", [])]

def g03(run):
    p = run / "03_review" / "review.md"
    if not p.is_file(): return "review.md missing"
    rows = {}
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and re.fullmatch(r"[FRJ]\d{2,}", cells[0]):
            rows[cells[0]] = cells[3].upper()
    missing = [i for i in ids_from_02(run) if i not in rows]
    if missing: return "no decision for: " + ", ".join(missing)
    bad = [i for i, dcs in rows.items() if dcs not in DECISIONS]
    if bad: return "decision must be KEEP, DOWNGRADE, DROP or ASK: " + ", ".join(bad)
    return None

GATES = {"01": g01, "02": g02, "03": g03}

def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(errors="replace")  # Windows consoles
    if len(sys.argv) != 3: sys.exit(__doc__)
    run, what = Path(sys.argv[1]), sys.argv[2]
    if what == "status":
        for d in sorted(p for p in run.iterdir() if p.is_dir() and re.match(r"\d\d_", p.name) and not p.name.startswith("00")):
            c = d / "check.md"
            verdict = c.read_text(encoding="utf-8", errors="replace").splitlines()[0] if c.is_file() else ("awaiting Zaim" if d.name.startswith("04") else "not checked")
            print(f"{d.name:<14} {verdict}")
        return
    if what not in GATES: sys.exit(f"unknown stage {what}: use 01, 02, 03 or status")
    d = stage_dir(run, what)
    if d is None: sys.exit(f"no {what}_ folder in {run}")
    prev = {"02": "01", "03": "02"}.get(what)
    pd = stage_dir(run, prev) if prev else None
    if prev and not (pd and (pd / "check.md").is_file() and (pd / "check.md").read_text(encoding="utf-8", errors="replace").startswith("pass")):
        why = f"stage {prev} has not passed its gate"
    else:
        why = GATES[what](run)
    (d / "check.md").write_text(("pass" if why is None else f"fail: {why}") + "\n", encoding="utf-8")
    print(f"{d.name}: " + ("pass" if why is None else f"fail: {why}"))
    sys.exit(0 if why is None else 1)

if __name__ == "__main__":
    main()
