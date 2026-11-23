"""icm_check.py: every skill in the repo passes; a broken pipeline is caught."""
import os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")  # child output on Windows consoles

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "skills" / "mahareka-skill-builder" / "scripts" / "icm_check.py"

def check(*args):
    return subprocess.run([sys.executable, "-P", str(CHECK), *map(str, args)], capture_output=True, text=True, encoding="utf-8")

class IcmCheck(unittest.TestCase):
    def test_repo_skills_pass(self):
        p = check("--all", ROOT / "skills")
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("bq-error-checker: PASS", p.stdout)
        self.assertIn("mahareka-skill-builder: PASS", p.stdout)

    def test_broken_pipeline_fails(self):
        base = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, base, ignore_errors=True)
        tmp = base / "bq-error-checker"
        shutil.copytree(ROOT / "skills" / "bq-error-checker", tmp)
        (tmp / "_templates" / "SKILL.md").write_text("---\nname: x\ndescription: y\n---\n", encoding="utf-8")
        c = tmp / "stages" / "03_review" / "CONTEXT.md"
        c.write_text(c.read_text(encoding="utf-8").replace("## Check", "## Verify"), encoding="utf-8")
        (tmp / "stages" / "04_report").rename(tmp / "stages" / "05_report")
        p = check(tmp)
        self.assertEqual(p.returncode, 1)
        self.assertIn("second SKILL.md", p.stdout)
        self.assertIn("03_review/CONTEXT.md has no '## Check'", p.stdout)
        self.assertIn("breaks the numbering", p.stdout)
        self.assertIn("path `stages/04_report/` does not exist".replace("path", "folder"), p.stdout)

if __name__ == "__main__":
    unittest.main()
