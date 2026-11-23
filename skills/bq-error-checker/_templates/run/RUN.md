---
runs_dir: bq-audit
project: {project}
date: {date}
input: {input}
---
# BQ audit run — {project} ({date})

One BQ audit. Stage folders hold their outputs and a `check.md` each (first line `pass` or
`fail: <why>`); `00_input/` holds the files as uploaded, never edited.
Status: `python3 SKILL/_tools/gate.py <this folder> status`.
