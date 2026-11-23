#!/usr/bin/env python3
"""
Layer F — Rate Intelligence. Compares checked BQ lines (JSON from check_bq.py) against
Rate_History.xlsx, detects band deviations / systematic shifts / drift, appends new rates.
Usage:
  python rate_learn.py --lines findings.json --history Rate_History.xlsx --project N050 \
      --subcon SMC --basis SELL [--band 0.15] --out Rate_History_updated.xlsx [--json rates.json]
Matching is deliberately conservative (fuzzy desc match >= threshold); the judgment on
near-matches is stage 03's, using _shared/learning.md.

Memory layouts (v2.0 reads both, writes to the one it finds):
  current  (learning.md): sheets RATES + INBOX, columns ELEMENT | ITEM | SPEC/GRADE | UOM |
           COST RATE | MARKUP | SELL RATE | VENDOR | SOURCE/PROJECT | DATE | STATUS | NOTES.
           Reads RATES and INBOX; appends ONLY to INBOX; formulas are preserved.
  legacy   (v1.x): sheet RATES with ITEM_KEY | DESCRIPTION | UOM | GRADE_SPEC | BASIS | RATE | ...
"""
import json, argparse, re, statistics, datetime
from difflib import SequenceMatcher
from openpyxl import load_workbook, Workbook

STOP = {"to","supply","and","install","c/w","cw","the","of","for","with","in","at","complete","all","incl","including"}
DIM_RE = re.compile(r"\b\d+\s*(mm|m|ft|'|\")\b|\b[hwd]\s*[:=]?\s*\d+\b|\b\d{3,4}\b")
CURRENT_COLS = ["ELEMENT","ITEM","SPEC/GRADE","UOM","COST RATE","MARKUP","SELL RATE","VENDOR",
                "SOURCE/PROJECT","DATE","STATUS","NOTES"]
LEGACY_COLS = ["ITEM_KEY","DESCRIPTION","UOM","GRADE_SPEC","BASIS","RATE","PROJECT","SUBCON","DATE","STATUS","NOTES"]

def normkey(desc):
    d = str(desc).lower()
    d = DIM_RE.sub(" ", d)
    words = [w for w in re.split(r"[^a-z0-9]+", d) if w and w not in STOP]
    return " ".join(words[:8])

def sim(a,b): return SequenceMatcher(None,a,b).ratio()

def num(v):
    return float(v) if isinstance(v,(int,float)) and not isinstance(v,bool) else None

def header(ws):
    return {str(c.value).strip().upper(): i for i,c in enumerate(ws[1]) if c.value}

def load_history(path):
    """Returns (rows, wb_formulas, layout). rows: dicts with item_key, uom, basis, rate, status."""
    try:
        wbv = load_workbook(path, data_only=True)   # cached values (SELL RATE may be a formula)
        wbf = load_workbook(path)                   # formulas kept, for writing back
    except FileNotFoundError:
        return [], None, None
    sheets = [s for s in ("RATES","INBOX") if s in wbv.sheetnames] or [wbv.active.title]
    first = header(wbv[sheets[0]])
    layout = "current" if "COST RATE" in first or "SELL RATE" in first else "legacy"
    rows = []
    for name in (sheets if layout == "current" else sheets[:1]):
        ws = wbv[name]; idx = header(ws)
        for r in ws.iter_rows(min_row=2, values_only=True):
            if not any(v is not None for v in r): continue
            g = lambda k: r[idx[k]] if k in idx and idx[k] < len(r) else None
            if layout == "current":
                for basis, col in (("COST","COST RATE"),("SELL","SELL RATE")):
                    if num(g(col)) is not None:
                        rows.append({"item_key": g("ITEM"), "uom": g("UOM"), "basis": basis,
                                     "rate": num(g(col)), "status": g("STATUS")})
            else:
                rows.append({"item_key": g("ITEM_KEY") or g("DESCRIPTION"), "uom": g("UOM"),
                             "basis": g("BASIS"), "rate": num(g("RATE")), "status": g("STATUS")})
    return rows, wbf, layout

def append_rows(wb, layout, entries, basis, project, subcon, today):
    """entries: (desc, uom, rate, status, note). Current layout: INBOX only."""
    if layout == "current":
        if "INBOX" not in wb.sheetnames:
            wb.create_sheet("INBOX").append(CURRENT_COLS)
        ws = wb["INBOX"]; idx = header(ws)
        for desc, uom, rate, status, note in entries:
            row = [None] * max(len(idx), len(CURRENT_COLS))
            vals = {"ITEM": desc[:120], "UOM": uom, "VENDOR": subcon, "SOURCE/PROJECT": project,
                    "DATE": today, "STATUS": status, "NOTES": note,
                    ("SELL RATE" if basis == "SELL" else "COST RATE"): rate}
            for k, v in vals.items():
                if k in idx: row[idx[k]] = v
            ws.append(row)
    else:
        ws = wb["RATES"] if "RATES" in wb.sheetnames else wb.active
        for desc, uom, rate, status, note in entries:
            ws.append([normkey(desc), desc[:120], uom, "", basis, rate, project, subcon, today, status, note])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True); ap.add_argument("--history", required=True)
    ap.add_argument("--project", required=True); ap.add_argument("--subcon", default="")
    ap.add_argument("--basis", default="SELL", choices=["SELL","COST"])
    ap.add_argument("--band", type=float, default=0.15)
    ap.add_argument("--markup", type=float, default=1.5, help="derive SELL from COST history when no SELL match")
    ap.add_argument("--out", default="Rate_History_updated.xlsx")
    ap.add_argument("--json", help="write matches, flags (ids R01..) and shift for stage 03")
    a = ap.parse_args()

    lines = json.load(open(a.lines))["lines"]
    hist, wb, layout = load_history(a.history)
    today = datetime.date.today().isoformat()
    flags, matches, news, devs = [], [], [], []

    def cands_for(basis, l):
        return [h for h in hist if str(h.get("basis") or "").upper()==basis
                and str(h.get("uom") or "").lower()==str(l.get("unit") or "").lower()
                and str(h.get("status") or "").lower() in ("verified","pending")]

    for l in lines:
        if not l.get("rate") or not l.get("desc"): continue
        key = normkey(l["desc"])
        derived = False
        cands = cands_for(a.basis, l)
        best, score = None, 0
        for h in cands:
            s = sim(key, normkey(h.get("item_key") or ""))
            if s > score: best, score = h, s
        if (not best or score < 0.72) and a.basis == "SELL":
            for h in cands_for("COST", l):
                s = sim(key, normkey(h.get("item_key") or ""))
                if s > score and h.get("rate") is not None:
                    h2 = dict(h); h2["rate"] = round(h["rate"]*a.markup/5)*5  # derive sell, RM5 round (conflicts.md #2)
                    best, score, derived = h2, s, True
        if best and score >= 0.72:
            hkeys = normkey(best.get("item_key") or "")
            pool = cands_for("COST", l) if derived else cands
            same = [h for h in pool if sim(hkeys, normkey(h.get("item_key") or "")) >= 0.85
                    and h.get("rate") is not None]
            if derived:
                same = [dict(h, rate=round(h["rate"]*a.markup/5)*5) for h in same]
            rates = [h["rate"] for h in same if str(h.get("status") or "").lower()=="verified"] \
                    or [h["rate"] for h in same]
            if rates:
                med = statistics.median(rates)
                dev = (l["rate"]-med)/med if med else 0
                matches.append({"row":l["row"],"desc":l["desc"],"rate":l["rate"],"median":med,
                                "dev":dev,"n_hist":len(rates),"score":round(score,2)})
                if abs(dev) > a.band:
                    flags.append({"row":l["row"],"desc":l["desc"][:60],"rate":l["rate"],
                                  "median":med,"dev_pct":round(dev*100,1),
                                  "rm_impact":round(abs((l.get("qty") or 0)*(l["rate"]-med)),2),
                                  "history_n":len(rates),"derived":derived})
                devs.append(dev)
        else:
            news.append(l)

    # systematic shift detection
    shift = None
    if len(devs) >= 5:
        same_dir = [d for d in devs if abs(d) > a.band/2]
        if same_dir and len(same_dir)/len(devs) >= 0.6:
            signs = [1 if d>0 else -1 for d in same_dir]
            if abs(sum(signs)) / len(signs) >= 0.8:
                shift = {"direction":"UP" if sum(signs)>0 else "DOWN",
                         "median_shift_pct": round(statistics.median(same_dir)*100,1),
                         "affected": len(same_dir), "matched": len(devs)}

    # append news + deviating rates as pending/flagged (never straight into curated RATES)
    if wb is None:
        wb = Workbook(); ws = wb.active; ws.title = "RATES"; ws.append(CURRENT_COLS)
        wb.create_sheet("INBOX").append(CURRENT_COLS)
        wb.create_sheet("RESOLUTIONS").append(["DATE","PROJECT","FLAG","OUTCOME","LESSON"])
        layout = "current"
    entries = [(l["desc"], l.get("unit"), l["rate"], "pending", "auto-added: new item") for l in news]
    entries += [(f["desc"], next((l.get("unit") for l in lines if l["row"]==f["row"]), ""), f["rate"],
                 "flagged", f"deviates {f['dev_pct']}% vs median {f['median']}") for f in flags]
    append_rows(wb, layout, entries, a.basis, a.project, a.subcon, today)
    wb.save(a.out)

    flags.sort(key=lambda x: -x["rm_impact"])
    for i, f in enumerate(flags, 1): f["id"] = f"R{i:02d}"
    print(f"MEMORY layout: {layout} | MATCHED vs history: {len(matches)} | NEW items appended: {len(news)} | BAND FLAGS: {len(flags)}")
    if shift:
        print(f"\n⚠ SYSTEMATIC SHIFT {shift['direction']} ~{shift['median_shift_pct']}% "
              f"({shift['affected']}/{shift['matched']} matched lines) → probable pricelist revision. "
              f"ADVISE: request latest pricelist from {a.subcon or 'subcon'} BEFORE flagging individual lines.")
    for f in flags:
        print(f"[{f['id']}] row {f['row']}: {f['desc']} — RM{f['rate']:,.2f} vs hist median RM{f['median']:,.2f} "
              f"({f['dev_pct']:+}%, n={f['history_n']}{', DERIVED cost x' + str(a.markup) if f.get('derived') else ''}) RM impact ~{f['rm_impact']:,.2f}")
    print(f"\nUpdated memory: {a.out} (new/flagged rows = STATUS pending/flagged, awaiting Zaim verification)")
    if a.json:
        with open(a.json, "w") as fh:
            json.dump({"layout": layout, "matched": len(matches), "new": len(news), "flags": flags,
                       "shift": shift, "memory_out": a.out}, fh, indent=1, default=str)

if __name__ == "__main__":
    main()
