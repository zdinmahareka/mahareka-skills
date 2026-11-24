"""patch_qs_agent.py: hides the installed QS agent on windows and sets rule R-MASTER v2, once, with a backup."""
import os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from patch_qs_agent import remove_windows, set_rule, patch, MARK, MARK_V1

# What the 23 Nov version of this tool appended (its marker, heading and bullets).
V1 = MARK_V1 + """
## Ratebase master and copies (R-MASTER)

The master QS_RATEBASE is the one on MatDuo (the Linux VPS). Every other machine holds a
read-only copy.

- **On MatDuo:** nothing changes. Publish and install ratebase updates exactly as this skill
  already says.
- **On any other machine** (for example Mattigo, the Windows laptop): never save, publish or
  overwrite the ratebase or its published outputs. A new rate or rule learned there is
  **staged**: end the answer with `Staged for master:` and list each item (trade, item, UOM,
  rate, source, date). Zaim approves it and MatDuo adds it to the master.
- If this machine's ratebase version differs from the master's (Mission Control → Virtual Office
  shows both), say so before quoting a rate from the copy.
"""

class Patch(unittest.TestCase):
    def test_windows_leaves_platforms_in_every_shape(self):
        cases = {
            "---\nname: q\nplatforms: [macos, linux, windows]\n---\nbody": "platforms: [macos, linux]\n---",
            "---\nname: q\nplatforms: macos, Windows, linux\n---\nbody": "platforms: macos, linux\n---",
            "---\nname: q\nplatforms:\n  - macos\n  - linux\n  - windows\ndescription: x\n---\nbody": "  - macos\n  - linux\ndescription: x",
            "---\nname: q\nmetadata:\n  hermes:\n    platforms: [linux, 'windows']\n---\nbody": "    platforms: [linux]\n---",
        }
        for src, want in cases.items():
            out, ch = remove_windows(src)
            self.assertTrue(ch, src); self.assertIn(want, out); self.assertNotIn("indows", out); self.assertTrue(out.endswith("---\nbody"))
        for same in ("---\nname: q\nplatforms: [macos, linux]\n---\nb",            # nothing to remove
                     "---\nname: q\nplatforms: [windows]\n---\nb",                 # never leave a skill with no platform
                     "---\nname: q\nplatforms:\n  - windows\n---\nb",
                     "---\nname: q\n---\nplatforms: [linux, windows]\n", "no frontmatter\nplatforms: [linux, windows]"):
            self.assertEqual(remove_windows(same), (same, False))

    def test_rule_v2_replaces_v1_wherever_it_sits_and_keeps_the_rest(self):
        base = "---\nname: q\nplatforms: [macos, linux, windows]\n---\n# QS\nRules.\n"
        was = base + "\n" + V1                                                    # exactly as the old tool left it
        out, done = patch(was)
        self.assertEqual(done, ["platforms: removed windows", "rule R-MASTER updated (v1 to v2)"])
        self.assertIn("# QS\nRules.\n\n" + MARK, out); self.assertNotIn(MARK_V1, out); self.assertNotIn("read-only", out); self.assertNotIn("Ratebase master and copies", out)
        self.assertIn("No other machine keeps a ratebase", out); self.assertIn("ask MatDuo", out); self.assertIn("**staged**", out); self.assertEqual(out.count("(R-MASTER)"), 1)
        self.assertEqual(patch(out), (out, []))                                    # safe to run again
        # Hermes edited the v1 section and added its own section after it: the whole v1 section goes, the rest stays
        edited = base + "\n" + V1.replace("say so before quoting a rate from the copy.", "say so first.\n- Extra line Hermes added inside.") + "\n## Lessons Hermes learned\n- keep this\n"
        out2, done2 = patch(edited)
        self.assertIn("rule R-MASTER updated (v1 to v2)", done2); self.assertNotIn("Extra line Hermes added inside", out2); self.assertNotIn(MARK_V1, out2)
        self.assertTrue(out2.rstrip().endswith("## Lessons Hermes learned\n- keep this")); self.assertLess(out2.index(MARK), out2.index("## Lessons Hermes learned"))
        fresh, done3 = patch("---\nname: q\nplatforms: [macos, linux]\n---\n# QS\nRules.\n")                           # never patched before
        self.assertEqual(done3, ["rule R-MASTER added"]); self.assertTrue(fresh.startswith("---\nname: q\nplatforms: [macos, linux]\n---\n# QS\nRules.\n\n" + MARK))
        self.assertEqual(set_rule(fresh), (fresh, None))

    def test_line_endings_are_kept(self):
        crlf, done = patch(("---\nname: q\nplatforms: [linux, windows]\n---\nbody\n\n" + V1).replace("\n", "\r\n"))
        self.assertEqual(len(done), 2); self.assertNotIn("\n", crlf.replace("\r\n", "")); self.assertIn("platforms: [linux]\r\n", crlf); self.assertIn(MARK + "\r\n", crlf)

    def test_on_disk_backup_and_only_skill_md_changes(self):
        home = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        skill = home / "skills" / "mahareka" / "mahareka-qs-agent"; (skill / "scripts").mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: mahareka-qs-agent\nplatforms: [macos, linux, windows]\n---\nRules\n\n" + V1, encoding="utf-8")
        (skill / "scripts" / "QS_RATEBASE_test.xlsx").write_bytes(b"ratebase"); (skill / "scripts" / "qs_boot.py").write_text("print(1)\n", encoding="utf-8")
        env = {**os.environ, "HOME": home.as_posix(), "USERPROFILE": str(home)}
        run = lambda d: subprocess.run([sys.executable, "-P", str(ROOT / "tools" / "patch_qs_agent.py"), str(d)], capture_output=True, text=True, encoding="utf-8", env=env)
        p = run(home / "skills")
        self.assertEqual(p.returncode, 0, p.stderr); self.assertIn("platforms: removed windows, rule R-MASTER updated (v1 to v2)", p.stdout)
        now = (skill / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("platforms: [macos, linux]", now); self.assertIn(MARK, now); self.assertNotIn("read-only", now)
        self.assertEqual((skill / "scripts" / "QS_RATEBASE_test.xlsx").read_bytes(), b"ratebase")     # the ratebase is never touched
        self.assertEqual((skill / "scripts" / "qs_boot.py").read_text(encoding="utf-8"), "print(1)\n")
        backups = list((home / "mc-backups" / "skills").glob("mahareka-qs-agent-SKILL-*.md"))
        self.assertEqual(len(backups), 1); self.assertIn("windows", backups[0].read_text(encoding="utf-8")); self.assertIn(MARK_V1, backups[0].read_text(encoding="utf-8"))
        self.assertIn("nothing to change", run(home / "skills").stdout)
        self.assertEqual(len(list((home / "mc-backups" / "skills").glob("*"))), 1)                     # no second backup
        (home / "empty").mkdir(); self.assertIn("not installed here", run(home / "empty").stdout)

if __name__ == "__main__":
    unittest.main()
