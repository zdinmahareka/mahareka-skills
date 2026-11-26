#!/usr/bin/env python3
"""
Layer F — Rate Intelligence, against the ONE ratebase. Read-only.

Compares the priced BQ lines (JSON from check_bq.py) with QS_RATEBASE, which belongs to
`mahareka-qs-agent`. It never opens the workbook by itself and never writes it: it loads the
owner's own tool (`ratebase.py`, beside `qs_boot.py` in KNOWLEDGE) and reads through its
functions `open_rb()`, `rate_tabs(wb)` and `rows(ws)`. A sell rate is the one the owner
computed; nothing is derived or rounded here.

Usage:
  PY rate_check.py --lines findings.json --basis SELL|COST [--subcon SMC] [--project N050]
                   [--band 0.15] --json rates.json [--tool <path to ratebase.py>]

Writes rates.json for stage 03, always (so a check that could not run is seen, never silent):
  flags   band deviations, ids R01.., ranked by RM impact, each with its ratebase context
  shift   a systematic shift (probable pricelist revision), or null
  gaps    priced lines the ratebase does not hold: the list for `mahareka-qs-agent` to store
  error   why the ratebase could not be read (then flags and gaps are empty)
Matching is deliberately conservative (fuzzy description match, same UOM); the judgment on
near-matches is stage 03's, using _shared/learning.md.
"""
import argparse, contextlib, importlib.util, io, json, re, statistics, sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import where  # noqa: E402  (finds KNOWLEDGE the same way as every other tool here)

__version__ = "2.2"
NEEDS = ("open_rb", "rate_tabs", "rows")
STOP = {"to","supply","and","install","c/w","cw","the","of","for","with","in","at","complete","all","incl","including"}
DIM_RE = re.compile(r"\b\d+\s*(mm|m|ft|'|\")\b|\b[hwd]\s*[:=]?\s*\d+\b|\b\d{3,4}\b")
MATCH, SAME = 0.72, 0.85
SKIP_STATUS = ("SUPERSEDED", "BENCHMARK")

def normkey(desc):
    d = DIM_RE.sub(" ", str(desc).lower())
    return " ".join([w for w in re.split(r"[^a-z0-9]+", d) if w and w not in STOP][:8])

def sim(a, b): return SequenceMatcher(None, a, b).ratio()

def num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

def load_ratebase(tool):
    """Every live rate the ratebase holds, read through its owner's tool.
    -> (rows, source) ; rows: {id, item, uom, basis, rate, status, stale}. Raises RuntimeError with the reason."""
    tool = Path(tool)
    if not tool.is_file():
        raise RuntimeError(f"ratebase.py not found at {tool}: the rate authority (mahareka-qs-agent) is not on this machine")
    sys.dont_write_bytecode = True               # read-only means no cache file left in the owner's folder either
    spec = importlib.util.spec_from_file_location("mahareka_qs_ratebase", tool)
    rb = importlib.util.module_from_spec(spec)
    quiet = io.StringIO()
    try:
        with contextlib.redirect_stdout(quiet):
            spec.loader.exec_module(rb)
            missing = [f for f in NEEDS if not callable(getattr(rb, f, None))]
            if missing:
                raise RuntimeError(f"ratebase.py v{getattr(rb, '__version__', '?')} has no {', '.join(missing)}(): this check reads the ratebase only through those")
            wb, path = rb.open_rb()
            out = []
            for tab in rb.rate_tabs(wb):
                for r in rb.rows(wb[tab]):
                    status = str(r.get("STATUS") or "").strip().upper()
                    if not r.get("ITEM") or any(status.startswith(s) for s in SKIP_STATUS): continue
                    stale = None
                    if callable(getattr(rb, "freshness", None)):
                        try:
                            _, age, label = rb.freshness(r)
                            stale = age if label == "STALE" else None
                        except Exception:
                            stale = None
                    for basis, col in (("COST", "ALL-IN"), ("SELL", "SELL")):
                        if num(r.get(col)) is not None and num(r.get(col)) > 0:
                            out.append({"id": r.get("ID"), "tab": tab, "item": str(r.get("ITEM")), "uom": str(r.get("UOM") or "").strip().lower(),
                                        "basis": basis, "rate": num(r.get(col)), "status": status.split()[0] if status else "", "stale": stale})
    except SystemExit as e:                      # the owner's tool stops like this when the master is missing
        raise RuntimeError(f"the ratebase could not be opened: {str(e).splitlines()[0] if str(e) else 'ratebase.py stopped'}")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"the ratebase could not be read through ratebase.py: {type(e).__name__}: {e}")
    notes = [l for l in quiet.getvalue().splitlines() if l.startswith("WARNING")]
    return out, {"tool": f"ratebase.py v{getattr(rb, '__version__', '?')}", "file": Path(path).name, "rates": len(out), "warnings": notes[:5]}

def check(lines, hist, basis, band):
    flags, matches, gaps, devs = [], [], [], []
    for l in lines:
        if not l.get("rate") or not l.get("desc"): continue
        key, unit = normkey(l["desc"]), str(l.get("unit") or "").strip().lower()
        cands = [h for h in hist if h["basis"] == basis and h["uom"] == unit]
        best, score = None, 0
        for h in cands:
            s = sim(key, normkey(h["item"]))
            if s > score: best, score = h, s
        if not best or score < MATCH:
            gaps.append({"row": l["row"], "desc": l["desc"][:120], "unit": l.get("unit"), "rate": l["rate"], "basis": basis,
                         "near": ({"id": best["id"], "item": best["item"][:60], "score": round(score, 2)} if best and score >= 0.5 else None)})
            continue
        same = [h for h in cands if sim(normkey(best["item"]), normkey(h["item"])) >= SAME]
        verified = [h for h in same if h["status"] == "VERIFIED"]
        pool = verified or same                    # compare against VERIFIED; say so when there is none
        med = statistics.median(h["rate"] for h in pool)
        dev = (l["rate"] - med) / med if med else 0
        ctx = {"ids": [h["id"] for h in pool][:6], "n": len(pool), "against": "VERIFIED" if verified else "/".join(sorted({h["status"] or "?" for h in pool})),
               "stale_days": max([h["stale"] for h in pool if h["stale"]] or [0]) or None, "score": round(score, 2)}
        matches.append({"row": l["row"], "rate": l["rate"], "median": med, "dev": dev})
        devs.append(dev)
        if abs(dev) > band:
            flags.append({"row": l["row"], "desc": l["desc"][:60], "rate": l["rate"], "median": med, "dev_pct": round(dev * 100, 1),
                          "rm_impact": round(abs((l.get("qty") or 0) * (l["rate"] - med)), 2), "ratebase": ctx})
    shift = None
    if len(devs) >= 5:
        moved = [d for d in devs if abs(d) > band / 2]
        if moved and len(moved) / len(devs) >= 0.6:
            signs = [1 if d > 0 else -1 for d in moved]
            if abs(sum(signs)) / len(signs) >= 0.8:
                shift = {"direction": "UP" if sum(signs) > 0 else "DOWN", "median_shift_pct": round(statistics.median(moved) * 100, 1),
                         "affected": len(moved), "matched": len(devs)}
    flags.sort(key=lambda x: -x["rm_impact"])
    for i, f in enumerate(flags, 1): f["id"] = f"R{i:02d}"
    return flags, shift, gaps, matches

def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(errors="replace")  # Windows consoles
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True); ap.add_argument("--json", required=True)
    ap.add_argument("--basis", default="SELL", choices=["SELL", "COST"]); ap.add_argument("--band", type=float, default=0.15)
    ap.add_argument("--subcon", default=""); ap.add_argument("--project", default=""); ap.add_argument("--tool")
    a = ap.parse_args()
    out = {"version": __version__, "basis": a.basis, "band": a.band, "subcon": a.subcon, "project": a.project,
           "source": None, "error": None, "matched": 0, "flags": [], "shift": None, "gaps": []}
    lines = json.loads(Path(a.lines).read_text(encoding="utf-8"))["lines"]
    tool = Path(a.tool) if a.tool else where.knowledge()[0] / "ratebase.py"
    try:
        hist, out["source"] = load_ratebase(tool)
        out["flags"], out["shift"], out["gaps"], matches = check(lines, hist, a.basis, a.band)
        out["matched"] = len(matches)
    except RuntimeError as e:
        out["error"] = str(e)
    Path(a.json).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    if out["error"]:
        print(f"RATE CHECK DID NOT RUN: {out['error']}")
        print("Stage 03 must raise this as an ASK. Never price-check blind and never invent a benchmark.")
        sys.exit(1)
    s = out["source"]
    print(f"RATEBASE {s['file']} via {s['tool']} ({s['rates']} live rates) | COMPARED: {out['matched']} | BAND FLAGS: {len(out['flags'])} | RATEBASE GAPS: {len(out['gaps'])}")
    for w in s["warnings"]: print(f"  {w}")
    if out["shift"]:
        sh = out["shift"]
        print(f"\nSYSTEMATIC SHIFT {sh['direction']} ~{sh['median_shift_pct']}% ({sh['affected']}/{sh['matched']} compared lines): probable pricelist revision. "
              f"ADVISE: request latest pricelist from {a.subcon or 'subcon'} BEFORE flagging individual lines.")
    for f in out["flags"]:
        c = f["ratebase"]
        print(f"[{f['id']}] row {f['row']}: {f['desc']} — RM{f['rate']:,.2f} vs ratebase median RM{f['median']:,.2f} ({f['dev_pct']:+}%, n={c['n']} {c['against']}"
              f"{', STALE ' + str(c['stale_days']) + 'd: verify current' if c['stale_days'] else ''}) RM impact ~{f['rm_impact']:,.2f}")
    if out["gaps"]:
        print(f"\n{len(out['gaps'])} line(s) the ratebase does not hold. List them in the report under \"For the ratebase\"; mahareka-qs-agent stores them as PENDING on Zaim's word.")

if __name__ == "__main__":
    main()
