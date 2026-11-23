# <Skill> pipeline — one screen

One run = <the repeating unit>. <N> stages, each ending at a check.

| Stage | Job | Output (in RUN) | Check |
|---|---|---|---|
| `stages/01_<verb>/` | <job> | `01_<verb>/<file>` | Zaim / `gate.py RUN 01` |

**Order matters:** <why each stage comes before the next>.

**Status lives on disk.** Each stage folder in RUN holds `check.md`, first line `pass` or
`fail: <why>`.

## Invariants broken on purpose

- Contract inputs use `RUN/…` and `SKILL/…`: the skill folder is read-only in a session, so
  each run lives outside it. `new_run.py` prints RUN.
