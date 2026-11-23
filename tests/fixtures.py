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
