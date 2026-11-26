#!/usr/bin/env python3
"""
skill_check.py: audit a Mahareka skill against MAHAREKA_STANDARD.md (the 11 principles).

Catches the failure classes that actually cost time:
  - Type C skill with no bootstrap (engines can vanish silently)
  - memory shipped inside the skill instead of the KNOWLEDGE folder
  - a rule copied from another skill and left stale (rounding, markup, pro-rata)
  - a second rate memory growing beside the master
  - no regression case, so nobody can prove the engine still works
  - no README.md for people (rule M11)

Usage (PY = the Python recorded in ~/.mahareka/python):
  PY scripts/skill_check.py <skill folder>
  PY scripts/skill_check.py --all [folder]     every skill below the folder; default: the folder
                                               this machine recorded in ~/.mahareka/skills-dir
  PY scripts/skill_check.py <path> --json      machine-readable
  PY scripts/skill_check.py <path> --log       also stage one AUDIT_LOG row per skill (registry.py)

Exit 0 = no BLOCKER findings. Exit 1 = at least one BLOCKER.
Complements icm_check.py (structure, M1-M11); it does not replace it.
"""
import os, sys, re, json, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _env  # noqa: E402
from icm_check import readme_findings  # noqa: E402

__version__ = "2.2"

# Rules owned by one skill. If another skill states a different value, that copy is stale.
# pattern -> (owner, correct value, severity)
OWNED_RULES = [
    (r"(?i)round(ed)?\s+(to\s+)?(the\s+)?nearest\s+RM\s?5\b",
     "mahareka-qs-agent", "rule R-ALL-42 (read the value from the owner; never restate it)", "BLOCKER"),
    (r"(?i)MROUND\s*\([^)]*,\s*5\s*\)",
     "mahareka-qs-agent", "rule R-ALL-42 (read the value from the owner; never restate it)", "BLOCKER"),
    (r"(?i)ROUND\s*\(\s*COST\s*[x×*]\s*MARKUP\s*/\s*5\s*\)\s*[x×*]\s*5",
     "mahareka-qs-agent", "rule R-ALL-42 (read the value from the owner; never restate it)", "BLOCKER"),
]

# A second rate memory beside QS_RATEBASE is forbidden by mahareka-qs-agent's own boundary.
SECOND_MEMORY = re.compile(r"(?i)\b(Rate_History|RateBase)\.xlsx\b")

ENGINE_EXT = (".py",)
MEMORY_EXT = (".xlsx", ".xlsm", ".db", ".sqlite", ".json")


def read(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        return ""


def frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def classify(files, skill_md):
    """Infer archetype from what the skill actually ships and claims."""
    has_engine = any(f.endswith(ENGINE_EXT) for f in files)
    has_memory = any(f.endswith(MEMORY_EXT) for f in files)
    has_ref = any(f.startswith(("references/", "reference/")) or "/references/" in f
                  for f in files)
    learns = bool(re.search(
        r"(?i)\b(self[- ]?learn|self[- ]?reinforc|append to memory|store.*rate|rate memory|"
        r"memory file|learning protocol|write.*back to memory)\b", skill_md))
    claims_engine = bool(re.search(r"(?i)scripts?/\S+\.py|python3\s+\S+\.py", skill_md))

    if learns or has_memory or ((has_engine or claims_engine) and learns):
        t = "C"
    elif has_engine or claims_engine:
        t = "C"          # ships code -> engine layer -> C rules apply
    elif has_ref:
        t = "B"
    else:
        t = "A"

    sub = ""
    if t == "C":
        # order matters: a skill that OWNS a memory is C1 even if it also audits
        if has_memory or re.search(r"(?i)\b(rate memory|pricing brain|master ratebase|"
                                   r"self[- ]reinforc\w*|rate engine)\b", skill_md):
            sub = "C1 memory agent"
        elif re.search(r"(?i)\b(audit|verify|error checker|review)\b", skill_md[:600]):
            sub = "C2 auditor"
        elif re.search(r"(?i)\b(generate|produce|report pack|output pack)\b", skill_md[:1200]):
            sub = "C3 producer"
        else:
            sub = "C1 memory agent"
    elif t == "B":
        sub = "B2 template/output spec" if re.search(r"(?i)template|format spec", skill_md) else "B1 knowledge reference"
    else:
        sub = "A2 procedure" if re.search(r"(?i)\bworkflow|step \d|procedure\b", skill_md) else "A1 style/format"
    return t, sub, {"engine": has_engine, "memory": has_memory, "reference": has_ref, "learns": learns}


def audit(path):
    path = os.path.abspath(path)
    name = os.path.basename(path)
    files = []
    for dp, _, fns in os.walk(path):
        for fn in fns:
            if "__pycache__" in dp:
                continue
            files.append(os.path.relpath(os.path.join(dp, fn), path).replace(os.sep, "/"))
    skill_md_path = os.path.join(path, "SKILL.md")
    md = read(skill_md_path)
    fm = frontmatter(md)
    t, sub, feat = classify(files, md)

    F = []   # (severity, principle, message)
    def add(sev, pr, msg): F.append((sev, pr, msg))

    # --- P0 SKILL.md basics ---
    if not md:
        add("BLOCKER", "P0", "SKILL.md missing or unreadable")
        return dict(name=name, path=path, type=t, subtype=sub, files=files, findings=F, features=feat)
    if not fm.get("name"):
        add("BLOCKER", "P0", "frontmatter missing `name`")
    elif fm["name"] != name:
        add("WARN", "P0", f"frontmatter name '{fm['name']}' != folder '{name}'")
    desc = fm.get("description", "")
    if not desc:
        add("BLOCKER", "P0", "frontmatter missing `description`: skill will never trigger reliably")
    else:
        if len(desc) < 120:
            add("WARN", "P0", f"description short ({len(desc)} chars): add trigger phrasings")
        # BM detection: a keyword list alone always leaks (it missed "vendor mana
        # bagus", then "senarai kerosakan"). Combine a function-word list with
        # Malay morphology: ke-...-an, pe-...-an, ber-, meN-, se- affixes.
        bm_words = re.search(
            r"(?i)\b(harga|berapa|semak|simpan|tolong|buat|kos|betul|nak|mana|siapa|"
            r"macam|bila|boleh|guna|cari|tengok|tambah|ubah|kena|dah|lagi|semua|"
            r"senarai|jadual|kerja|projek|tapak|baru|lama|ada|ni|tak|yang|untuk|dengan)\b", desc)
        bm_morph = re.search(
            r"(?i)\b(ke\w{3,}an|pe\w{3,}an|ber\w{3,}|mem\w{3,}|men\w{3,}|meng\w{3,}|se\w{4,}kan)\b",
            desc)
        bm = bm_words or bm_morph
        if not bm:
            add("WARN", "SKILL.md", "description has no Bahasa Malaysia trigger words")
        if not re.search(r"(?i)\b(instead|use .* for|rather than)\b", desc):
            add("INFO", "SKILL.md", "description states no boundary against neighbouring skills")

    # --- P1 two layers ---
    engines_in_skill = [f for f in files if f.endswith(ENGINE_EXT)]
    memory_in_skill = [f for f in files if f.endswith(MEMORY_EXT)]
    if t == "C":
        # P1 tests MUTABILITY, not file type. Static engines inside a skill are a
        # legitimate trade-off (fewer uploads, no drift): flag the cost, not a fault.
        if engines_in_skill:
            add("INFO", "P1", f"engines ship inside the skill ({len(engines_in_skill)}): "
                              f"valid for static code, but patching one needs a re-zip and "
                              f"version bump. Fine if deliberate.")
        if memory_in_skill:
            declared_seed = bool(re.search(r"(?i)\bseed\b", md)) and \
                            bool(re.search(r"(?i)project knowledge|knowledge folder|\bKNOWLEDGE\b", md))
            if declared_seed:
                add("WARN", "P1", f"memory ships inside the skill as a declared SEED "
                                  f"({', '.join(memory_in_skill[:2])}): confirm the bootstrap "
                                  f"WARNS when the seed is used, or a broken install looks healthy")
            else:
                add("BLOCKER", "P1", f"memory shipped inside the skill: "
                                     f"{', '.join(memory_in_skill[:3])}: it can never be updated, "
                                     f"so the loop dies silently. Move it to the KNOWLEDGE folder.")
    # reference docs that get appended to
    for f in files:
        if f.endswith(".md") and re.search(r"(?i)lesson|learning|history", f):
            body = read(os.path.join(path, f))
            if re.search(r"(?i)\b(append|add a line|log here|new entries)\b", body):
                add("WARN", "P1", f"`{f}` is written to during use but ships inside the skill: "
                                  f"move to the KNOWLEDGE folder or it cannot actually be updated")

    # --- P2 bootstrap ---
    if t == "C":
        has_boot = any(re.search(r"(?i)_?boot\.py$|selfcheck\.py$", f) for f in files) or \
                   bool(re.search(r"(?i)\b\w*_?boot\.py\b|selfcheck\.py", md))
        if not has_boot:
            add("BLOCKER", "P2", "Type C skill has no bootstrap: engines can go missing undetected")
        elif not re.search(r"(?i)(step\s*0|first|before any|always run)", md[:4000]):
            add("WARN", "P2", "bootstrap exists but SKILL.md does not clearly order it FIRST")

    # --- P3 loud failure ---
    if t == "C" and not re.search(
            r"(?i)(never .*(silent|fallback|hand[- ]calculat)|do not hand[- ]calculat|"
            r"stop\b.*missing|refuse[sd]? to (run|compute)|DEGRADED)", md):
        add("WARN", "P3", "no explicit prohibition on silent fallback when files/data are missing")

    # --- P4 read-only write path ---
    if t == "C" and feat["memory"] or re.search(r"(?i)updated .*\.xlsx|write.*back|save.*back", md):
        if not re.search(r"(?i)(outputs|publish|staged|hand[s]? over|beside)", md):
            add("WARN", "P4", "skill writes memory but never says where the updated file is put for Zaim")
        if not re.search(r"(?i)(replace|save|put).{0,60}(project knowledge|project files|knowledge folder|\bKNOWLEDGE\b)", md):
            add("WARN", "P4", "no instruction telling Zaim where to put the updated memory file")

    # --- P5 append-only ---
    if t == "C" and re.search(r"(?i)memory|history|ratebase", md):
        if not re.search(r"(?i)(supersed|append[- ]only|never delete|retain.*old|keep.*old)", md):
            add("WARN", "P5", "memory discipline stated without append-only / SUPERSEDED rule")

    # --- P6 frozen formulas, live prices ---
    for f in engines_in_skill:
        body = read(os.path.join(path, f))
        hard = re.findall(r"(?i)\b(price|rate|cost)\s*=\s*\d+(\.\d+)?", body)
        if hard:
            add("WARN", "P6", f"`{f}` appears to hardcode a price/rate value")

    # --- P7 STATUS discipline ---
    if t == "C" and feat["learns"]:
        sts = sum(1 for s in ("VERIFIED", "BUDGETARY", "PENDING", "SUPERSEDED")
                  if re.search(rf"(?i)\b{s}\b", md))
        if sts < 2:
            add("WARN", "P7", "no STATUS vocabulary (VERIFIED / BUDGETARY / PENDING / SUPERSEDED) in SKILL.md")

    # --- P8 decision authority ---
    if not re.search(r"(?i)(ask zaim|always ask|zaim decides|decision authority|never assume)", md):
        add("WARN" if t == "C" else "INFO", "P8", "no decision-authority statement (what is automatic vs what goes to Zaim)")

    # --- P9 numbered gates ---
    if t == "C" and not re.search(r"(?i)\bgate\s*[A-Z]?\d|\b[QG][1-9][0-9]?\b", md):
        add("INFO", "P9", "no numbered quality gates: unresolved checks cannot be named in output")

    # --- P10 regression case ---
    if t == "C":
        if not re.search(r"(?i)(regression|calibration|worked example|proven:|verified vs|known.{0,12}answer)", md):
            add("WARN", "P10", "no regression/calibration case: cannot prove the engine still works after a change")

    # --- P11 versioning ---
    for f in engines_in_skill:
        if "__version__" not in read(os.path.join(path, f)):
            add("INFO", "P11", f"`{f}` has no __version__ stamp: version drift will go unnoticed")

    # --- cross-skill owned rules ---
    for f in files:
        if not f.endswith((".md", ".py")):
            continue
        body = read(os.path.join(path, f))
        for pat, owner, correct, sev in OWNED_RULES:
            if re.search(pat, body) and name != owner:
                add(sev, "CROSS", f"`{f}` carries a stale copy of a rule owned by {owner}: should be: {correct}")
        if name != "mahareka-qs-agent":
            m = SECOND_MEMORY.search(body)
            if m:
                add("BLOCKER", "CROSS",
                    f"`{f}` maintains `{m.group(0)}`: a second rate memory beside QS_RATEBASE.xlsx "
                    f"(mahareka-qs-agent declares one master)")

    # --- M11 a page for people ---
    for sev, msg in readme_findings(Path(path)):
        add(sev, "M11", msg.replace("M11: ", ""))

    return dict(name=name, path=path, type=t, subtype=sub, files=files, findings=F, features=feat)


def render(reports, as_json=False):
    if as_json:
        print(json.dumps([{**r, "findings": [list(f) for f in r["findings"]]} for r in reports], indent=2))
        return max((1 for r in reports for f in r["findings"] if f[0] == "BLOCKER"), default=0)

    worst = 0
    for r in reports:
        b = sum(1 for f in r["findings"] if f[0] == "BLOCKER")
        w = sum(1 for f in r["findings"] if f[0] == "WARN")
        i = sum(1 for f in r["findings"] if f[0] == "INFO")
        verdict = "BLOCKED" if b else ("NEEDS WORK" if w else "PASS")
        worst = max(worst, 1 if b else 0)
        print(f"\n{'='*74}")
        print(f"  {r['name']}   [{r['type']} · {r['subtype']}]   {len(r['files'])} files")
        print(f"  verdict: {verdict}   ({b} blocker, {w} warn, {i} info)")
        print(f"{'='*74}")
        for sev in ("BLOCKER", "WARN", "INFO"):
            for s, pr, msg in r["findings"]:
                if s == sev:
                    print(f"  [{sev:<7}] {pr:<10} {msg}")
        if not r["findings"]:
            print("  no findings: conforms to MAHAREKA_STANDARD v1.0")
    print()
    return worst


def log(reports):
    """One AUDIT_LOG row per skill, staged for Zaim (never written into the registry itself)."""
    import registry
    for r in reports:
        b, w, i = (sum(1 for f in r["findings"] if f[0] == s) for s in ("BLOCKER", "WARN", "INFO"))
        verdict = "BLOCKED" if b else ("NEEDS WORK" if w else "PASS")
        first = next((f[2] for f in r["findings"] if f[0] == "BLOCKER"), "") or next((f[2] for f in r["findings"] if f[0] == "WARN"), "no findings")
        registry.log_audit(r["name"], verdict, b, w, i, first[:200])


def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(errors="replace")  # Windows consoles
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--cross", action="store_true", help="(implied) cross-skill rule conflicts")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--log", action="store_true", help="stage one AUDIT_LOG row per skill")
    a = ap.parse_args()

    if a.all:
        root, how = _env.skills_dir(a.path)
        if not root or not root.is_dir():
            sys.exit("STOP: no skills folder. Give one: skill_check.py --all <folder>")
        targets = [str(p) for p in _env.find_skills(root)]
        if not targets:
            sys.exit(f"STOP: no skill (a folder holding SKILL.md) below {root}")
    elif a.path:
        targets = [a.path]
    else:
        sys.exit("give a skill path, or --all")

    reports = [audit(t) for t in targets]
    worst = render(reports, a.json)
    if a.log:
        try:
            log(reports)
        except ImportError:
            sys.exit("STOP: this Python has no openpyxl, so the audit was not logged. Run with the Python in ~/.mahareka/python.")
        except (FileNotFoundError, KeyError) as e:
            sys.exit(f"STOP: the audit was not logged: {e}")
    sys.exit(worst)


if __name__ == "__main__":
    main()
