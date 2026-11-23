# 01_intake — know what you are auditing before you audit it

One job: fill `RUN/01_intake/intake.md` so every later stage reads facts, not guesses.

## Inputs
- Working (this run): `RUN/00_input/` (the BQ as uploaded; also any subcon quote or drawing)
- Working (this run): `RUN/01_intake/intake.md` (blank stamp made by `new_run.py`)
- Reference (every run): `SKILL/_shared/conventions.md` (sections: Column standard, Annotation rules)

Do NOT load: `_shared/reporting.md`, `_shared/lessons.md`, rate memory, other runs.

## Process
1. **xlsx:** list the sheets. Pick the ACTIVE BQ sheet (names vary: `KOSONG`, `New`,
   `No Rate`, `BQ CLIENT`, `PHASE 1-4`). Ignore legacy sheets from old projects. If two sheets
   could be the active one, ask.
   **PDF:** reconstruct a clean table (Item | Description | Qty | Unit | Rate | Amount) into
   `RUN/01_intake/reconstructed.xlsx`, and set `sheet:` to its sheet name.
2. **Set the mode** (never blend them):
   - Mode 1 (Verification): "check errors", "semak", "ada error tak", "verify", subcon quote
     validation, xlsx integrity.
   - Mode 2 (Commercial Audit): "audit this", "review this quotation", "is anything
     overpriced", "find VE", "compare these BQs", "cost drivers", "make RM90k option".
   - Genuinely ambiguous → Mode 2 (it contains Mode 1's checks).
3. **Set the depth:** `management` by default; `full` only on "full audit", "deep audit",
   "audit everything", "audit all rates", "detailed QS audit".
4. **Set the basis** (`SELL` for a client BQ, `COST` for a subcon quote), the subcon, and
   any budget target or comparison file.
5. **Ask, don't guess.** Unclear sheet, units, cost vs sell basis, missing drawing,
   unstated unit height or depth → write every question under `## Open questions`, set
   `open_questions:` to the count, and ask Zaim **once**, in one consolidated round. When he
   answers, write each answer under its question and set `open_questions: 0`.

## Outputs
- `intake.md` → `RUN/01_intake/` (frontmatter: project, file, sheet, mode, depth, basis,
  subcon, budget_target, compare_with, open_questions)

## Check
`PY SKILL/_tools/gate.py RUN 01` — passes when file, sheet, mode, depth and basis are set
and `open_questions: 0`. While questions are open, the run waits for Zaim.
