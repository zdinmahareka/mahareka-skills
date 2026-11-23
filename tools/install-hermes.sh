#!/usr/bin/env bash
# Install Mahareka skills into a Hermes profile's skills folder.
# Usage: bash tools/install-hermes.sh <hermes skills dir> [skill ...]
#   e.g. bash tools/install-hermes.sh ~/.hermes/profiles/matduo/skills
# Runs the tests first. A skill not installed yet goes to <skills dir>/mahareka/<name>/.
# An installed copy is replaced only when it is unedited (tools/skill_state.py): the old copy
# moves to ~/mc-backups/skills/<name>-<time>/ (outside the skills folder, so Hermes never sees
# two copies), its _local/ folder is carried over, and the new one is copied in whole.
# A copy edited on this machine (Hermes's curator or skill_manage, or by hand) is KEPT: the
# run ends with exit 3 and names it. To replace it anyway (a backup is still kept):
#   MAHAREKA_REPLACE="<name> ..." bash tools/install-hermes.sh <skills dir>
# The skills folder is recorded in ~/.mahareka/skills-dir at the first install. Any other
# folder is refused unless MAHAREKA_SET_DIR=1 is given, so nothing can install by guesswork.
set -euo pipefail
W() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s\n' "$1"; fi; }
REPO="$(W "$(cd "$(dirname "$0")/.." && pwd)")"
SKILLS="${1:?usage: install-hermes.sh <hermes skills dir> [skill ...]}"; shift || true
[ -d "$SKILLS" ] || { echo "[install] no such skills folder: $SKILLS"; exit 1; }
SKILLS="$(W "$(cd "$SKILLS" && pwd)")"
NAMES=("$@"); [ ${#NAMES[@]} -gt 0 ] || NAMES=(bq-error-checker mahareka-skill-builder chief-of-staff)

# The Python the skills run with (needs openpyxl): MAHAREKA_PYTHON, else the first of
# python3 / py / python that has openpyxl. Recorded in ~/.mahareka/python for where.py.
ok() { "$1" -c "import sys, openpyxl; sys.exit(sys.version_info < (3, 11))" >/dev/null 2>&1; }
PY=""
if [ -n "${MAHAREKA_PYTHON:-}" ]; then
  ok "$MAHAREKA_PYTHON" || { echo "[install] STOP: MAHAREKA_PYTHON=$MAHAREKA_PYTHON is not Python 3.11+ with openpyxl"; exit 1; }
  PY="$MAHAREKA_PYTHON"
else
  for c in python3 py python; do
    if command -v "$c" >/dev/null 2>&1 && ok "$c"; then PY="$c"; break; fi
  done
fi
if [ -z "$PY" ]; then
  echo "[install] STOP: no Python 3.11+ with openpyxl (tried python3, py, python)."
  echo "[install] Either point at one that has it: MAHAREKA_PYTHON=/path/to/python bash $0 $SKILLS"
  echo "[install] or install it into a non-Hermes Python: <python> -m pip install openpyxl"
  exit 1
fi
# record the real interpreter (on Windows a native C:\\... path, which Git Bash and Hermes both run)
PY="$("$PY" -c "import sys; print(sys.executable)")"
echo "[install] python: $PY"

# Only ever install into this machine's recorded skills folder.
STATE="$REPO/tools/skill_state.py"; REC="$(cat "$HOME/.mahareka/skills-dir" 2>/dev/null || true)"
if [ "${MAHAREKA_SET_DIR:-}" != "1" ]; then
  if [ -z "$REC" ]; then
    echo "[install] STOP: this machine has no recorded skills folder (~/.mahareka/skills-dir), so nothing is installed."
    echo "[install] If $SKILLS is where this machine's Hermes keeps its own skills, run once: MAHAREKA_SET_DIR=1 bash $0 $SKILLS"
    exit 1
  fi
  "$PY" "$STATE" samedir "$REC" "$SKILLS" || { echo "[install] STOP: $SKILLS is not this machine's recorded skills folder ($REC). Nothing installed."; exit 1; }
fi

# tests that run this installer must use this same bash (on Windows: Git Bash, not WSL's)
if command -v cygpath >/dev/null 2>&1; then export MAHAREKA_BASH="$(cygpath -w "$BASH")"; else export MAHAREKA_BASH="$BASH"; fi
LOG="$(mktemp)"; trap 'rm -f "$LOG"' EXIT
( cd "$REPO" && "$PY" -m unittest discover -s tests >"$LOG" 2>&1 ) \
  || { echo "[install] STOP: tests failed"; tail -20 "$LOG"; exit 1; }
echo "[install] tests: $(grep -oE 'Ran [0-9]+ tests' "$LOG") OK"
find "$REPO" -name __pycache__ -prune -exec rm -rf {} +

mkdir -p "$HOME/.mahareka" && printf '%s\n' "$PY" > "$HOME/.mahareka/python"
# where the skills go on this machine, so auto-update can install new versions without being told
printf '%s\n' "$SKILLS" > "$HOME/.mahareka/skills-dir"

BQ_DEST=""; KEPT=""
STAMP="$(date +%Y%m%d-%H%M%S)"; BK="$HOME/mc-backups/skills"; mkdir -p "$BK"
for n in "${NAMES[@]}"; do
  [ -f "$REPO/skills/$n/SKILL.md" ] || { echo "[install] STOP: unknown skill $n"; exit 1; }
  # hidden folders below the skills dir (.hub, .archive) are skipped; ~/.hermes itself is fine
  cur="$(cd "$SKILLS" && find . -maxdepth 4 -path "*/$n/SKILL.md" -not -path "*/.*/*" 2>/dev/null | head -1)"
  if [ -n "$cur" ]; then dest="$SKILLS/$(dirname "${cur#./}")"; else dest="$SKILLS/mahareka/$n"; fi
  if [ "$n" = "bq-error-checker" ]; then BQ_DEST="$dest"; fi
  st="$("$PY" "$STATE" check "$REPO" "$n" "$dest")"
  case " ${MAHAREKA_REPLACE:-} " in *" $n "*|*" all "*) [ "$st" = "local_change" ] && st="forced" ;; esac
  if [ "$st" = "same" ]; then
    "$PY" "$STATE" record "$n" "$dest"; echo "[install] $n: already this version at $dest"; continue
  fi
  if [ "$st" = "local_change" ]; then
    KEPT="$KEPT $n"
    echo "[install] $n: KEPT (local_change). The copy at $dest was edited on this machine since it was installed, so the repo version was not installed."
    continue
  fi
  if [ -d "$dest" ]; then
    mv "$dest" "$BK/$n-$STAMP"; echo "[install] $n: old copy -> $BK/$n-$STAMP$([ "$st" = "forced" ] && echo " (edited on this machine; replaced because MAHAREKA_REPLACE names it)")"
  else
    mkdir -p "$(dirname "$dest")"
  fi
  cp -R "$REPO/skills/$n" "$dest"
  # the machine's own notes stay with the skill
  if [ -d "$BK/$n-$STAMP/_local" ]; then rm -rf "$dest/_local"; cp -R "$BK/$n-$STAMP/_local" "$dest/_local"; fi
  "$PY" "$REPO/skills/mahareka-skill-builder/scripts/icm_check.py" "$dest" >/dev/null \
    || { echo "[install] STOP: icm_check failed on $dest (old copy is in $BK)"; exit 1; }
  find "$dest" -name __pycache__ -prune -exec rm -rf {} +
  "$PY" "$STATE" record "$n" "$dest"
  echo "[install] $n: installed at $dest ($(grep -oE 'version \*\*[0-9.]+\*\*' "$dest/SKILL.md" | head -1 | tr -d '*'))"
done
# approved changes to the installed QS agent (windows + ratebase master rule); safe to repeat
"$PY" "$REPO/tools/patch_qs_agent.py" "$SKILLS" || echo "[install] qs-agent not changed (see above)"
# paths as the installed skill sees them (it looks for mahareka-qs-agent next to itself)
WHERE="${BQ_DEST:-$REPO/skills/bq-error-checker}/_tools/where.py"; [ -f "$WHERE" ] || WHERE="$REPO/skills/bq-error-checker/_tools/where.py"
"$PY" "$WHERE"
if [ -n "$KEPT" ]; then
  echo "[install] done, but KEPT (local_change):$KEPT. Zaim decides: merge the machine's edits into the repo, or replace with MAHAREKA_REPLACE=\"${KEPT# }\" (a backup is kept)."
  exit 3
fi
echo "[install] done"
