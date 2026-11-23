#!/usr/bin/env bash
# Install Mahareka skills into a Hermes profile's skills folder.
# Usage: bash tools/install-hermes.sh <hermes skills dir> [skill ...]
#   e.g. bash tools/install-hermes.sh ~/.hermes/profiles/matduo/skills
# Runs the tests first. Each existing copy is moved to ~/mc-backups/skills/<name>-<time>/
# (outside the skills folder, so Hermes never sees two copies), then replaced whole.
# A skill not installed yet goes to <skills dir>/mahareka/<name>/.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS="${1:?usage: install-hermes.sh <hermes skills dir> [skill ...]}"; shift || true
[ -d "$SKILLS" ] || { echo "[install] no such skills folder: $SKILLS"; exit 1; }
NAMES=("$@"); [ ${#NAMES[@]} -gt 0 ] || NAMES=(bq-error-checker mahareka-skill-builder)

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

LOG="$(mktemp)"; trap 'rm -f "$LOG"' EXIT
( cd "$REPO" && "$PY" -m unittest discover -s tests >"$LOG" 2>&1 ) \
  || { echo "[install] STOP: tests failed"; tail -20 "$LOG"; exit 1; }
echo "[install] tests: $(grep -oE 'Ran [0-9]+ tests' "$LOG") OK"
find "$REPO" -name __pycache__ -prune -exec rm -rf {} +

mkdir -p "$HOME/.mahareka" && printf '%s\n' "$PY" > "$HOME/.mahareka/python"

BQ_DEST=""
STAMP="$(date +%Y%m%d-%H%M%S)"; BK="$HOME/mc-backups/skills"; mkdir -p "$BK"
for n in "${NAMES[@]}"; do
  [ -f "$REPO/skills/$n/SKILL.md" ] || { echo "[install] STOP: unknown skill $n"; exit 1; }
  # hidden folders below the skills dir (.hub, .archive) are skipped; ~/.hermes itself is fine
  cur="$(cd "$SKILLS" && find . -maxdepth 4 -path "*/$n/SKILL.md" -not -path "*/.*/*" 2>/dev/null | head -1)"
  if [ -n "$cur" ]; then
    dest="$SKILLS/$(dirname "${cur#./}")"; mv "$dest" "$BK/$n-$STAMP"; echo "[install] $n: old copy -> $BK/$n-$STAMP"
  else
    dest="$SKILLS/mahareka/$n"; mkdir -p "$(dirname "$dest")"
  fi
  cp -R "$REPO/skills/$n" "$dest"
  if [ "$n" = "bq-error-checker" ]; then BQ_DEST="$dest"; fi
  "$PY" "$REPO/skills/mahareka-skill-builder/scripts/icm_check.py" "$dest" >/dev/null \
    || { echo "[install] STOP: icm_check failed on $dest (old copy is in $BK)"; exit 1; }
  find "$dest" -name __pycache__ -prune -exec rm -rf {} +
  echo "[install] $n: installed at $dest ($(grep -oE 'version \*\*[0-9.]+\*\*' "$dest/SKILL.md" | head -1 | tr -d '*'))"
done
# paths as the installed skill sees them (it looks for mahareka-qs-agent next to itself)
"$PY" "${BQ_DEST:-$REPO/skills/bq-error-checker}/_tools/where.py"
echo "[install] done"
