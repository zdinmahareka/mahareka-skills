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

PY=""
for c in python3 py python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys; sys.exit(sys.version_info < (3, 9))" 2>/dev/null; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "[install] STOP: no Python 3.9+ found (python3 / py / python)"; exit 1; }
"$PY" -c "import openpyxl" 2>/dev/null || { echo "[install] STOP: $PY has no openpyxl. Install it with: $PY -m pip install openpyxl"; exit 1; }
echo "[install] python: $PY"

LOG="$(mktemp)"
( cd "$REPO" && "$PY" -m unittest discover -s tests >"$LOG" 2>&1 ) \
  || { echo "[install] STOP: tests failed"; tail -20 "$LOG"; exit 1; }
echo "[install] tests: $(grep -oE 'Ran [0-9]+ tests' "$LOG") OK"
find "$REPO" -name __pycache__ -prune -exec rm -rf {} +

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
  "$PY" "$REPO/skills/mahareka-skill-builder/scripts/icm_check.py" "$dest" >/dev/null \
    || { echo "[install] STOP: icm_check failed on $dest (old copy is in $BK)"; exit 1; }
  find "$dest" -name __pycache__ -prune -exec rm -rf {} +
  echo "[install] $n: installed at $dest ($(grep -oE 'version \*\*[0-9.]+\*\*' "$dest/SKILL.md" | head -1 | tr -d '*'))"
done
"$PY" "$REPO/skills/bq-error-checker/_tools/where.py"
echo "[install] done"
