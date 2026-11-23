"""patch_qs_agent.py: adds windows and rule R-MASTER to the installed QS agent, once, with a backup."""
import os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from patch_qs_agent import add_windows, patch, MARK

class Patch(unittest.TestCase):
    def test_platforms_in_every_shape(self):
        cases = {
            "---\nname: q\nplatforms: [macos, linux]\n---\nbody": "platforms: [macos, linux, windows]",
            "---\nname: q\nplatforms: macos, linux\n---\nbody": "platforms: macos, linux, windows",
            "---\nname: q\nplatforms:\n  - macos\n  - linux\ndescription: x\n---\nbody": "  - linux\n  - windows\ndescription: x",
            "---\nname: q\nmetadata:\n  hermes:\n    platforms: [linux]\n---\nbody": "    platforms: [linux, windows]",
        }
        for src, want in cases.items():
            out, ch = add_windows(src)
            self.assertTrue(ch, src); self.assertIn(want, out); self.assertTrue(out.endswith("---\nbody"))
        for same in ("---\nname: q\nplatforms: [linux, windows]\n---\nb", "---\nname: q\n---\nplatforms: [linux]\n", "no frontmatter\nplatforms: [linux]", "---\nname: q\nplatforms: [all]\n---\nb"):
            self.assertEqual(add_windows(same), (same, False))                     # nothing to add, or not in the frontmatter

    def test_rule_added_once_and_line_endings_kept(self):
        out, done = patch("---\nname: q\nplatforms: [macos, linux]\n---\n# QS\nRules.\n")
        self.assertEqual(done, ["platforms: added windows", "rule R-MASTER added"])
        self.assertIn("# QS\nRules.\n\n" + MARK, out); self.assertIn("**staged**", out); self.assertIn("On MatDuo:** nothing changes", out)
        self.assertEqual(patch(out), (out, []))                                    # safe to run again
        crlf, _ = patch("---\r\nname: q\r\nplatforms: [linux]\r\n---\r\nbody\r\n")
        self.assertNotIn("\n", crlf.replace("\r\n", "")); self.assertIn("platforms: [linux, windows]\r\n", crlf)

    def test_on_disk_backup_and_only_skill_md_changes(self):
        home = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        skill = home / "skills" / "mahareka" / "mahareka-qs-agent"; (skill / "scripts").mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: mahareka-qs-agent\nplatforms: [macos, linux]\n---\nRules\n", encoding="utf-8")
        (skill / "scripts" / "QS_RATEBASE_test.xlsx").write_bytes(b"ratebase"); (skill / "scripts" / "qs_boot.py").write_text("print(1)\n", encoding="utf-8")
        env = {**os.environ, "HOME": home.as_posix(), "USERPROFILE": str(home)}
        run = lambda d: subprocess.run([sys.executable, "-P", str(ROOT / "tools" / "patch_qs_agent.py"), str(d)], capture_output=True, text=True, encoding="utf-8", env=env)
        p = run(home / "skills")
        self.assertEqual(p.returncode, 0, p.stderr); self.assertIn("platforms: added windows, rule R-MASTER added", p.stdout)
        self.assertIn("windows", (skill / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual((skill / "scripts" / "QS_RATEBASE_test.xlsx").read_bytes(), b"ratebase")     # the ratebase is never touched
        backups = list((home / "mc-backups" / "skills").glob("mahareka-qs-agent-SKILL-*.md"))
        self.assertEqual(len(backups), 1); self.assertNotIn("windows", backups[0].read_text(encoding="utf-8"))
        self.assertIn("nothing to change", run(home / "skills").stdout)
        self.assertEqual(len(list((home / "mc-backups" / "skills").glob("*"))), 1)                     # no second backup
        self.assertIn("not installed here", run(home / "nowhere-skills-dir-made").stdout if (home / "nowhere-skills-dir-made").mkdir() is None else "")

if __name__ == "__main__":
    unittest.main()
