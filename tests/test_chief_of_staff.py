"""chief-of-staff: roster.py finds the roster Mission Control publishes and prints one staff card."""
import os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
TOOL = Path(__file__).resolve().parents[1] / "skills" / "chief-of-staff" / "_tools" / "roster.py"
ROSTER = """# Virtual Office roster (Mahareka)

Zaim ialah Boss. Peranan tidak memberi kuasa baru.

## Cara guna
- "Hakim, …" atau kerja QS → jawab sebagai Hakim.
- Apa-apa yang menghantar → plan dulu, tunggu kelulusan Zaim.

## Staf

### Hakim · QS Agent · Commercial & QS (Fulfillment)
- Watak: Teliti, nombor dulu.
- Skill dibina: bq-error-checker (MatDuo, Mattigo)
- Memori meja (diluluskan Zaim):
  - Wardrobe sliding minimum 4 kaki per set (2026-11-24)

### Amin · Finance Agent · Finance & Account (Business Support)
- Watak: Amanah dan tepat.
- Memori meja: sulit. Hanya dihantar bersama tugasan dari Mission Control.
"""

class Roster(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("MAHAREKA_")}
        self.env.update(HOME=self.home.as_posix(), USERPROFILE=str(self.home))

    def run_tool(self, *args, **extra):
        return subprocess.run([sys.executable, "-P", str(TOOL), *args], capture_output=True, text=True, encoding="utf-8", env={**self.env, **extra})

    def wiki(self, rel=".hermes/profiles/agent/shared-wiki", index="# Shared wiki (from Zaim, via Mission Control)\n"):
        d = self.home / rel; (d / "office").mkdir(parents=True)
        (d / "INDEX.md").write_text(index, encoding="utf-8"); (d / "office" / "roster.md").write_text(ROSTER, encoding="utf-8")
        return d / "office" / "roster.md"

    def test_no_roster_says_so(self):
        p = self.run_tool("--list")
        self.assertEqual(p.returncode, 2); self.assertIn("NO ROSTER", p.stdout)

    def test_finds_the_shared_wiki_copy_and_prints_one_card(self):
        f = self.wiki()
        self.assertEqual(self.run_tool("--path").stdout.strip(), str(f))
        self.assertEqual(self.run_tool("--list").stdout.strip().splitlines(), ["- Hakim · QS Agent · Commercial & QS (Fulfillment)", "- Amin · Finance Agent · Finance & Account (Business Support)"])
        out = self.run_tool("--staff", "hakim").stdout
        self.assertIn("## Cara guna", out); self.assertIn("### Hakim · QS Agent", out); self.assertIn("Wardrobe sliding", out)
        self.assertNotIn("Amin", out)                                             # only the card asked for
        self.assertIn("### Hakim", self.run_tool("--staff", "Commercial").stdout)   # a desk name works too
        p = self.run_tool("--staff", "nobody")
        self.assertEqual(p.returncode, 3); self.assertIn("- Hakim", p.stdout)

    def test_ignores_a_roster_that_is_not_in_the_shared_wiki(self):
        self.wiki(rel="Downloads/ARCHIVE/old", index="# Some other notes\n")          # not Mission Control's folder
        self.assertEqual(self.run_tool("--list").returncode, 2)
        f = self.wiki(rel="elsewhere/wiki")
        self.assertIn("### Amin", self.run_tool("--staff", "amin", MAHAREKA_ROSTER=str(f)).stdout)

if __name__ == "__main__":
    unittest.main()
