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
        self.assertIsNone(w["qs_boot"]); self.assertNotIn("rate_history", w, "one ratebase: the skill looks for no rate memory of its own")
        k = self.home / "kb"; k.mkdir()
        (k / "qs_boot.py").write_text("print('INTACT')\n", encoding="utf-8")
        (k / "Rate_History.xlsx").write_bytes(b"x")
        w = self.where(MAHAREKA_KNOWLEDGE=str(k))
        self.assertEqual(w["knowledge_found_by"], "env")
        self.assertTrue(w["qs_boot"].endswith("qs_boot.py"))
        self.assertNotIn("rate_history", w, "a leftover Rate_History in KNOWLEDGE is ignored")

    def test_where_never_uses_archive_or_download_copies(self):
        """Old ratebase / Rate_History copies under home (Downloads, ARCHIVE, Telegram, temp) are ignored."""
        for d in ("Downloads/ARCHIVE/mahareka qs agent v1.4", "Downloads/Telegram Desktop",
                  ".hermes/profiles/a/cache/scratch/tmpx1/QS"):
            p = self.home / d; p.mkdir(parents=True)
            (p / "qs_boot.py").write_text("", encoding="utf-8"); (p / "Rate_History.xlsx").write_bytes(b"x")
        w = self.where()
        self.assertEqual(w["knowledge"], str(self.home / "mahareka-knowledge"))
        self.assertIsNone(w["qs_boot"])
        named = self.home / "Downloads" / "ARCHIVE" / "mahareka qs agent v1.4" / "Rate_History.xlsx"
        w = self.where(MAHAREKA_RATE_HISTORY=str(named))          # even a named one is no longer read (v2.1)
        self.assertNotIn(str(named), json.dumps(w))

    def install(self, skills, **extra):
        # the installer must use this Python (it has openpyxl); python3 on PATH may be a Hermes venv without it
        env = {**self.env, "MAHAREKA_PYTHON": Path(sys.executable).as_posix(), "MAHAREKA_SET_DIR": "1", **extra}
        env = {k: v for k, v in env.items() if v is not None}
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
        (old / "_local").mkdir(); (old / "_local" / "lessons.md").write_text("mine", encoding="utf-8")
        p = self.install(skills)                                   # the old copy is not from this repo: kept
        self.assertEqual(p.returncode, 3, p.stdout + p.stderr); self.assertIn("bq-error-checker: KEPT (local_change)", p.stdout)
        self.assertTrue((old / "references" / "x.md").is_file()); self.assertFalse((self.home / "mc-backups" / "skills").exists() and list((self.home / "mc-backups" / "skills").glob("bq-*")))
        p = self.install(skills, MAHAREKA_REPLACE="bq-error-checker")   # Zaim says replace it
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual((old / "_local" / "lessons.md").read_text(encoding="utf-8"), "mine", "the machine's own notes are carried over")
        # the installed copy is the repo's current one, whatever its version number is
        self.assertEqual((old / "SKILL.md").read_text(encoding="utf-8"), (ROOT / "skills" / "bq-error-checker" / "SKILL.md").read_text(encoding="utf-8"))
        self.assertFalse((old / "references").exists(), "old files must not linger")
        self.assertTrue((skills / "mahareka" / "mahareka-skill-builder" / "SKILL.md").is_file())
        backups = list((self.home / "mc-backups" / "skills").glob("bq-error-checker-*"))
        self.assertEqual(len(backups), 1); self.assertTrue((backups[0] / "references" / "x.md").is_file())
        self.assertEqual(len(list(skills.rglob("bq-error-checker/SKILL.md"))), 1)
        self.assertTrue((skills / "mahareka" / "chief-of-staff" / "_tools" / "roster.py").is_file())
        self.assertTrue(os.path.samefile((self.home / ".mahareka" / "skills-dir").read_text(encoding="utf-8").strip(), skills))   # for auto-update
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
        self.assertNotIn("rate_history", w, "one ratebase: no rate memory of its own")

    @unittest.skipIf(os.environ.get("MAHAREKA_SKIP_TESTS"), "already inside an install run")
    def test_install_never_guesses_the_folder_and_keeps_local_edits(self):
        skills = self.home / ".hermes" / "profiles" / "agent" / "skills"; skills.mkdir(parents=True)
        other = self.home / ".hermes" / "backups" / "pkg" / "files" / "skills"; other.mkdir(parents=True)
        p = self.install(skills, MAHAREKA_SET_DIR=None)            # no recorded folder: nothing installs
        self.assertEqual(p.returncode, 1); self.assertIn("no recorded skills folder", p.stdout); self.assertEqual(list(skills.iterdir()), [])
        self.assertEqual(self.install(skills).returncode, 0)       # first install, by hand
        cos = skills / "mahareka" / "chief-of-staff" / "SKILL.md"; self.assertTrue(cos.is_file())
        p = self.install(other, MAHAREKA_SET_DIR=None)             # a backup or another profile is refused
        self.assertEqual(p.returncode, 1); self.assertIn("is not this machine's recorded skills folder", p.stdout); self.assertEqual(list(other.iterdir()), [])
        p = self.install(skills, MAHAREKA_SET_DIR=None)            # unchanged: nothing is moved
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr); self.assertIn("chief-of-staff: already this version", p.stdout)
        self.assertFalse((self.home / "mc-backups" / "skills").exists() and list((self.home / "mc-backups" / "skills").iterdir()))
        cos.write_text(cos.read_text(encoding="utf-8") + "\n## Lesson Hermes learned\n- keep me\n", encoding="utf-8")   # Hermes patched it
        (cos.parent / "_local").mkdir(); (cos.parent / "_local" / "notes.md").write_text("x", encoding="utf-8")            # _local alone is not an edit
        p = self.install(skills, MAHAREKA_SET_DIR=None)
        self.assertEqual(p.returncode, 3, p.stdout + p.stderr); self.assertIn("KEPT (local_change): chief-of-staff", p.stdout)
        self.assertIn("keep me", cos.read_text(encoding="utf-8")); self.assertIn("bq-error-checker: already this version", p.stdout)

    def test_skill_state_knows_this_repos_own_versions(self):
        sys.path.insert(0, str(ROOT / "tools")); self.addCleanup(sys.path.remove, str(ROOT / "tools"))
        import skill_state as st
        self.assertEqual(st.decide(None, "a", None, ()), "new"); self.assertEqual(st.decide("a", "a", None, ()), "same")
        self.assertEqual(st.decide("old", "a", "old", ()), "clean"); self.assertEqual(st.decide("old", "a", None, {"old"}), "clean")
        self.assertEqual(st.decide("edited", "a", "old", {"older"}), "local_change")
        a = self.home / "a"; b = self.home / "b"
        for d, nl in ((a, "\n"), (b, "\r\n")):
            (d / "__pycache__").mkdir(parents=True); (d / "_local").mkdir()
            (d / "SKILL.md").write_bytes(f"x{nl}y{nl}".encode()); (d / "__pycache__" / "c.pyc").write_bytes(nl.encode()); (d / "_local" / "n.md").write_text(str(d), encoding="utf-8")
        self.assertEqual(st.fingerprint(a), st.fingerprint(b), "line endings, caches and _local don't count")
        (b / "SKILL.md").write_bytes(b"x\ny\nz\n"); self.assertNotEqual(st.fingerprint(a), st.fingerprint(b))
        if (ROOT / ".git").exists() and shutil.which("git"):      # an unedited copy of any past version is recognised
            past = st.history(ROOT, "bq-error-checker")
            head = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "skills/bq-error-checker"], capture_output=True, text=True).stdout
            if past and not head.strip(): self.assertIn(st.fingerprint(ROOT / "skills" / "bq-error-checker"), past)

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
