"""Hermes-only install: paths come from MAHAREKA_* or ~/, the old copy is backed up outside the skills folder."""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WHERE = ROOT / "skills" / "bq-error-checker" / "_tools" / "where.py"

class HermesInstall(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("MAHAREKA_")}
        self.env.update(HOME=str(self.home), USERPROFILE=str(self.home), MAHAREKA_SKIP_TESTS="1")

    def where(self, **extra):
        p = subprocess.run([sys.executable, "-I", str(WHERE), "--json"], capture_output=True, text=True,
                           env={**self.env, **extra})
        return json.loads(p.stdout)

    def test_where_defaults_and_overrides(self):
        w = self.where()
        self.assertEqual(w["knowledge"], str(self.home / "mahareka-knowledge"))
        self.assertEqual(w["runs"], str(self.home / "mahareka-runs"))
        self.assertIsNone(w["qs_boot"]); self.assertIsNone(w["rate_history"])
        k = self.home / "kb"; k.mkdir()
        (k / "qs_boot.py").write_text("print('INTACT')\n")
        (k / "Rate_History.xlsx").write_bytes(b"x")
        w = self.where(MAHAREKA_KNOWLEDGE=str(k))
        self.assertEqual(w["knowledge_found_by"], "env")
        self.assertTrue(w["qs_boot"].endswith("qs_boot.py"))
        self.assertTrue(w["rate_history"].endswith("Rate_History.xlsx"))

    def test_where_finds_files_already_on_the_machine(self):
        deep = self.home / "Documents" / "QS" / "ratebase"; deep.mkdir(parents=True)
        (deep / "qs_boot.py").write_text("print('INTACT')\n")
        (self.home / "Documents" / "QS" / "Rate_History_v3.xlsx").write_bytes(b"x")
        bk = self.home / "mc-backups" / "old"; bk.mkdir(parents=True); (bk / "qs_boot.py").write_text("")
        w = self.where()
        self.assertEqual(w["knowledge"], str(deep)); self.assertEqual(w["knowledge_found_by"], "search")
        self.assertEqual(w["rate_history"], str(self.home / "Documents" / "QS" / "Rate_History_v3.xlsx"))
        self.assertEqual(w["rate_history_found_by"], "search")

    @unittest.skipIf(os.environ.get("MAHAREKA_SKIP_TESTS"), "already inside an install run")
    def test_install_replaces_in_place_and_backs_up(self):
        skills = self.home / ".hermes" / "skills"
        old = skills / "construction" / "bq-error-checker"; old.mkdir(parents=True)
        (old / "SKILL.md").write_text("---\nname: bq-error-checker\ndescription: old\n---\nv1\n")
        (old / "references").mkdir(); (old / "references" / "x.md").write_text("old")
        p = subprocess.run(["bash", str(ROOT / "tools" / "install-hermes.sh"), str(skills)],
                           capture_output=True, text=True, env=self.env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("version **2.0**", (old / "SKILL.md").read_text())
        self.assertFalse((old / "references").exists(), "old files must not linger")
        self.assertTrue((skills / "mahareka" / "mahareka-skill-builder" / "SKILL.md").is_file())
        backups = list((self.home / "mc-backups" / "skills").glob("bq-error-checker-*"))
        self.assertEqual(len(backups), 1); self.assertTrue((backups[0] / "references" / "x.md").is_file())
        self.assertEqual(len(list(skills.rglob("bq-error-checker/SKILL.md"))), 1)
        self.assertIn("[install] done", p.stdout)

if __name__ == "__main__":
    unittest.main()
