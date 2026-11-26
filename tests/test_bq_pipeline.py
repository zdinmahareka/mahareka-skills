"""bq-error-checker v2.0: a full run through the four stages on a synthetic BQ (G10 + G12)."""
import os, shutil, json, re, subprocess, sys, tempfile, unittest
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")  # child output on Windows consoles

sys.path.insert(0, str(Path(__file__).parent))
from fixtures import make_bq

SKILL = Path(__file__).resolve().parents[1] / "skills" / "bq-error-checker"
PY = sys.executable

def run(*args, ok=True):
    p = subprocess.run([PY, "-P", *map(str, args)], capture_output=True, text=True, encoding="utf-8")
    if ok and p.returncode: raise AssertionError(p.stdout + p.stderr)
    return p

def set_front(path, **kv):
    t = path.read_text(encoding="utf-8")
    for k, v in kv.items():
        t = re.sub(rf"^{k}:[^\n]*", f"{k}: {v}", t, count=1, flags=re.M)
    path.write_text(t, encoding="utf-8")

class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.bq = self.tmp / "test_bq.xlsx"
        make_bq(self.bq)
        out = run(SKILL / "_tools/new_run.py", "--project", "T050", "--input", self.bq, "--root", self.tmp)
        self.run_dir = Path(out.stdout.strip())

    def gate(self, stage, ok=True):
        return run(SKILL / "_tools/gate.py", self.run_dir, stage, ok=ok)

    def test_full_run(self):
        r = self.run_dir
        # the stamp
        self.assertTrue((r / "00_input" / "test_bq.xlsx").is_file())
        for st in ("01_intake", "02_checks", "03_review", "04_report"): self.assertTrue((r / st).is_dir())
        self.assertIn("T050", (r / "RUN.md").read_text(encoding="utf-8"))

        # 01: blank intake fails; open questions fail; filled passes
        self.assertIn("not set", self.gate("01", ok=False).stdout)
        self.assertIn("stage 01", self.gate("02", ok=False).stdout)        # order enforced
        intake = r / "01_intake" / "intake.md"
        set_front(intake, sheet="BQ CLIENT", mode="1", basis="SELL", subcon="SMC", open_questions="1")
        self.assertIn("open question", self.gate("01", ok=False).stdout)
        set_front(intake, open_questions="0")
        self.gate("01")

        # 02: DEGRADED stops; INTACT passes after the scripts run
        (r / "02_checks" / "boot.txt").write_text("DEGRADED: qs_boot.py missing\n", encoding="utf-8")
        run(SKILL / "_tools/check_bq.py", r / "00_input/test_bq.xlsx", "--sheet", "BQ CLIENT",
            "--json", r / "02_checks/findings.json")
        self.assertIn("DEGRADED", self.gate("02", ok=False).stdout)
        (r / "02_checks" / "boot.txt").write_text("QS BOOT: INTACT\n", encoding="utf-8")
        self.gate("02")
        # one ratebase (v2.1): stage 02 leaves no rate file of its own behind, and nothing is written for a second memory
        self.assertEqual(sorted(p.name for p in (r / "02_checks").iterdir()), ["boot.txt", "check.md", "findings.json"])
        self.assertEqual([p.name for p in (r / "04_report").iterdir() if p.suffix == ".xlsx"], [])

        # the regression answers (G10)
        f = json.loads((r / "02_checks/findings.json").read_text(encoding="utf-8"))["findings"]
        issues = {(x["row"], x["layer"]): x["issue"] for x in f}
        self.assertIn("Qty x Rate = 1,350.00 but Amount = 1,450.00", issues[(8, "A")])     # arithmetic
        self.assertIn("Sibling outlier: rate 72.00", issues[(6, "B")])                    # lesson 1 decimal typo
        self.assertIn("HIDDEN row carries Amount RM1,200.00", issues[(11, "A")])           # lesson 12
        self.assertIn("Non-standard UOM 'item'", issues[(10, "C")])
        self.assertFalse(any(x["row"] == 9 for x in f), "lesson 14: 'not included' must not be flagged")
        self.assertEqual([x["id"] for x in f], [f"F{i:02d}" for i in range(1, len(f) + 1)])

        # 03: every id needs a decision
        review = r / "03_review" / "review.md"
        ids = [x["id"] for x in f]
        rows = "".join(f"| {i} | - | - | KEEP | - |\n" for i in ids[:-1])
        review.write_text(review.read_text(encoding="utf-8").replace("|---|---|---|---|---|\n", "|---|---|---|---|---|\n" + rows), encoding="utf-8")
        self.assertIn(ids[-1], self.gate("03", ok=False).stdout)
        review.write_text(review.read_text(encoding="utf-8").replace(rows, rows + f"| {ids[-1]} | - | - | MAYBE | - |\n"), encoding="utf-8")
        self.assertIn("decision must be", self.gate("03", ok=False).stdout)
        review.write_text(review.read_text(encoding="utf-8").replace("MAYBE", "DROP"), encoding="utf-8")
        self.gate("03")
        # a rate finding is made in the review itself (R ids, against the one ratebase) and needs a valid decision too
        text = review.read_text(encoding="utf-8")
        review.write_text(text.replace(rows, rows + "| R01 | 7 | wardrobe rate above the ratebase band | LATER | - |\n"), encoding="utf-8")
        self.assertIn("decision must be", self.gate("03", ok=False).stdout)
        review.write_text(review.read_text(encoding="utf-8").replace("LATER", "KEEP"), encoding="utf-8")
        self.gate("03")

        status = run(SKILL / "_tools/gate.py", r, "status").stdout
        self.assertRegex(status, r"01_intake\s+pass")
        self.assertRegex(status, r"03_review\s+pass")
        self.assertRegex(status, r"04_report\s+awaiting Zaim")

    def test_one_ratebase_no_second_memory(self):
        """v2.1 (Zaim, 26 Nov 2026): the skill reads QS_RATEBASE through its owner and keeps no rate memory of its own."""
        self.assertFalse((SKILL / "_tools" / "rate_learn.py").exists())
        text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in SKILL.rglob("*") if p.is_file() and p.suffix in (".md", ".py"))
        for gone in ("Rate_History", "rate_learn", "rates.json", "MAHAREKA_RATE_HISTORY", "nearest RM5", "MROUND"):
            self.assertNotIn(gone, text, f"{gone} belongs to the retired second memory or the retired rounding rule")
        self.assertIn("rule R-ALL-42 (owned by `mahareka-qs-agent`", text, "the rounding rule is named by its owner, not restated")
        conflicts = (SKILL / "_shared" / "conflicts.md").read_text(encoding="utf-8")
        self.assertEqual(conflicts.count("RESOLVED in v2.1"), 2); self.assertIn('3. **"not included" annotation.**', conflicts); self.assertIn("Unresolved.", conflicts, "what was not decided stays declared")
        self.assertIn("**Always ask Zaim:**", (SKILL / "SKILL.md").read_text(encoding="utf-8"))

    def test_run_folders_never_collide(self):
        again = run(SKILL / "_tools/new_run.py", "--project", "T050", "--root", self.tmp).stdout.strip()
        self.assertNotEqual(again, str(self.run_dir))
        self.assertTrue(again.endswith("-2"))

if __name__ == "__main__":
    unittest.main()
