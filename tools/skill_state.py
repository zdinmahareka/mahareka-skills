#!/usr/bin/env python3
"""
Has an installed skill changed on this machine since it was installed?
Hermes edits skills by itself (the curator, `skill_manage` after a task), so the installer must
not replace a copy that holds such edits. An installed copy may be replaced only when it is one
this repo produced: the version recorded at the last install, or any version in the repo's git
history. Anything else is a local change and is kept.

Usage: skill_state.py check <repo> <name> <dest>   prints new | same | clean | local_change
       skill_state.py record <name> <dest>         remember what was just installed
       skill_state.py samedir <a> <b>              exit 0 when both are the same folder
Standard library only. Ignored when comparing: _local/ (the machine's own notes), dot files,
__pycache__, *.pyc, and CRLF vs LF.
"""
import hashlib, json, os, subprocess, sys, time
from pathlib import Path

SKIP_DIRS = {"__pycache__", "_local"}

def _norm(data): return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()

def _roll(pairs):
    h = hashlib.sha256()
    for rel, digest in sorted(pairs): h.update(f"{rel}\0{digest}\n".encode("utf-8"))
    return h.hexdigest()

def fingerprint(folder):
    """One hash for the whole skill folder; None when the folder is missing."""
    folder = Path(folder)
    if not folder.is_dir(): return None
    pairs = []
    for d, dirs, files in os.walk(folder):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
        for f in files:
            if f.startswith(".") or f.endswith(".pyc"): continue
            p = Path(d) / f
            pairs.append((p.relative_to(folder).as_posix(), _norm(p.read_bytes())))
    return _roll(pairs)

def history(repo, name):
    """Fingerprints of every version of skills/<name> in the repo's git history (empty if no git)."""
    def git(*a, data=None):
        return subprocess.run(["git", "-C", str(repo), *a], input=data, capture_output=True, check=True).stdout
    out, blobs = set(), {}
    try:
        commits = git("log", "--format=%H", "--", f"skills/{name}").decode().split()
        for c in commits:
            rows = []
            for line in git("ls-tree", "-r", "-z", c, f"skills/{name}").decode("utf-8", "replace").split("\0"):
                if not line.strip(): continue
                meta, path = line.split("\t", 1)
                mode, kind, sha = meta.split()
                rel = path[len(f"skills/{name}/"):]
                parts = rel.split("/")
                if kind != "blob" or any(x in SKIP_DIRS or x.startswith(".") for x in parts) or rel.endswith(".pyc"): continue
                rows.append((rel, sha))
            for rel, sha in rows:
                if sha not in blobs: blobs[sha] = _norm(git("cat-file", "blob", sha))
            out.add(_roll([(rel, blobs[sha]) for rel, sha in rows]))
    except (OSError, subprocess.CalledProcessError, ValueError):
        pass
    return out

def state_file(): return Path.home() / ".mahareka" / "installed.json"

def recorded(name, dest):
    try: e = json.loads(state_file().read_text(encoding="utf-8")).get(name) or {}
    except (OSError, ValueError): return None
    return e.get("fingerprint") if e.get("dest") == Path(dest).resolve().as_posix() else None

def decide(dest_fp, repo_fp, recorded_fp, past):
    """new: nothing installed. same: already this version. clean: an unedited older version.
    local_change: edited on this machine (or not from this repo): keep it."""
    if dest_fp is None: return "new"
    if dest_fp == repo_fp: return "same"
    if dest_fp == recorded_fp or dest_fp in past: return "clean"
    return "local_change"

def check(repo, name, dest):
    d, r = fingerprint(dest), fingerprint(Path(repo) / "skills" / name)
    if d is None or d == r: return decide(d, r, None, ())
    rec = recorded(name, dest)
    return decide(d, r, rec, () if d == rec else history(repo, name))

def record(name, dest):
    f = state_file(); f.parent.mkdir(parents=True, exist_ok=True)
    try: data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError): data = {}
    data[name] = {"fingerprint": fingerprint(dest), "dest": Path(dest).resolve().as_posix(), "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    f.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")

def main(argv):
    if len(argv) == 4 and argv[0] == "check": print(check(argv[1], argv[2], argv[3])); return 0
    if len(argv) == 3 and argv[0] == "record": record(argv[1], argv[2]); return 0
    if len(argv) == 3 and argv[0] == "samedir":
        try: return 0 if os.path.samefile(argv[1], argv[2]) else 1
        except OSError: return 1
    print(__doc__); return 2

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
