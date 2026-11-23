"""bq-error-checker v2.0: a full run through the four stages on a synthetic BQ (G10 + G12)."""
import json, re, subprocess, sys, tempfile, unittest
from pathlib import Path
from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).parent))
from fixtures import make_bq, make_history

SKILL = Path(__file__).resolve().parents[1] / "skills" / "bq-error-checker"
PY = sys.executable

def run(*args, ok=True):
    p = subprocess.run([PY, "-I", *map(str, args)], capture_output=True, text=True)
    if ok and p.returncode: raise AssertionError(p.stdout + p.stderr)
    return p

def set_front(path, **kv):
    t = path.read_text()
    for k, v in kv.items():
        t = re.sub(rf"^{k}:[^\n]*", f"{k}: {v}", t, count=1, flags=re.M)
    path.write_text(t)

class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.bq, self.hist = self.tmp / "test_bq.xlsx", self.tmp / "Rate_History.xlsx"
        make_bq(self.bq); make_history(self.hist)
        out = run(SKILL / "_tools/new_run.py", "--project", "T050", "--input", self.bq, "--root", self.tmp)
        self.run_dir = Path(out.stdout.strip())

    def gate(self, stage, ok=True):
        return run(SKILL / "_tools/gate.py", self.run_dir, stage, ok=ok)

    def test_full_run(self):
        r = self.run_dir
        # the stamp
        self.assertTrue((r / "00_input" / "test_bq.xlsx").is_file())
        for st in ("01_intake", "02_checks", "03_review", "04_report"): self.assertTrue((r / st).is_dir())
        self.assertIn("T050", (r / "RUN.md").read_text())

        # 01: blank intake fails; open questions fail; filled passes
        self.assertIn("not set", self.gate("01", ok=False).stdout)
        self.assertIn("stage 01", self.gate("02", ok=False).stdout)        # order enforced
        intake = r / "01_intake" / "intake.md"
        set_front(intake, sheet="BQ CLIENT", mode="1", basis="SELL", subcon="SMC", open_questions="1")
        self.assertIn("open question", self.gate("01", ok=False).stdout)
        set_front(intake, open_questions="0")
        self.gate("01")

        # 02: DEGRADED stops; INTACT passes after the scripts run
        (r / "02_checks" / "boot.txt").write_text("DEGRADED: qs_boot.py missing\n")
        run(SKILL / "_tools/check_bq.py", r / "00_input/test_bq.xlsx", "--sheet", "BQ CLIENT",
            "--json", r / "02_checks/findings.json")
        self.assertIn("DEGRADED", self.gate("02", ok=False).stdout)
        (r / "02_checks" / "boot.txt").write_text("QS BOOT: INTACT\n")
        out = run(SKILL / "_tools/rate_learn.py", "--lines", r / "02_checks/findings.json", "--history", self.hist,
                  "--project", "T050", "--subcon", "SMC", "--basis", "SELL",
                  "--out", r / "04_report/Rate_History_updated.xlsx", "--json", r / "02_checks/rates.json")
        self.assertIn("MEMORY layout: current", out.stdout)
        self.gate("02")

        # the regression answers (G10)
        f = json.loads((r / "02_checks/findings.json").read_text())["findings"]
        issues = {(x["row"], x["layer"]): x["issue"] for x in f}
        self.assertIn("Qty x Rate = 1,350.00 but Amount = 1,450.00", issues[(8, "A")])     # arithmetic
        self.assertIn("Sibling outlier: rate 72.00", issues[(6, "B")])                    # lesson 1 decimal typo
        self.assertIn("HIDDEN row carries Amount RM1,200.00", issues[(11, "A")])           # lesson 12
        self.assertIn("Non-standard UOM 'item'", issues[(10, "C")])
        self.assertFalse(any(x["row"] == 9 for x in f), "lesson 14: 'not included' must not be flagged")
        self.assertEqual([x["id"] for x in f], [f"F{i:02d}" for i in range(1, len(f) + 1)])

        rates = json.loads((r / "02_checks/rates.json").read_text())
        self.assertEqual(rates["layout"], "current")
        wardrobe = [x for x in rates["flags"] if x["row"] == 7]
        self.assertTrue(wardrobe and wardrobe[0]["dev_pct"] > 15, rates)                  # 690 vs median 530
        self.assertFalse(any(x["row"] == 4 for x in rates["flags"]))                      # 290 within band

        # memory: appended to INBOX only, curated RATES untouched, formula kept
        wb = load_workbook(r / "04_report/Rate_History_updated.xlsx")
        self.assertEqual(wb["RATES"].max_row, 6)
        self.assertEqual(wb["RATES"]["G6"].value, "=ROUND(E6*F6/5)*5")
        inbox = list(wb["INBOX"].iter_rows(min_row=2, values_only=True))
        self.assertTrue(inbox and all(row[10] in ("pending", "flagged") for row in inbox))
        self.assertTrue(any(row[1].startswith("Wardrobe") and row[10] == "flagged" for row in inbox))

        # 03: every id needs a decision
        review = r / "03_review" / "review.md"
        ids = [x["id"] for x in f] + [x["id"] for x in rates["flags"]]
        rows = "".join(f"| {i} | - | - | KEEP | - |\n" for i in ids[:-1])
        review.write_text(review.read_text().replace("|---|---|---|---|---|\n", "|---|---|---|---|---|\n" + rows))
        self.assertIn(ids[-1], self.gate("03", ok=False).stdout)
        review.write_text(review.read_text().replace(rows, rows + f"| {ids[-1]} | - | - | MAYBE | - |\n"))
        self.assertIn("decision must be", self.gate("03", ok=False).stdout)
        review.write_text(review.read_text().replace("MAYBE", "DROP"))
        self.gate("03")

        status = run(SKILL / "_tools/gate.py", r, "status").stdout
        self.assertRegex(status, r"01_intake\s+pass")
        self.assertRegex(status, r"03_review\s+pass")
        self.assertRegex(status, r"04_report\s+awaiting Zaim")

    def test_legacy_memory_still_read(self):
        from openpyxl import Workbook
        wb = Workbook(); ws = wb.active; ws.title = "RATES"
        ws.append(["ITEM_KEY", "DESCRIPTION", "UOM", "GRADE_SPEC", "BASIS", "RATE", "PROJECT", "SUBCON", "DATE", "STATUS", "NOTES"])
        ws.append(["base unit e1 melamine carcass", "Base unit E1 melamine carcass", "fr", "E1", "SELL", 295, "T", "SMC", "2026-01-01", "verified", ""])
        legacy = self.tmp / "legacy.xlsx"; wb.save(legacy)
        fj = self.tmp / "f.json"
        run(SKILL / "_tools/check_bq.py", self.bq, "--json", fj)
        out = run(SKILL / "_tools/rate_learn.py", "--lines", fj, "--history", legacy, "--project", "T",
                  "--out", self.tmp / "o.xlsx", "--json", self.tmp / "r.json")
        self.assertIn("MEMORY layout: legacy", out.stdout)
        self.assertGreaterEqual(json.loads((self.tmp / "r.json").read_text())["matched"], 1)

    def test_run_folders_never_collide(self):
        again = run(SKILL / "_tools/new_run.py", "--project", "T050", "--root", self.tmp).stdout.strip()
        self.assertNotEqual(again, str(self.run_dir))
        self.assertTrue(again.endswith("-2"))

if __name__ == "__main__":
    unittest.main()
