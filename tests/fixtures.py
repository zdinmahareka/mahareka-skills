"""Synthetic BQ and registry for regression tests. No client data."""
from openpyxl import Workbook

def make_bq(path):
    wb = Workbook(); ws = wb.active; ws.title = "BQ CLIENT"
    ws.append(["MAHAREKA CONSTRUCTION — TEST BQ"]); ws.append([])
    ws.append(["ITEM", "DESCRIPTION", "QTY", "UNIT", "RATE", "AMOUNT"])           # header row 3
    rows = [
        ("a)", "Base unit E1 melamine carcass", 10, "fr", 290, 2900),           # r4 ok
        ("b)", "Wall unit E1 melamine", 8, "fr", 310, 2480),                    # r5 ok
        ("c)", "Tall unit E1 melamine", 4, "fr", 72, 288),                      # r6 decimal typo (lesson 1)
        ("d)", "Wardrobe swing door E1", 6, "fr", 690, 4140),                   # r7 ok
        ("e)", "Shoe cabinet E1", 3, "fr", 450, 1450),                          # r8 arithmetic: 1350 != 1450
        ("f)", "Quartz top 20mm", 12, "fr", None, "not included"),              # r9 annotation, must not flag
        ("g)", "Feature wall paint", 1, "item", 800, 800),                      # r10 UOM 'item'
    ]
    for r in rows: ws.append(list(r))
    ws.append(["h)", "Herringbone SPC option", 100, "sqft", 12, 1200])          # r11 hidden with amount
    ws.row_dimensions[11].hidden = True
    ws.append([None, "TOTAL AMOUNT", None, None, None, 2900 + 2480 + 288 + 4140 + 1450 + 800])  # r12
    wb.save(path)

REGISTRY_TABS = {
    "README": [], "PORTFOLIO": ["SKILL", "TYPE", "SUBTYPE", "PURPOSE", "SKILL LAYER", "PROJECT LAYER", "MEMORY", "HEALTH", "BLOCKERS", "LAST AUDIT", "NOTES"],
    "PATTERNS": ["ID", "PATTERN", "PROBLEM IT SOLVES", "IMPLEMENTATION", "USE WHEN", "PROVEN IN"],
    "LESSONS": ["DATE", "SKILL", "WHAT HAPPENED", "ROOT CAUSE", "FIX", "PRINCIPLE"], "GATES": ["GATE", "CHECK", "APPLIES TO", "HOW VERIFIED"],
    "TRIGGERS": ["DOMAIN", "ENGLISH", "BAHASA MALAYSIA", "CASUAL / REAL TYPING", "NOTE"],
    "AUDIT_LOG": ["DATE", "SKILL", "VERDICT", "BLOCKERS", "WARNINGS", "INFO", "SUMMARY"],
}

def make_knowledge(folder):
    """A synthetic KNOWLEDGE folder: the registry in its real shape (title row 1, headings row 3, data from row 4) and a stand-in standard."""
    wb = Workbook(); wb.remove(wb.active)
    for tab, cols in REGISTRY_TABS.items():
        ws = wb.create_sheet(tab); ws.cell(1, 1, f"{tab} (synthetic)")
        for c, h in enumerate(cols, 1): ws.cell(3, c, h)
    wb["PORTFOLIO"].append(["bq-error-checker", "C", "C2 auditor", "audits BQ documents", "x", "x", "x", "BLOCKED", 2, "2026-07-30", "synthetic"])
    wb["PORTFOLIO"].append(["mahareka-retired-skill", "A", "", "retired", "x", "x", "x", "SUPERSEDED", 0, "2026-07-30", "synthetic"])
    wb["PATTERNS"].append(["P1", "Two layers", "x", "x", "x", "x"]); wb["GATES"].append(["G1", "archetype justified", "all", "read"])
    wb.save(folder / "SKILL_REGISTRY.xlsx")
    (folder / "MAHAREKA_STANDARD.md").write_text("# Mahareka standard (synthetic stand-in)\n", encoding="utf-8")

RATEBASE_HEADERS = ["ID", "ITEM", "SPEC/NOTE", "UOM", "MATERIAL", "LABOUR", "EQUIPMENT", "OTHER", "SUBCON", "ALL-IN", "MARKUP", "SELL", "VENDOR/SOURCE", "PROJECT", "DATE", "STATUS"]
# A stand-in for mahareka-qs-agent's ratebase.py: the same public functions (open_rb, rate_tabs,
# rows, freshness) over a synthetic workbook. The real tool is never copied into this repo.
RATEBASE_STANDIN = '''"""Stand-in for the QS agent's ratebase.py (tests only): same public functions, synthetic rates."""
import glob, os, sys
from openpyxl import load_workbook
__version__ = "test"
HERE = os.path.dirname(os.path.abspath(__file__))
def open_rb(path=None):
    hits = sorted(glob.glob(os.path.join(HERE, "QS_RATEBASE*.xlsx")))
    if not hits: sys.exit("No QS_RATEBASE*.xlsx found in: " + HERE)
    print("WARNING: synthetic ratebase (tests)")
    return load_workbook(hits[-1]), hits[-1]
def rate_tabs(wb): return [s for s in wb.sheetnames if s != "README"]
def rows(ws):
    hdr = [c.value for c in ws[3]]
    for r in ws.iter_rows(min_row=4, values_only=True):
        if r[0] is None and r[1] is None: continue
        d = dict(zip(hdr, r))
        if d.get("SELL") is None and d.get("ALL-IN") and d.get("MARKUP"): d["SELL"] = d["ALL-IN"] * d["MARKUP"]   # the owner computes sell
        yield d
def freshness(r):
    old = r.get("ID") == "BIF-003"
    return None, (400 if old else 10), ("STALE" if old else "FRESH")
'''

def make_ratebase(folder, tool=RATEBASE_STANDIN):
    """A synthetic KNOWLEDGE folder for the rate authority: qs_boot.py, the stand-in ratebase.py and a small QS_RATEBASE."""
    wb = Workbook(); ws = wb.active; ws.title = "BIF"
    ws.append(["BUILT-IN FURNITURE (synthetic)"]); ws.append([]); ws.append(RATEBASE_HEADERS)
    for rid, item, allin, markup, sell, status in [
        ("BIF-001", "Base unit E1 melamine carcass", None, None, 290, "VERIFIED"),
        ("BIF-002", "Base unit E1 melamine carcass", None, None, 300, "VERIFIED"),
        ("BIF-003", "Wardrobe swing door E1", None, None, 520, "VERIFIED"),
        ("BIF-004", "Wardrobe swing door E1", None, None, 540, "VERIFIED"),
        ("BIF-005", "Wardrobe swing door E1", None, None, 900, "SUPERSEDED"),          # kept forever, never compared
        ("BIF-006", "Wall unit E1 melamine", 200, 1.5, None, "VERIFIED"),              # sell comes from the owner's tool
        ("BIF-007", "Shoe cabinet E1", None, None, 440, "PENDING"),
    ]:
        ws.append([rid, item, "E1", "fr", None, None, None, None, allin, allin, markup, sell, "SMC", "T001", "2026-06-01", status])
    # the cases the first run on the real ratebase got wrong (26 Nov 2026): variants, supplier rows, sizes, wording, units
    for rid, item, unit, sell, status in [
        ("BIF-008", "Fridge unit H810 D580 loaded", "fr", 400, "VERIFIED"),
        ("BIF-044", "Drawer 3-tier", "set", 800, "VERIFIED"), ("BIF-045", "Drawer 3-tier", "set", 820, "VERIFIED"), ("BIF-046", "Drawer 2-tier", "set", 500, "VERIFIED"),
        ("BIF-072", "TV fluted panel D<100", "sqft", 50, "BUDGETARY"),
        ("BIF-121", "SMC open colour carcass - kitchen", "fr", 100, "VERIFIED"),
        ("BIF-130", "Pantry cabinet c/w swing door and soft closing hinges", "fr", 480, "VERIFIED"),
    ]:
        ws.append([rid, item, None, unit, None, None, None, None, None, None, None, sell, "SMC pricelist" if rid == "BIF-121" else "Workshop", "T002", "2026-06-01", status])
    el = wb.create_sheet("EL"); el.append(["ELECTRICAL (synthetic)"]); el.append([]); el.append(RATEBASE_HEADERS)
    for rid, item, sell in [("EL-004", "Twin eyeball downlight", 90), ("EL-038", "Eyeball downlight", 40), ("EL-010", "13A switch socket outlet - Vivace E", 60)]:
        el.append([rid, item, None, "nos", None, None, None, None, None, None, None, sell, "Hafiz", "T003", "2026-06-01", "VERIFIED"])
    wb.create_sheet("README").append(["RB v9.9 | synthetic"])
    wb.save(folder / "QS_RATEBASE_v9.9_20260101.xlsx")
    (folder / "ratebase.py").write_text(tool, encoding="utf-8")
    (folder / "qs_boot.py").write_text("print('QS BOOT: INTACT')\n", encoding="utf-8")
