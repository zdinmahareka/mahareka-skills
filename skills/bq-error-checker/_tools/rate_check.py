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
  flags           band deviations, ids R01.., ranked by RM impact, each with its ratebase context
                  and `evidence`: "strong" (2+ VERIFIED rows) or "weak" (one row, or none VERIFIED)
  shift           a systematic shift (probable pricelist revision), or null
  possible        lines with a likely ratebase row that must be confirmed before comparing, and why:
                  another variant (twin / single, 2 / 3 tier), a size-dependent row, a supplier
                  price-list row (a component), a more specific item, another unit, a cost-only row
  not_comparable  lump sums and composite lines: no single rate to compare
  gaps            priced lines the ratebase does not hold: the list for `mahareka-qs-agent` to store
  error           why the ratebase could not be read (then the lists are empty)
A line is COMPARED only when the item, the unit and the variant all agree. Everything less
certain is "possible", never a flag: a false accusation costs more than a missed one. The
judgment is stage 03's, using _shared/learning.md.
Tuned on 26 Nov 2026 from the first run against the real ratebase (MatDuo's seven points).
"""
import argparse, contextlib, importlib.util, io, json, re, statistics, sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import where  # noqa: E402  (finds KNOWLEDGE the same way as every other tool here)

__version__ = "2.3"
NEEDS = ("open_rb", "rate_tabs", "rows")
STOP = {"to","supply","and","install","c/w","cw","the","of","for","with","in","at","complete","all","incl","including"}
DIM_RE = re.compile(r"\b\d+\s*(mm|m|ft|'|\")\b|\b[hwd]\s*[:=]?\s*\d+\b|\b\d{3,4}\b")
MATCH, NEAR = 0.72, 0.60
SKIP_STATUS = ("SUPERSEDED", "BENCHMARK")
# One unit, many spellings. A line and a ratebase row are compared only inside one family.
UOM = {"nos": "nos", "no": "nos", "pc": "nos", "pcs": "nos", "unit": "nos", "units": "nos", "ea": "nos", "each": "nos", "nr": "nos",
       "set": "set", "sets": "set", "lot": "set", "fr": "fr", "ftrun": "fr", "ftr": "fr", "sqft": "sqft", "sf": "sqft", "ft2": "sqft",
       "m": "m", "lm": "m", "rm": "m", "sqm": "sqm", "m2": "sqm", "ls": "ls", "lumpsum": "ls", "ps": "ls", "point": "point", "pt": "point", "pts": "point"}
ABBREV = {"sso": "switch socket outlet", "db": "distribution board"}
# Words that make it a different item, not another wording of the same one.
VARIANT = {"single", "twin", "double", "triple", "dual", "quad"}
SIZE_RE = re.compile(r"\b[hwdl]\s?[<>]?\s?\d{2,4}\b|\b\d{3,4}\s?mm\b", re.I)

def uom(u):
    k = re.sub(r"[^a-z0-9]", "", str(u or "").lower())
    return UOM.get(k, k)

def tokens(desc):
    d = DIM_RE.sub(" ", SIZE_RE.sub(" ", str(desc).lower()))
    out = []
    for w in re.split(r"[^a-z0-9]+", d):
        if not w or w in STOP or (len(w) == 1 and not w.isdigit()): continue      # "s&i", "c/w" leave single letters behind
        out += ABBREV[w].split() if w in ABBREV else [w]
    return out

def normkey(desc): return " ".join(tokens(desc)[:8])
def variants(desc): return {w for w in tokens(desc) if w in VARIANT or re.fullmatch(r"\d{1,2}[a-z]?", w)}
def sizes(desc): return {re.sub(r"\s", "", m.group(0).lower()) for m in SIZE_RE.finditer(str(desc))}
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
                            item, vendor = str(r.get("ITEM")), re.split(r"[^a-z0-9]+", str(r.get("VENDOR/SOURCE") or "").lower())[0]
                            out.append({"id": r.get("ID"), "tab": tab, "item": item, "uom": uom(r.get("UOM")), "uom_raw": str(r.get("UOM") or "").strip(),
                                        "basis": basis, "rate": num(r.get(col)), "status": status.split()[0] if status else "", "stale": stale,
                                        # a row named after its supplier is a line of that supplier's price list: a component, not a finished item
                                        "supplier_row": len(vendor) >= 3 and vendor in tokens(item)})
    except SystemExit as e:                      # the owner's tool stops like this when the master is missing
        raise RuntimeError(f"the ratebase could not be opened: {str(e).splitlines()[0] if str(e) else 'ratebase.py stopped'}")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"the ratebase could not be read through ratebase.py: {type(e).__name__}: {e}")
    notes = [l for l in quiet.getvalue().splitlines() if l.startswith("WARNING")]
    return out, {"tool": f"ratebase.py v{getattr(rb, '__version__', '?')}", "file": Path(path).name, "rates": len(out), "warnings": notes[:5]}

def relate(ta, tb):
    """How two items' words relate: equal, one inside the other, or each has a word the other lacks."""
    if ta == tb: return "equal"
    if ta < tb: return "row is more specific"
    if tb < ta: return "line is more specific"
    return "differs"

def best_of(toks, key, rows):
    """The closest row: same words first, then one inside the other, then the closest wording.
    -> (row, score, relation) or (None, 0, None)"""
    ta, best = set(toks), (None, 0, None, -1)
    for h in rows:
        tb = set(tokens(h["item"]))
        if not ta & tb: continue
        rel, sc = relate(ta, tb), sim(key, normkey(h["item"]))
        rank = {"equal": 3, "row is more specific": 2, "line is more specific": 2, "differs": 0}[rel] + sc
        if rank > best[3]: best = (h, sc, rel, rank)
    return best[:3]

def check(lines, hist, basis, band):
    flags, matches, possible, skipped, gaps, devs = [], [], [], [], [], []
    for l in lines:
        if not l.get("rate") or not l.get("desc"): continue
        desc, unit = str(l["desc"]), uom(l.get("unit"))
        toks, key = tokens(desc), normkey(desc)
        base = {"row": l["row"], "desc": desc[:120], "unit": l.get("unit"), "rate": l["rate"], "basis": basis}
        if unit == "ls" or "+" in desc:
            skipped.append({**base, "why": "lump sum" if unit == "ls" else "composite line (several works in one rate)"}); continue
        def maybe(h, score, why):
            possible.append({**base, "why": why, "ratebase": {"id": h["id"], "item": h["item"][:80], "uom": h["uom_raw"], "status": h["status"], "score": round(score, 2)}})
        same_unit = [h for h in hist if h["basis"] == basis and h["uom"] == unit]
        best, score, rel = best_of(toks, key, same_unit)
        sure = best and rel != "differs" and (score >= MATCH or rel == "equal")
        if not sure:
            # nothing certain in this unit and basis. Close wording here? The same item in another unit, or as a cost rate only?
            other, s2, r2 = best_of(toks, key, [h for h in hist if h["basis"] == basis and h["uom"] != unit])
            cost, s3, r3 = best_of(toks, key, [h for h in hist if h["basis"] != basis and h["uom"] == unit])
            if best and rel != "differs": maybe(best, score, f"the {rel}: confirm the spec matches")
            elif best and score >= NEAR:
                odd = sorted((set(toks) ^ set(tokens(best["item"]))))[:4]
                maybe(best, score, f"close wording, different words ({' / '.join(odd)}): confirm it is the same item")
            elif other and r2 != "differs" and (s2 >= NEAR or r2 == "equal"): maybe(other, s2, f"the ratebase holds it in another unit ({other['uom_raw'] or '?'}): not comparable as it is")
            elif cost and r3 != "differs" and (s3 >= NEAR or r3 == "equal"): maybe(cost, s3, f"the ratebase holds a {cost['basis']} rate only for this item")
            else: gaps.append({**base, "near": ({"id": best["id"], "item": best["item"][:60], "score": round(score, 2)} if best and score >= 0.5 else None)})
            continue
        # the words agree. Is it really the same thing?
        if variants(desc) != variants(best["item"]):
            # another row may be the right variant (a single, when the closest row is a twin)
            exact = [(h, sim(key, normkey(h["item"]))) for h in same_unit
                     if variants(h["item"]) == variants(desc) and relate(set(toks), set(tokens(h["item"]))) != "differs" and set(toks) & set(tokens(h["item"]))]
            if not exact:
                maybe(best, score, f"another variant ({', '.join(sorted(variants(desc) ^ variants(best['item'])))}): not the same item"); continue
            best, score = max(exact, key=lambda x: x[1])
        if best["supplier_row"]: maybe(best, score, "a supplier price-list row (a component): confirm before comparing with a finished item"); continue
        if sizes(best["item"]) and sizes(best["item"]) != sizes(desc):
            maybe(best, score, "size-dependent rate: " + ("the line gives no size" if not sizes(desc) else "sizes differ, pro-rata first (bif_prorata.py)")); continue
        # compare with rows that are the same item in the same variant, never a mix
        pool_all = [h for h in same_unit if set(tokens(h["item"])) == set(tokens(best["item"])) and not h["supplier_row"] and sizes(h["item"]) == sizes(best["item"])]
        verified = [h for h in pool_all if h["status"] == "VERIFIED"]
        pool = verified or pool_all
        med = statistics.median(h["rate"] for h in pool)
        dev = (l["rate"] - med) / med if med else 0
        strong = len(verified) >= 2
        ctx = {"ids": [h["id"] for h in pool][:6], "item": best["item"][:80], "n": len(pool), "against": "VERIFIED" if verified else "/".join(sorted({h["status"] or "?" for h in pool})),
               "stale_days": max([h["stale"] for h in pool if h["stale"]] or [0]) or None, "score": round(score, 2)}
        matches.append({"row": l["row"], "rate": l["rate"], "median": med, "dev": dev})
        devs.append(dev)
        if abs(dev) > band:
            flags.append({"row": l["row"], "desc": desc[:60], "rate": l["rate"], "median": med, "dev_pct": round(dev * 100, 1),
                          "rm_impact": round(abs((l.get("qty") or 0) * (l["rate"] - med)), 2), "evidence": "strong" if strong else "weak", "ratebase": ctx})
    shift = None
    if len(devs) >= 5:
        moved = [d for d in devs if abs(d) > band / 2]
        if moved and len(moved) / len(devs) >= 0.6:
            signs = [1 if d > 0 else -1 for d in moved]
            if abs(sum(signs)) / len(signs) >= 0.8:
                shift = {"direction": "UP" if sum(signs) > 0 else "DOWN", "median_shift_pct": round(statistics.median(moved) * 100, 1),
                         "affected": len(moved), "matched": len(devs)}
    flags.sort(key=lambda x: (x["evidence"] != "strong", -x["rm_impact"]))
    for i, f in enumerate(flags, 1): f["id"] = f"R{i:02d}"
    return flags, shift, gaps, matches, possible, skipped

def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(errors="replace")  # Windows consoles
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True); ap.add_argument("--json", required=True)
    ap.add_argument("--basis", default="SELL", choices=["SELL", "COST"]); ap.add_argument("--band", type=float, default=0.15)
    ap.add_argument("--subcon", default=""); ap.add_argument("--project", default=""); ap.add_argument("--tool")
    a = ap.parse_args()
    out = {"version": __version__, "basis": a.basis, "band": a.band, "subcon": a.subcon, "project": a.project,
           "source": None, "error": None, "matched": 0, "flags": [], "shift": None, "possible": [], "not_comparable": [], "gaps": []}
    lines = json.loads(Path(a.lines).read_text(encoding="utf-8"))["lines"]
    tool = Path(a.tool) if a.tool else where.knowledge()[0] / "ratebase.py"
    try:
        hist, out["source"] = load_ratebase(tool)
        out["flags"], out["shift"], out["gaps"], matches, out["possible"], out["not_comparable"] = check(lines, hist, a.basis, a.band)
        out["matched"] = len(matches)
    except RuntimeError as e:
        out["error"] = str(e)
    Path(a.json).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    if out["error"]:
        print(f"RATE CHECK DID NOT RUN: {out['error']}")
        print("Stage 03 must raise this as an ASK. Never price-check blind and never invent a benchmark.")
        sys.exit(1)
    s = out["source"]
    strong = [f for f in out["flags"] if f["evidence"] == "strong"]
    print(f"RATEBASE {s['file']} via {s['tool']} ({s['rates']} live rates) | COMPARED: {out['matched']} | BAND FLAGS: {len(strong)}"
          f"{' (+' + str(len(out['flags']) - len(strong)) + ' on weak evidence)' if len(out['flags']) > len(strong) else ''}"
          f" | POSSIBLE MATCHES: {len(out['possible'])} | NOT COMPARABLE: {len(out['not_comparable'])} | RATEBASE GAPS: {len(out['gaps'])}")
    for w in s["warnings"]: print(f"  {w}")
    if out["shift"]:
        sh = out["shift"]
        print(f"\nSYSTEMATIC SHIFT {sh['direction']} ~{sh['median_shift_pct']}% ({sh['affected']}/{sh['matched']} compared lines): probable pricelist revision. "
              f"ADVISE: request latest pricelist from {a.subcon or 'subcon'} BEFORE flagging individual lines.")
    for f in out["flags"]:
        c = f["ratebase"]
        print(f"[{f['id']}]{' WEAK EVIDENCE' if f['evidence'] == 'weak' else ''} row {f['row']}: {f['desc']} — RM{f['rate']:,.2f} vs ratebase median RM{f['median']:,.2f} ({f['dev_pct']:+}%, n={c['n']} {c['against']}"
              f"{', STALE ' + str(c['stale_days']) + 'd: verify current' if c['stale_days'] else ''}) RM impact ~{f['rm_impact']:,.2f}")
    if out["possible"]:
        print(f"\n{len(out['possible'])} possible match(es): a likely ratebase row that must be confirmed before any comparison (see rates.json, `possible`, each with its reason).")
    if out["gaps"]:
        print(f"\n{len(out['gaps'])} line(s) the ratebase does not hold. List them in the report under \"For the ratebase\"; mahareka-qs-agent stores them as PENDING on Zaim's word.")

if __name__ == "__main__":
    main()
