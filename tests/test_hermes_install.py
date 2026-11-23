"""Hermes-only install: paths come from MAHAREKA_* or ~/, the old copy is backed up outside the skills folder."""
import json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")  # child output on Windows consoles

ROOT = Path(__file__).resolve().parents[1]
WHERE = ROOT / "skills" / "bq-error-checker" / "_tools" / "where.py"
# The bash to run the installer with. On Windows a bare "bash" from Python can start WSL's
# System32\bash.exe instead of Git Bash, so use the one the installer exported, else PATH's.
BASH = os.environ.get("MAHAREKA_BASH") or shutil.which("bash") or "bash"

class HermesInstall(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("MAHAREKA_")}
        # bash gets forward slashes (Git Bash on Windows drops backslashes); Python reads USERPROFILE there
        self.env.update(HOME=self.home.as_posix(), USERPROFILE=str(self.home), MAHAREKA_SKIP_TESTS="1")

    def where(self, **extra):
        p = subprocess.run([sys.executable, "-P", str(WHERE), "--json"], capture_output=True, text=True, encoding="utf-8",
                           env={**self.env, **extra})
        return json.loads(p.stdout)

    def test_where_defaults_and_overrides(self):
        w = self.where()
        self.assertEqual(w["knowledge"], str(self.home / "mahareka-knowledge"))
        self.assertEqual(w["runs"], str(self.home / "mahareka-runs"))
        self.assertIsNone(w["qs_boot"]); self.assertIsNone(w["rate_history"])
        k = self.home / "kb"; k.mkdir()
        (k / "qs_boot.py").write_text("print('INTACT')\n", encoding="utf-8")
        (k / "Rate_History.xlsx").write_bytes(b"x")
        w = self.where(MAHAREKA_KNOWLEDGE=str(k))
        self.assertEqual(w["knowledge_found_by"], "env")
        self.assertTrue(w["qs_boot"].endswith("qs_boot.py"))
        self.assertTrue(w["rate_history"].endswith("Rate_History.xlsx"))

    def test_where_never_uses_archive_or_download_copies(self):
        """Old ratebase / Rate_History copies under home (Downloads, ARCHIVE, Telegram, temp) are ignored."""
        for d in ("Downloads/ARCHIVE/mahareka qs agent v1.4", "Downloads/Telegram Desktop",
                  ".hermes/profiles/a/cache/scratch/tmpx1/QS"):
            p = self.home / d; p.mkdir(parents=True)
            (p / "qs_boot.py").write_text("", encoding="utf-8"); (p / "Rate_History.xlsx").write_bytes(b"x")
        w = self.where()
        self.assertEqual(w["knowledge"], str(self.home / "mahareka-knowledge"))
        self.assertIsNone(w["qs_boot"]); self.assertIsNone(w["rate_history"])
        named = self.home / "Downloads" / "ARCHIVE" / "mahareka qs agent v1.4" / "Rate_History.xlsx"
        w = self.where(MAHAREKA_RATE_HISTORY=str(named))          # only when Zaim names it
        self.assertEqual((w["rate_history"], w["rate_history_found_by"]), (str(named), "env"))

    def install(self, skills, **extra):
        # the installer must use this Python (it has openpyxl); python3 on PATH may be a Hermes venv without it
        env = {**self.env, "MAHAREKA_PYTHON": Path(sys.executable).as_posix(), **extra}
        return subprocess.run([BASH, (ROOT / "tools" / "install-hermes.sh").as_posix(), skills.as_posix()],
                              capture_output=True, text=True, encoding="utf-8", env=env)

    def agent_layout(self):
        """A Hermes profile: old bq skill and the QS agent (with the live ratebase) in skills/mahareka/."""
        skills = self.home / ".hermes" / "profiles" / "agent" / "skills"
        old = skills / "mahareka" / "bq-error-checker"; old.mkdir(parents=True)
        (old / "SKILL.md").write_text("---\nname: bq-error-checker\ndescription: old\n---\nv1\n", encoding="utf-8")
        (old / "references").mkdir(); (old / "references" / "x.md").write_text("old", encoding="utf-8")
        qs = skills / "mahareka" / "mahareka-qs-agent" / "scripts"; qs.mkdir(parents=True)
        (qs.parent / "SKILL.md").write_text("---\nname: mahareka-qs-agent\ndescription: qs\n---\n", encoding="utf-8")
        (qs / "qs_boot.py").write_text("print('QS BOOT: INTACT')\n", encoding="utf-8")
        (qs / "QS_RATEBASE_test_a.xlsx").write_bytes(b"x")
        out = self.home / ".hermes" / "qs_outputs"; out.mkdir(parents=True)
        (out / "QS_RATEBASE_test_b.xlsx").write_bytes(b"x")
        return skills, old, qs

    @unittest.skipIf(os.environ.get("MAHAREKA_SKIP_TESTS"), "already inside an install run")
    def test_install_replaces_in_place_and_backs_up(self):
        skills, old, qs = self.agent_layout()
        p = self.install(skills)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("version **2.0**", (old / "SKILL.md").read_text(encoding="utf-8"))
        self.assertFalse((old / "references").exists(), "old files must not linger")
        self.assertTrue((skills / "mahareka" / "mahareka-skill-builder" / "SKILL.md").is_file())
        backups = list((self.home / "mc-backups" / "skills").glob("bq-error-checker-*"))
        self.assertEqual(len(backups), 1); self.assertTrue((backups[0] / "references" / "x.md").is_file())
        self.assertEqual(len(list(skills.rglob("bq-error-checker/SKILL.md"))), 1)
        self.assertTrue((skills / "mahareka" / "chief-of-staff" / "_tools" / "roster.py").is_file())
        self.assertEqual((self.home / ".mahareka" / "skills-dir").read_text(encoding="utf-8").strip(), skills.as_posix())   # for auto-update
        self.assertEqual((qs / "qs_boot.py").read_text(encoding="utf-8"), "print('QS BOOT: INTACT')\n", "the QS agent's engines are never touched")
        self.assertEqual((qs / "QS_RATEBASE_test_a.xlsx").read_bytes(), b"x", "the ratebase is never touched")
        self.assertIn("rule R-MASTER", p.stdout); self.assertIn("R-MASTER", (qs.parent / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("[install] done", p.stdout)
        self.assertIn(f"KNOWLEDGE     {qs}  (skill mahareka-qs-agent)", p.stdout)   # the installed copy's view
        # the installed copy finds the QS agent's ratebase folder and the recorded Python
        recorded = (self.home / ".mahareka" / "python").read_text(encoding="utf-8").strip()
        w = json.loads(subprocess.run([sys.executable, "-P", str(old / "_tools" / "where.py"), "--json"],
                                      capture_output=True, text=True, encoding="utf-8", env=self.env).stdout)
        self.assertEqual(w["knowledge"], str(qs)); self.assertEqual(w["knowledge_found_by"], "skill mahareka-qs-agent")
        self.assertEqual(w["python"], recorded); self.assertEqual(w["python_found_by"], "recorded by install")
        self.assertIsNone(w["rate_history"])

    def test_install_stops_on_a_python_without_openpyxl(self):
        skills, old, _ = self.agent_layout()
        fake = self.home / "nopy"; fake.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8"); fake.chmod(0o755)
        p = self.install(skills, MAHAREKA_PYTHON=fake.as_posix())
        self.assertEqual(p.returncode, 1)
        self.assertIn("STOP: MAHAREKA_PYTHON", p.stdout)
        self.assertTrue((old / "references" / "x.md").is_file(), "nothing moved on STOP")
        self.assertFalse((self.home / ".mahareka" / "python").exists())

    def test_where_python_override(self):
        self.assertEqual(self.where(MAHAREKA_PYTHON="/opt/py/bin/python")["python_found_by"], "env")
        self.assertEqual(self.where()["python_found_by"], "this python")

if __name__ == "__main__":
    unittest.main()
