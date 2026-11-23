"""A reshape moves rules verbatim. These v1.1 safety lines must stay somewhere in the skill."""
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skills" / "bq-error-checker"
KEPT = [
    "INTACT but FLAGGED", "Never\n   hand-calculate as a silent fallback; use `ratebase.py`, `bif_prorata.py`, `bur_calc.py`.",
    "Never price-check blind, never invent an assumption silently, never\n   invent a benchmark.",
    "**ratebase gap**", "Never quote a rate from this skill's own files.",
    "False accusations against a subcon = 0\n  tolerance.", "PRO-RATA FIRST",
    "Never blend the modes", "Gate pending", "NEVER approve silently",
    "Do not fix any of them as a side effect of another task.",
    "suspect revision FIRST, never accuse first",
]

class RulesKept(unittest.TestCase):
    def test_v11_safety_lines_present(self):
        text = "\n".join(p.read_text(encoding="utf-8") for p in SKILL.rglob("*.md"))
        missing = [k for k in KEPT if k not in text]
        self.assertEqual(missing, [], "rules dropped by a reshape")

if __name__ == "__main__":
    unittest.main()
