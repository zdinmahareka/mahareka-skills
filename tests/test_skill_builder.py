"""skill-builder 2.2 on Hermes: bootstrap, new_skill, skill_check and the staged registry. No Claude-Project paths."""
import hashlib, json, os, shutil, subprocess, sys, tempfile, time, unittest
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures import make_knowledge  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "skills" / "mahareka-skill-builder"
SCRIPTS = BUILDER / "scripts"

class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.know = self.tmp / "knowledge"; self.know.mkdir(); make_knowledge(self.know)
        self.skills = self.tmp / "skills"; self.skills.mkdir()
        self.home = self.tmp / "home"; self.home.mkdir()

    def run_tool(self, tool, *args, know=True):
        env = {**os.environ, "HOME": str(self.home), "USERPROFILE": str(self.home)}
        env.pop("MAHAREKA_KNOWLEDGE", None)
        if know: env["MAHAREKA_KNOWLEDGE"] = str(self.know)
        return subprocess.run([sys.executable, "-P", str(SCRIPTS / tool), *map(str, args)], capture_output=True, text=True, encoding="utf-8", env=env)

    def new(self, name, typ, *extra):
        return self.run_tool("new_skill.py", "--name", name, "--type", typ, "--purpose", "Checks a site diary against the programme",
                             "--triggers-en", "check the diary", "--triggers-bm", "semak diari tapak", "--skills", self.skills, *extra)

class Bootstrap(Base):
    def test_intact_with_registry_and_standard(self):
        p = self.run_tool("sb_boot.py", "--skills", ROOT / "skills")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("INTACT: safe to build and audit.", p.stdout)
        self.assertIn("SKILL_REGISTRY.xlsx    2 skills", p.stdout)
        self.assertIn("bq-error-checker                     [C] BLOCKED", p.stdout); self.assertIn("<-- BLOCKED", p.stdout)
        self.assertIn("chief-of-staff                       NOT REGISTERED", p.stdout)
        self.assertIn("mahareka-retired-skill               in the registry but NOT INSTALLED", p.stdout)
        self.assertIn("TYPE_A/B/C templates are not used on Hermes", p.stdout, "missing templates are not a blocker")

    def test_degraded_without_the_registry_or_the_standard(self):
        (self.know / "SKILL_REGISTRY.xlsx").unlink()
        p = self.run_tool("sb_boot.py", "--skills", ROOT / "skills")
        self.assertEqual(p.returncode, 1); self.assertIn("DEGRADED: do NOT build or audit from memory.", p.stdout); self.assertIn("- SKILL_REGISTRY.xlsx (KNOWLEDGE folder)", p.stdout)
        make_knowledge(self.know); (self.know / "MAHAREKA_STANDARD.md").unlink()
        p = self.run_tool("sb_boot.py"); self.assertEqual(p.returncode, 1); self.assertIn("- MAHAREKA_STANDARD.md (KNOWLEDGE folder)", p.stdout)

    def test_knowledge_is_found_the_hermes_way(self):
        # No variable set: ~/mahareka-knowledge, then the shared folder. Never a Claude path.
        p = self.run_tool("sb_boot.py", know=False); self.assertEqual(p.returncode, 1); self.assertIn("KNOWLEDGE: (not found)", p.stdout)
        shared = self.home / "mahareka-shared" / "Work" / "mahareka-knowledge"; shared.mkdir(parents=True); make_knowledge(shared)
        p = self.run_tool("sb_boot.py", know=False); self.assertEqual(p.returncode, 0, p.stdout); self.assertIn("[shared folder]", p.stdout)
        own = self.home / "mahareka-knowledge"; own.mkdir(); make_knowledge(own)
        p = self.run_tool("sb_boot.py", know=False); self.assertIn("[~/mahareka-knowledge]", p.stdout)

    def test_no_claude_project_path_anywhere(self):
        hits = [str(f.relative_to(BUILDER)) for f in BUILDER.rglob("*") if f.is_file() and f.suffix in (".py", ".md") and "/mnt/" in f.read_text(encoding="utf-8", errors="replace")]
        self.assertEqual(hits, [], "a /mnt/ path does not exist on Hermes")
        self.assertFalse((SCRIPTS / "skill_scaffold.py").exists(), "the Claude-Project scaffold is retired")

class NewSkill(Base):
    def check(self, tool, path):
        return subprocess.run([sys.executable, "-P", str(SCRIPTS / tool), str(path)], capture_output=True, text=True, encoding="utf-8")

    def test_each_shape_passes_the_checker_on_day_one(self):
        for typ, must in (("A", ["SKILL.md", "README.md"]), ("B", ["SKILL.md", "README.md", "_shared/rules.md"]),
                          ("C", ["SKILL.md", "README.md", "CONTEXT.md", "_shared/rules.md", "_templates/run/RUN.md", "_tools/new_run.py", "_tools/gate.py",
                                 "stages/01_intake/CONTEXT.md", "stages/02_work/CONTEXT.md", "stages/03_report/CONTEXT.md"])):
            name = f"mahareka-diary-check-{typ.lower()}"
            p = self.new(name, typ); dest = self.skills / "mahareka" / name
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr); self.assertIn(f"== {name}: PASS (0 blockers)", p.stdout)
            got = sorted(str(f.relative_to(dest)).replace(os.sep, "/") for f in dest.rglob("*") if f.is_file())
            self.assertEqual(got, sorted(must), typ)
            entry = (dest / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(f"name: {name}\n", entry); self.assertIn('description: Checks a site diary against the programme. Use whenever the user asks: check the diary — "semak diari tapak".', entry)
            self.assertEqual(self.check("icm_check.py", dest).returncode, 0)
            readme = (dest / "README.md").read_text(encoding="utf-8")
            self.assertTrue(readme.startswith(f"# {name}: README")); self.assertIn("## Purpose\nChecks a site diary against the programme\n", readme)
            self.assertEqual(len(list(dest.rglob("SKILL.md"))), 1, "only the entry is named SKILL.md")

    def test_custom_stages_are_numbered_in_order(self):
        p = self.new("mahareka-claim-pack", "C", "--stages", "collect,price,review,issue"); dest = self.skills / "mahareka" / "mahareka-claim-pack"
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertEqual(sorted(d.name for d in (dest / "stages").iterdir()), ["01_collect", "02_price", "03_review", "04_issue"])
        ctx = (dest / "CONTEXT.md").read_text(encoding="utf-8"); self.assertIn("4 stages", ctx); self.assertIn("| `stages/03_review/` |", ctx)
        self.assertIn("RUN/02_price/<file>", (dest / "stages" / "03_review" / "CONTEXT.md").read_text(encoding="utf-8"), "each stage reads the one before it")

    def test_refuses_an_existing_name_a_bad_name_or_no_purpose(self):
        self.assertEqual(self.new("mahareka-diary-check", "A").returncode, 0)
        (self.skills / "construction" / "mahareka-elsewhere").mkdir(parents=True); (self.skills / "construction" / "mahareka-elsewhere" / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        before = sorted(self.skills.rglob("*"))
        p = self.new("mahareka-diary-check", "B"); self.assertEqual(p.returncode, 1); self.assertIn("already exists", p.stderr); self.assertIn("Nothing was written", p.stderr)
        p = self.new("mahareka-elsewhere", "A"); self.assertEqual(p.returncode, 1, "a skill of that name in another category counts too")
        for bad in ("Diary Check", "diary-check", "mahareka_diary"): self.assertEqual(self.new(bad, "A").returncode, 1, bad)
        p = self.run_tool("new_skill.py", "--name", "mahareka-x-y", "--type", "A", "--purpose", "short", "--skills", self.skills); self.assertEqual(p.returncode, 1); self.assertIn("never fires", p.stderr)
        self.assertEqual(sorted(self.skills.rglob("*")), before, "a refusal writes nothing")

    def test_a_new_pipeline_runs_its_own_run_and_gate(self):
        self.assertEqual(self.new("mahareka-diary-run", "C").returncode, 0); dest = self.skills / "mahareka" / "mahareka-diary-run"
        src = self.tmp / "diary.txt"; src.write_text("day 1", encoding="utf-8")
        py = lambda *a: subprocess.run([sys.executable, "-P", *map(str, a)], capture_output=True, text=True, encoding="utf-8")
        p = py(dest / "_tools" / "new_run.py", "--project", "T001", "--input", src, "--root", self.tmp / "runs"); self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        run = next((self.tmp / "runs").rglob("01_intake")).parent
        p = py(dest / "_tools" / "gate.py", run, "01"); self.assertEqual(p.returncode, 1); self.assertEqual((run / "01_intake" / "check.md").read_text(encoding="utf-8").strip(), "fail: no output in this stage's folder")
        (run / "01_intake" / "intake.md").write_text("sheet: A", encoding="utf-8")
        self.assertEqual(py(dest / "_tools" / "gate.py", run, "01").returncode, 0)
        status = py(dest / "_tools" / "gate.py", run, "status").stdout
        self.assertRegex(status, r"01_intake\s+pass"); self.assertRegex(status, r"02_work\s+not checked")

class SkillCheck(Base):
    def test_audits_one_skill_all_skills_and_as_json(self):
        self.new("mahareka-diary-check", "A")
        p = self.run_tool("skill_check.py", self.skills / "mahareka" / "mahareka-diary-check"); self.assertEqual(p.returncode, 0, p.stdout + p.stderr); self.assertIn("mahareka-diary-check   [A", p.stdout)
        p = self.run_tool("skill_check.py", "--all", self.skills, "--json"); data = json.loads(p.stdout); self.assertEqual([d["name"] for d in data], ["mahareka-diary-check"])
        self.assertTrue(all("\\" not in f for f in data[0]["files"]), "file paths use / on every platform")
        p = self.run_tool("skill_check.py", "--all", self.tmp / "nothing-here"); self.assertEqual(p.returncode, 1); self.assertIn("STOP", p.stderr)

    def test_all_uses_the_recorded_skills_folder(self):
        self.new("mahareka-diary-check", "A")
        (self.home / ".mahareka").mkdir(); (self.home / ".mahareka" / "skills-dir").write_text(str(self.skills) + "\n", encoding="utf-8")
        p = self.run_tool("skill_check.py", "--all"); self.assertEqual(p.returncode, 0, p.stdout + p.stderr); self.assertIn("mahareka-diary-check", p.stdout)

    def test_a_stale_rule_names_its_owner_and_never_restates_the_value(self):
        self.new("mahareka-diary-check", "B"); rules = self.skills / "mahareka" / "mahareka-diary-check" / "_shared" / "rules.md"
        rules.write_text(rules.read_text(encoding="utf-8") + "\nSell rates are rounded to the nearest RM 5.\n", encoding="utf-8")
        p = self.run_tool("skill_check.py", self.skills / "mahareka" / "mahareka-diary-check")
        self.assertEqual(p.returncode, 1); line = next(l for l in p.stdout.splitlines() if "CROSS" in l)
        self.assertIn("a rule owned by mahareka-qs-agent", line); self.assertIn("rule R-ALL-42 (read the value from the owner; never restate it)", line)
        self.assertNotRegex(line.split("should be:")[1], r"\d+\s*-\s*\d+|0\.10|->", "the checker follows its own rule: no value of an owned rule")

    def test_missing_readme_is_a_blocker_and_resolved_conflicts_are_gone(self):
        self.new("mahareka-diary-check", "A"); (self.skills / "mahareka" / "mahareka-diary-check" / "README.md").unlink()
        p = self.run_tool("skill_check.py", self.skills / "mahareka" / "mahareka-diary-check"); self.assertEqual(p.returncode, 1); self.assertIn("M11        no README.md", p.stdout)
        # bq-error-checker v2.1: the second rate memory and the old rounding rule were removed on Zaim's decision (26 Nov 2026).
        p = self.run_tool("skill_check.py", ROOT / "skills" / "bq-error-checker")
        self.assertNotIn("CROSS", p.stdout, p.stdout); self.assertNotIn("P8", p.stdout, "it says what goes to Zaim")
        self.assertNotIn("P8", self.run_tool("skill_check.py", ROOT / "skills" / "chief-of-staff").stdout)
        self.assertEqual(self.run_tool("skill_check.py", BUILDER).returncode, 0, "the builder follows every rule it enforces")

class Registry(Base):
    def sha(self): return hashlib.sha256((self.know / "SKILL_REGISTRY.xlsx").read_bytes()).hexdigest()
    def rows(self, tab, name="SKILL_REGISTRY.staged.xlsx"):
        from openpyxl import load_workbook
        return [r for r in load_workbook(self.know / name)[tab].iter_rows(min_row=4, values_only=True) if r and r[0]]

    def test_updates_are_staged_append_only_and_the_registry_is_never_written(self):
        before, old = self.sha(), self.rows("PORTFOLIO", "SKILL_REGISTRY.xlsx")
        p = self.run_tool("registry.py", "add-skill", "--name", "mahareka-diary-check", "--type", "B", "--purpose", "Checks a site diary")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr); self.assertIn("ACTION ZAIM: replace SKILL_REGISTRY.xlsx in the KNOWLEDGE folder with SKILL_REGISTRY.staged.xlsx.", p.stdout)
        self.assertEqual(self.sha(), before, "the registry itself is untouched")
        rows = self.rows("PORTFOLIO"); self.assertEqual(rows[:2], old, "existing rows are kept as they were"); self.assertEqual(rows[2][:2], ("mahareka-diary-check", "B")); self.assertEqual(rows[2][7], "NEW")
        time.sleep(0.05)
        p = self.run_tool("registry.py", "log-audit", "--name", "mahareka-diary-check", "--verdict", "NEEDS WORK", "--warnings", "2", "--summary", "no decision authority")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(len(self.rows("PORTFOLIO")), 3, "a second update continues the staged copy"); self.assertEqual(self.rows("AUDIT_LOG")[0][1:5], ("mahareka-diary-check", "NEEDS WORK", 0, 2))
        self.run_tool("registry.py", "lesson", "--name", "mahareka-diary-check", "--what", "trigger never fired", "--cause", "no BM trigger", "--fix", "added", "--principle", "P0")
        self.assertEqual(self.rows("LESSONS")[0][1:3], ("mahareka-diary-check", "trigger never fired")); self.assertEqual(self.sha(), before)
        boot = self.run_tool("sb_boot.py"); self.assertEqual(boot.returncode, 0); self.assertIn("SKILL_REGISTRY.staged.xlsx is newer than the registry", boot.stdout)

    def test_new_skill_register_and_check_log_stage_rows(self):
        p = self.new("mahareka-diary-check", "A", "--register"); self.assertEqual(p.returncode, 0, p.stdout + p.stderr); self.assertIn("staged: PORTFOLIO row 6", p.stdout)
        p = self.run_tool("skill_check.py", self.skills / "mahareka" / "mahareka-diary-check", "--log"); self.assertIn("staged: AUDIT_LOG row 4", p.stdout)
        self.assertEqual(self.rows("AUDIT_LOG")[0][1], "mahareka-diary-check")

    def test_no_knowledge_folder_stops_loudly(self):
        p = self.run_tool("registry.py", "add-skill", "--name", "mahareka-a-b", "--type", "A", "--purpose", "A purpose here", know=False)
        self.assertNotEqual(p.returncode, 0); self.assertIn("STOP: the KNOWLEDGE folder was not found", p.stderr)

if __name__ == "__main__":
    unittest.main()
