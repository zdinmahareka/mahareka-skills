"""bq-error-checker v2.0: a full run through the four stages on a synthetic BQ (G10 + G12)."""
import os, shutil, json, re, subprocess, sys, tempfile, unittest
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")  # child output on Windows consoles

sys.path.insert(0, str(Path(__file__).parent))
import hashlib
from fixtures import make_bq, make_ratebase, RATEBASE_STANDIN

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
        self.know = self.tmp / "knowledge"; self.know.mkdir(); make_ratebase(self.know)
        self.book = next(self.know.glob("QS_RATEBASE*.xlsx"))
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
        # Layer F must have run: without rates.json the gate stops
        self.assertIn("rates.json missing", self.gate("02", ok=False).stdout)
        before = hashlib.sha256(self.book.read_bytes()).hexdigest()
        out = run(SKILL / "_tools/rate_check.py", "--lines", r / "02_checks/findings.json", "--basis", "SELL", "--subcon", "SMC",
                  "--project", "T050", "--tool", self.know / "ratebase.py", "--json", r / "02_checks/rates.json")
        self.assertIn("RATEBASE QS_RATEBASE_v9.9_20260101.xlsx via ratebase.py vtest", out.stdout)
        self.gate("02")
        # one ratebase: read-only, nothing written beside it, no workbook of the skill's own
        self.assertEqual(hashlib.sha256(self.book.read_bytes()).hexdigest(), before, "the ratebase is never written")
        self.assertEqual(sorted(p.name for p in self.know.iterdir()), ["QS_RATEBASE_v9.9_20260101.xlsx", "qs_boot.py", "ratebase.py"], "not even a cache file is left in the owner's folder")
        self.assertEqual(sorted(p.name for p in (r / "02_checks").iterdir()), ["boot.txt", "check.md", "findings.json", "rates.json"])
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

        # Layer F against the one ratebase
        rates = json.loads((r / "02_checks/rates.json").read_text(encoding="utf-8"))
        self.assertIsNone(rates["error"]); self.assertEqual(rates["source"]["file"], "QS_RATEBASE_v9.9_20260101.xlsx")
        wardrobe = [x for x in rates["flags"] if x["row"] == 7]
        self.assertTrue(wardrobe and wardrobe[0]["dev_pct"] > 15, rates)                  # 690 vs median 530
        self.assertEqual(wardrobe[0]["median"], 530, "the SUPERSEDED 900 is never compared")
        self.assertEqual((wardrobe[0]["ratebase"]["against"], wardrobe[0]["ratebase"]["n"], wardrobe[0]["ratebase"]["ids"]), ("VERIFIED", 2, ["BIF-003", "BIF-004"]))
        self.assertEqual(wardrobe[0]["ratebase"]["stale_days"], 400, "a stale ratebase rate is said so")
        self.assertFalse(any(x["row"] in (4, 5, 8) for x in rates["flags"]), "290 vs 295, 310 vs the owner's 300, 450 vs 440: inside the band")
        self.assertTrue(any("Feature wall paint" in g["desc"] for g in rates["gaps"]), "what the ratebase does not hold is a gap, not a flag")
        self.assertEqual([x["id"] for x in rates["flags"]], [f"R{i:02d}" for i in range(1, len(rates["flags"]) + 1)])

        # 03: every id needs a decision
        review = r / "03_review" / "review.md"
        ids = [x["id"] for x in f] + [x["id"] for x in rates["flags"]]
        rows = "".join(f"| {i} | - | - | KEEP | - |\n" for i in ids[:-1])
        review.write_text(review.read_text(encoding="utf-8").replace("|---|---|---|---|---|\n", "|---|---|---|---|---|\n" + rows), encoding="utf-8")
        self.assertIn(ids[-1], self.gate("03", ok=False).stdout)
        review.write_text(review.read_text(encoding="utf-8").replace(rows, rows + f"| {ids[-1]} | - | - | MAYBE | - |\n"), encoding="utf-8")
        self.assertIn("decision must be", self.gate("03", ok=False).stdout)
        review.write_text(review.read_text(encoding="utf-8").replace("MAYBE", "DROP"), encoding="utf-8")
        self.gate("03")

        status = run(SKILL / "_tools/gate.py", r, "status").stdout
        self.assertRegex(status, r"01_intake\s+pass")
        self.assertRegex(status, r"03_review\s+pass")
        self.assertRegex(status, r"04_report\s+awaiting Zaim")

    def test_one_ratebase_no_second_memory(self):
        """v2.1 (Zaim, 26 Nov 2026): the skill reads QS_RATEBASE through its owner and keeps no rate memory of its own."""
        self.assertFalse((SKILL / "_tools" / "rate_learn.py").exists())
        text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in SKILL.rglob("*") if p.is_file() and p.suffix in (".md", ".py"))
        for gone in ("Rate_History", "rate_learn", "MAHAREKA_RATE_HISTORY", "nearest RM5", "MROUND", "load_workbook", ".save("):
            self.assertNotIn(gone, text.replace((SKILL / "_tools" / "check_bq.py").read_text(encoding="utf-8"), ""), f"{gone}: the skill keeps no rate workbook, opens none itself, and restates no owned rule")
        self.assertIn("rule R-ALL-42 (owned by `mahareka-qs-agent`", text, "the rounding rule is named by its owner, not restated")
        conflicts = (SKILL / "_shared" / "conflicts.md").read_text(encoding="utf-8")
        self.assertEqual(conflicts.count("RESOLVED in v2.1"), 2); self.assertIn('3. **"not included" annotation.**', conflicts); self.assertIn("Unresolved.", conflicts, "what was not decided stays declared")
        self.assertIn("**Always ask Zaim:**", (SKILL / "SKILL.md").read_text(encoding="utf-8"))

    def test_rate_check_is_loud_when_the_ratebase_cannot_be_read(self):
        fj, rj = self.tmp / "f.json", self.tmp / "r.json"
        run(SKILL / "_tools/check_bq.py", self.bq, "--json", fj)
        # no rate authority on this machine
        p = run(SKILL / "_tools/rate_check.py", "--lines", fj, "--tool", self.tmp / "nowhere" / "ratebase.py", "--json", rj, ok=False)
        self.assertIn("RATE CHECK DID NOT RUN", p.stdout); self.assertIn("Never price-check blind", p.stdout)
        out = json.loads(rj.read_text(encoding="utf-8")); self.assertIn("ratebase.py not found", out["error"]); self.assertEqual((out["flags"], out["gaps"]), ([], []))
        # the master workbook is missing: the owner's tool stops, and that is reported, not guessed around
        self.book.unlink()
        p = run(SKILL / "_tools/rate_check.py", "--lines", fj, "--tool", self.know / "ratebase.py", "--json", rj, ok=False)
        self.assertIn("the ratebase could not be opened: No QS_RATEBASE*.xlsx found", json.loads(rj.read_text(encoding="utf-8"))["error"])
        # a tool without the functions this check reads through: stop, never open the workbook directly
        make_ratebase(self.know, tool="__version__ = '0.1'\ndef find(q): return []\n")
        p = run(SKILL / "_tools/rate_check.py", "--lines", fj, "--tool", self.know / "ratebase.py", "--json", rj, ok=False)
        self.assertIn("ratebase.py v0.1 has no open_rb, rate_tabs, rows()", json.loads(rj.read_text(encoding="utf-8"))["error"])

    def test_rate_check_on_cost_basis_and_a_pricelist_shift(self):
        # a subcon quote (COST) where every line moved up about 10%: one advisory, not seven accusations
        lines = [{"row": 10 + i, "desc": "Wall unit E1 melamine", "unit": "fr", "rate": 222 + i, "qty": 2} for i in range(6)]
        fj, rj = self.tmp / "f.json", self.tmp / "r.json"
        fj.write_text(json.dumps({"lines": lines}), encoding="utf-8")
        p = run(SKILL / "_tools/rate_check.py", "--lines", fj, "--basis", "COST", "--subcon", "SMC", "--tool", self.know / "ratebase.py", "--json", rj)
        out = json.loads(rj.read_text(encoding="utf-8"))
        self.assertEqual(out["matched"], 6); self.assertEqual(out["flags"], [], "about 11% is inside the 15% band")
        self.assertEqual((out["shift"]["direction"], out["shift"]["affected"]), ("UP", 6)); self.assertIn("request latest pricelist from SMC", p.stdout)
        # a tighter band, asked for by Zaim, flags them
        run(SKILL / "_tools/rate_check.py", "--lines", fj, "--basis", "COST", "--band", "0.05", "--tool", self.know / "ratebase.py", "--json", rj)
        self.assertEqual(len(json.loads(rj.read_text(encoding="utf-8"))["flags"]), 6)

    def test_rate_check_compares_only_what_is_surely_the_same_item(self):
        """The first run on the real ratebase (26 Nov 2026) flagged wrong matches and missed rates that were there. Each case here is one of those."""
        L = lambda row, desc, unit, rate, qty=1: {"row": row, "desc": desc, "unit": unit, "rate": rate, "qty": qty}
        lines = [L(1, "Eyeball downlight", "pc", 100, 4), L(2, "Open colour carcass", "fr", 300), L(3, "Fridge unit", "fr", 600), L(4, "Drawer 3 tier", "set", 380, 2),
                 L(5, "Fluted panel, S&I", "sqft", 20), L(6, "Pantry cabinet", "fr", 500), L(7, "13A single SSO", "pc", 70), L(8, "Floor protection", "ls", 900),
                 L(9, "Baby ceiling fan + wiring", "nos", 250), L(10, "Renovation bin", "nos", 350), L(11, "Tall unit E1 melamine", "fr", 72), L(12, "Twin eyeball downlight", "nos", 92)]
        fj, rj = self.tmp / "f.json", self.tmp / "r.json"; fj.write_text(json.dumps({"lines": lines}), encoding="utf-8")
        p = run(SKILL / "_tools/rate_check.py", "--lines", fj, "--basis", "SELL", "--tool", self.know / "ratebase.py", "--json", rj)
        out = json.loads(rj.read_text(encoding="utf-8"))
        flags = {f["row"]: f for f in out["flags"]}; maybe = {m["row"]: m for m in out["possible"]}
        # a variant is never pooled with another: a single against the single, the 3-tier against the 3-tiers
        self.assertEqual(sorted(flags), [1, 4])
        self.assertEqual((flags[1]["ratebase"]["ids"], flags[1]["evidence"]), (["EL-038"], "weak"), "unit pc is nos; the twin is not in the median; one row is weak evidence")
        self.assertEqual((flags[4]["ratebase"]["ids"], flags[4]["median"], flags[4]["evidence"]), (["BIF-044", "BIF-045"], 810, "strong"))
        self.assertEqual([f["id"] for f in out["flags"]], ["R01", "R02"]); self.assertEqual(out["flags"][0]["row"], 4, "strong evidence first")
        self.assertNotIn(12, flags, "the twin is compared with the twin, and is inside the band")
        # a likely row that must be confirmed first is never a flag
        self.assertEqual(sorted(maybe), [2, 3, 5, 6, 7, 11])
        self.assertIn("supplier price-list row", maybe[2]["why"]); self.assertEqual(maybe[2]["ratebase"]["id"], "BIF-121")
        self.assertIn("size-dependent rate: the line gives no size", maybe[3]["why"]); self.assertIn("size-dependent", maybe[5]["why"])
        self.assertIn("row is more specific", maybe[6]["why"]); self.assertEqual(maybe[6]["ratebase"]["id"], "BIF-130")
        self.assertIn("different words", maybe[7]["why"]); self.assertEqual(maybe[7]["ratebase"]["id"], "EL-010", "SSO is read as switch socket outlet, pc as nos")
        self.assertRegex(maybe[11]["why"], r"different words \((tall / wall|wall / tall)\)", "a tall unit is not a wall unit, however alike they are spelt")
        self.assertEqual({n["row"]: n["why"] for n in out["not_comparable"]}, {8: "lump sum", 9: "composite line (several works in one rate)"})
        self.assertEqual([g["row"] for g in out["gaps"]], [10], "only what is really missing is a gap")
        self.assertIn("COMPARED: 3 | BAND FLAGS: 1 (+1 on weak evidence) | POSSIBLE MATCHES: 6 | NOT COMPARABLE: 2 | RATEBASE GAPS: 1", p.stdout)
        self.assertIn("[R02] WEAK EVIDENCE row 1", p.stdout)

    def test_run_folders_never_collide(self):
        again = run(SKILL / "_tools/new_run.py", "--project", "T050", "--root", self.tmp).stdout.strip()
        self.assertNotEqual(again, str(self.run_dir))
        self.assertTrue(again.endswith("-2"))

if __name__ == "__main__":
    unittest.main()
