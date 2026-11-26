# BQ audit pipeline — one screen

One run = one BQ (or one set of BQs being compared). Four stages, each ending at a check.

| Stage | Job | Output (in RUN) | Check |
|---|---|---|---|
| `stages/01_intake/` | pick the sheet, set mode and depth, ask every question once | `01_intake/intake.md` | `gate.py RUN 01`; Zaim answers open questions |
| `stages/02_checks/` | run the scripts: bootstrap the rate authority, then Layers A–C | `02_checks/findings.json`, `boot.txt` | `gate.py RUN 02` |
| `stages/03_review/` | judge every finding: Layers B, D, E, F, G | `03_review/review.md` | `gate.py RUN 03` (every finding has a decision) |
| `stages/04_report/` | write the Mode 1 or Mode 2 report, hand over what was learned | `04_report/report.md` | Zaim reads the report |

**Order matters:** intake before scripts (wrong sheet = wrong audit), scripts before judgment
(judge evidence, not impressions), judgment before report (no unreviewed flag reaches Zaim).

**Status lives on disk.** Each stage folder in RUN holds `check.md`, first line `pass` or
`fail: <why>`. A stage with no `check.md` has not been checked. Never skip a failed gate.

**Human editing is heavy at both ends.** Zaim corrects intake (sheet, mode, basis) and the
report. The middle is scripted and constrained by both.

## Invariants broken on purpose

- Contract inputs use `RUN/…` and `SKILL/…` instead of relative paths. The skill folder is
  part of the agent's installed skills, so each run lives outside it, in RUNS/bq-audit/
  (`_tools/where.py`). `new_run.py` prints RUN.
- The raw input is copied into `RUN/00_input/` and never edited; stages read it from there.
