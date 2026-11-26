"""Synthetic BQ and rate memory for regression tests. No client data."""
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

def make_history(path):
    wb = Workbook(); ws = wb.active; ws.title = "RATES"
    cols = ["ELEMENT", "ITEM", "SPEC/GRADE", "UOM", "COST RATE", "MARKUP", "SELL RATE", "VENDOR",
            "SOURCE/PROJECT", "DATE", "STATUS", "NOTES"]
    ws.append(cols)
    for i, (item, sell) in enumerate([("Base unit E1 melamine carcass", 290), ("Base unit E1 melamine carcass", 300),
                                      ("Wardrobe swing door E1", 520), ("Wardrobe swing door E1", 540)], start=2):
        ws.append(["BIF", item, "E1", "fr", None, None, sell, "SMC", "T001", "2026-06-01", "verified", ""])
    ws.append(["BIF", "Wall unit E1 melamine", "E1", "fr", 200, 1.5, "=ROUND(E6*F6/5)*5", "SMC", "T002",
               "2026-07-01", "verified", "formula row"])
    wb.create_sheet("INBOX").append(cols)
    wb.create_sheet("RESOLUTIONS").append(["DATE", "PROJECT", "FLAG", "OUTCOME", "LESSON"])
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
