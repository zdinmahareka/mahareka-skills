"""M11: every skill carries a README.md for people; the checker fails one that does not."""
import os, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "skills" / "mahareka-skill-builder" / "scripts" / "icm_check.py"
SECTIONS = ("Purpose", "What", "Why", "When", "How", "Using it", "Maintaining it")

def check(path):
    return subprocess.run([sys.executable, "-P", str(CHECK), str(path)], capture_output=True, text=True, encoding="utf-8")

def heads(path):
    return [h.strip() for h in re.findall(r"^##\s+(.+?)\s*$", path.read_text(encoding="utf-8"), re.M)]

class Readme(unittest.TestCase):
    def test_every_skill_has_one_with_its_sections(self):
        skills = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())
        self.assertGreaterEqual(len(skills), 3)
        for s in skills:
            readme = s / "README.md"
            self.assertTrue(readme.is_file(), f"{s.name} has no README.md")
            got = heads(readme)
            for name in SECTIONS:
                self.assertTrue(any(re.match(rf"{re.escape(name)}\b", h, re.I) for h in got), f"{s.name}/README.md has no '## {name}' section")
            text = readme.read_text(encoding="utf-8")
            self.assertTrue(text.startswith(f"# {s.name}"), f"{s.name}/README.md starts with the skill's name")
            for left in ("<skill-name>", "<x.y>", "<One or two", "<What it produces", "<The problem", "<What Zaim", "<The steps", "<Where the rules"):
                self.assertNotIn(left, text, f"{s.name}/README.md still has a placeholder from the starter")
            # A page for people holds no rate, secret or client figure.
            self.assertNotRegex(text, r"RM\s?\d{1,3}(?:,\d{3})+|\b\d{8,10}:[A-Za-z0-9_-]{30,}|-100\d{6,}", f"{s.name}/README.md holds a figure, token or chat id")

    def test_the_starter_has_the_same_sections(self):
        got = heads(ROOT / "skills" / "mahareka-skill-builder" / "assets" / "icm" / "README.md")
        self.assertEqual([h.split(" (")[0] for h in got], ["Purpose", "What it does", "Why it exists", "When it runs", "How it works", "Using it", "Maintaining it"])

    def test_checker_fails_a_skill_without_one_or_missing_a_section(self):
        base = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, base, ignore_errors=True)
        tmp = base / "chief-of-staff"
        shutil.copytree(ROOT / "skills" / "chief-of-staff", tmp)
        self.assertEqual(check(tmp).returncode, 0)
        readme = tmp / "README.md"; text = readme.read_text(encoding="utf-8")
        readme.write_text(text.replace("## Why it exists", "## Background").replace("## Maintaining it", "## Notes"), encoding="utf-8")
        p = check(tmp)
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn("BLOCKER M11: README.md has no '## Why ...' section", p.stdout)
        self.assertIn("WARN    M11: README.md has no '## Maintaining it' section", p.stdout)
        self.assertNotIn("no '## What", p.stdout)
        readme.unlink()
        p = check(tmp)
        self.assertEqual(p.returncode, 1)
        self.assertIn("M11: no README.md", p.stdout)

if __name__ == "__main__":
    unittest.main()
