#!/usr/bin/env python3
"""
Mahareka BQ deterministic checker — Layers A (arithmetic), B (anomaly stats), C (conventions).
Usage: python check_bq.py <file.xlsx> [--sheet SHEETNAME] [--json findings.json]
Findings get ids F01.. (ranked by RM impact) for stage 03_review.
Outputs a findings report to stdout (and JSON if requested).
Flexible parser: auto-detects header row & columns by keyword; handles messy Mahareka workbooks.
"""
import sys, json, re, argparse, statistics
from openpyxl import load_workbook

QTY_KEYS = ["qty", "quantity", "kuantiti"]
UNIT_KEYS = ["unit", "uom"]
RATE_KEYS = ["rate", "kadar", "harga"]
AMT_KEYS = ["amount", "jumlah", "total (rm)", "amaun"]
DESC_KEYS = ["description", "keterangan", "particular", "perkara", "butiran"]
ITEM_KEYS = ["item", "no", "bil"]

VALID_UOM = {"m","mr","sqft","sqm","fr","nos","set","unit","pair","ls","lot","point",
             "trip","month","visit","%","p/pc","p/set","p/fr","p/sf","pc","pcs","no","no.","sq ft","sq m","psf","pfr"}
BAD_AMT_TEXT = ["ommit","omit","not included","exclude","n/a","na","-"]
TOTAL_WORDS = ["total","sub total","subtotal","jumlah","grand total","carried","c/f","b/f"]

def norm(s):
    return str(s).strip().lower() if s is not None else ""

def is_num(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool)

def find_header(ws, max_scan=15):
    """Find header row + column map by keyword scoring."""
    best = None
    for r in range(1, min(max_scan, ws.max_row)+1):
        cols, score = {}, 0
        for c in range(1, min(ws.max_column, 30)+1):
            v = norm(ws.cell(r,c).value)
            if not v: continue
            for key, name in [(QTY_KEYS,"qty"),(UNIT_KEYS,"unit"),(RATE_KEYS,"rate"),
                              (AMT_KEYS,"amount"),(DESC_KEYS,"desc"),(ITEM_KEYS,"item")]:
                if any(v.startswith(k) or v == k for k in key) and name not in cols:
                    cols[name] = c; score += (2 if name in ("qty","rate","amount") else 1)
        if score >= 4 and "amount" in cols and "qty" in cols:
            # dual-QTY fix: prefer the QTY nearest the UNIT/RATE/AMOUNT cluster
            if "rate" in cols:
                best_q, best_d = cols["qty"], abs(cols["qty"]-cols["rate"])
                for c2 in range(1, min(ws.max_column,30)+1):
                    if norm(ws.cell(r,c2).value).startswith("qty") and abs(c2-cols["rate"]) < best_d:
                        best_q, best_d = c2, abs(c2-cols["rate"])
                cols["qty"] = best_q
            if best is None or score > best[2]:
                best = (r, cols, score)
    return best

def detect_sheet(wb, prefer=None):
    if prefer and prefer in wb.sheetnames:
        return prefer
    # rank candidate sheets: has header + most data rows; flag legacy sheets
    ranked = []
    for name in wb.sheetnames:
        ws = wb[name]
        h = find_header(ws)
        if h:
            ranked.append((name, h, ws.max_row))
    if not ranked:
        return None
    ranked.sort(key=lambda x: -x[2])
    return ranked[0][0]

def parse_number(v):
    if is_num(v): return float(v)
    if isinstance(v,str):
        s = v.replace(",","").replace("RM","").strip()
        try: return float(s)
        except ValueError: return None
    return None

def check(path, sheet=None):
    wb = load_workbook(path, data_only=True)
    wbf = load_workbook(path, data_only=False)  # formulas view
    findings, info = [], {}
    target = detect_sheet(wb, sheet)
    if not target:
        return {"error":"No BQ-like sheet found (need header with QTY/RATE/AMOUNT). Specify --sheet."}, []
    info["sheet"] = target
    info["all_sheets"] = wb.sheetnames
    if len(wb.sheetnames) > 6:
        findings.append({"layer":"C","sev":"warn","row":None,"issue":
            f"Workbook has {len(wb.sheetnames)} sheets - possible legacy-sheet contamination. Only '{target}' audited.","rm":0})

    ws, wsf = wb[target], wbf[target]
    hr, cols, _ = find_header(ws, max_scan=15)
    info["header_row"], info["columns"] = hr, cols
    cQ,cR,cA = cols.get("qty"), cols.get("rate"), cols.get("amount")
    cU,cD,cI = cols.get("unit"), cols.get("desc"), cols.get("item")

    lines, section_rows = [], []
    n_hidden_amt = 0
    for r in range(hr+1, ws.max_row+1):
        if ws.row_dimensions[r].hidden:
            hv = parse_number(ws.cell(r,cA).value) if cA else None
            if hv: 
                n_hidden_amt += hv
                findings.append({"layer":"A","sev":"error","row":r,"issue":
                    f"HIDDEN row carries Amount RM{hv:,.2f} - hidden rows must be zero (inflates total)","rm":hv})
            continue  # hidden rows excluded (Zaim rule: inactive options hidden + zeroed)
        qty  = ws.cell(r,cQ).value if cQ else None
        rate = ws.cell(r,cR).value if cR else None
        amt  = ws.cell(r,cA).value if cA else None
        unit = ws.cell(r,cU).value if cU else None
        desc = ws.cell(r,cD).value if cD else None
        item = ws.cell(r,cI).value if cI else None
        d = norm(desc)
        # formula error check (Layer A)
        for c,label in [(cQ,"QTY"),(cR,"RATE"),(cA,"AMOUNT")]:
            if c:
                fv = wsf.cell(r,c).value
                sv = ws.cell(r,c).value
                if isinstance(sv,str) and sv.startswith("#"):
                    findings.append({"layer":"A","sev":"error","row":r,"issue":f"Formula error {sv} in {label}","rm":0})
        # total rows
        if d and any(w in d for w in TOTAL_WORDS):
            section_rows.append({"row":r,"desc":desc,"amount":parse_number(amt)})
            continue
        qn, rn, an = parse_number(qty), parse_number(rate), parse_number(amt)
        # 'Rate Only'/'not included' text in Amount is ACCEPTABLE (Zaim convention) - just exclude from math
        if qn is None and rn is None and an is None:
            continue  # header/blank/section title
        line = {"row":r,"item":item,"desc":str(desc)[:80] if desc else "","unit":norm(unit),
                "qty":qn,"rate":rn,"amount":an}
        lines.append(line)
        # Layer A: arithmetic
        if qn is not None and rn is not None and an is not None:
            expect = qn*rn
            if abs(expect-an) > 1.0:
                findings.append({"layer":"A","sev":"error","row":r,"issue":
                    f"Qty x Rate = {expect:,.2f} but Amount = {an:,.2f} ({line['desc'][:50]})","rm":abs(expect-an)})
        # Layer B basics
        if (rn in (None,0)) and an not in (None,0):
            findings.append({"layer":"B","sev":"warn","row":r,"issue":
                f"Amount {an:,.2f} with zero/blank rate ({line['desc'][:50]})","rm":an or 0})
        if rn not in (None,0) and qn not in (None,0) and an in (None,0):
            findings.append({"layer":"B","sev":"warn","row":r,"issue":
                f"Rate {rn:,.2f} & qty present but Amount blank/zero ({line['desc'][:50]})","rm":(qn or 0)*(rn or 0)})
        # Layer C: qty=0 ghost, UOM
        if qn == 0 and (rn or an):
            findings.append({"layer":"C","sev":"warn","row":r,"issue":f"Qty=0 ghost row ({line['desc'][:50]})","rm":0})
        # Layer C: non-SMC-scope items must have blank rate/amount
        if any(k in d for k in ["quartz","backsplash","solid surface"]) and (rn or an):
            findings.append({"layer":"C","sev":"warn","row":r,"issue":
                f"Non-SMC-scope item ('{line['desc'][:40]}') has Rate/Amount filled - Mahareka rule: qty only, rate & amount BLANK (Zaim sets rate)","rm":an or 0})
        u = norm(unit)
        if u and u not in VALID_UOM:
            sev = "error" if u=="item" else "warn"
            findings.append({"layer":"C","sev":sev,"row":r,"issue":f"Non-standard UOM '{unit}'","rm":0})

    # Layer A: subtotal & grand total reconciliation (best effort)
    if section_rows:
        priced = [l for l in lines if l["amount"] is not None]
        cursor = hr
        for s in section_rows:
            seg = [l["amount"] for l in priced if cursor < l["row"] < s["row"]]
            if seg and s["amount"] is not None and "grand" not in norm(s["desc"]):
                if abs(sum(seg)-s["amount"]) > 1.0:
                    findings.append({"layer":"A","sev":"error","row":s["row"],"issue":
                        f"Subtotal mismatch: lines sum {sum(seg):,.2f} vs stated {s['amount']:,.2f} ({str(s['desc'])[:40]})",
                        "rm":abs(sum(seg)-s["amount"])})
            cursor = s["row"]
        gt = [s for s in section_rows if "grand" in norm(s["desc"]) or norm(s["desc"]).strip()=="total"]
        subs = [s for s in section_rows if s not in gt and s["amount"] is not None]
        if gt and gt[-1]["amount"] is not None and subs:
            ssum = sum(s["amount"] for s in subs)
            if abs(ssum-gt[-1]["amount"]) > 1.0 and abs(sum(l["amount"] or 0 for l in lines)-gt[-1]["amount"]) > 1.0:
                findings.append({"layer":"A","sev":"warn","row":gt[-1]["row"],"issue":
                    f"Grand total {gt[-1]['amount']:,.2f} vs subtotal sum {ssum:,.2f} - verify structure","rm":abs(ssum-gt[-1]["amount"])})

    # Layer B: sibling sanity per UOM group (log-scale outliers), duplicates
    from collections import defaultdict
    groups = defaultdict(list)
    for l in lines:
        if l["rate"] and l["rate"]>0: groups[l["unit"]].append(l)
    for u,ls in groups.items():
        if len(ls) >= 4:
            rates = [l["rate"] for l in ls]
            med = statistics.median(rates)
            for l in ls:
                if med>0 and (l["rate"] <= med/3.5 or l["rate"] >= med*3.5):
                    findings.append({"layer":"B","sev":"warn","row":l["row"],"issue":
                        f"Sibling outlier: rate {l['rate']:,.2f}/{u} vs group median {med:,.2f} - possible decimal typo ({l['desc'][:50]})",
                        "rm":abs((l["qty"] or 0)*(med-l["rate"]))})
    seen = {}
    for l in lines:
        key = (norm(l["desc"]), l["unit"], l["rate"])
        if key in seen and l["desc"]:
            findings.append({"layer":"B","sev":"warn","row":l["row"],"issue":
                f"Possible duplicate of row {seen[key]} ({l['desc'][:50]})","rm":l["amount"] or 0})
        else: seen[key] = l["row"]

    info["n_lines"] = len(lines)
    info["n_sections"] = len(section_rows)
    info["grand_total_guess"] = section_rows[-1]["amount"] if section_rows else sum(l["amount"] or 0 for l in lines)
    findings.sort(key=lambda f: -(f["rm"] or 0))
    return info, findings, lines

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file"); ap.add_argument("--sheet"); ap.add_argument("--json")
    a = ap.parse_args()
    res = check(a.file, a.sheet)
    if isinstance(res, tuple) and len(res)==3:
        info, findings, lines = res
    else:
        print(json.dumps(res[0], indent=2)); sys.exit(1)
    for i, f in enumerate(findings, 1): f["id"] = f"F{i:02d}"   # stage 03 decides each id
    print(f"SHEET: {info['sheet']} | header row {info['header_row']} | {info['n_lines']} lines | "
          f"{info['n_sections']} total rows | grand ~RM {info['grand_total_guess'] or 0:,.2f}")
    print(f"All sheets: {info['all_sheets']}")
    if not findings: print("\nNO ISSUES FOUND (Layers A-C).")
    for f in findings:
        print(f"[{f['id']} {f['layer']}/{f['sev'].upper()}] row {f['row']}: {f['issue']}"
              + (f"  (RM impact ~{f['rm']:,.2f})" if f.get("rm") else ""))
    if a.json:
        with open(a.json,"w") as fh:
            json.dump({"info":info,"findings":findings,"lines":lines}, fh, indent=1, default=str)
        print(f"\nJSON written: {a.json}")

if __name__ == "__main__":
    main()
