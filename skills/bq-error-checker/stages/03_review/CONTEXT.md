# 03_review — judge every finding before Zaim sees it

One job: decide, for every script finding, whether it is real, and add the judgment layers
the scripts cannot do. A false accusation against a subcon costs more than a missed flag.

## Inputs
- Working (this run): `RUN/01_intake/intake.md`
- Working (this run): `RUN/02_checks/findings.json`, `RUN/02_checks/rates.json` (if present)
- Working (this run): any drawing or subcon quote in `RUN/00_input/` (Layer E only)
- Reference (every run): `SKILL/_shared/taxonomy.md`
- Reference (every run): `SKILL/_shared/conventions.md`
- Reference (every run): `SKILL/_shared/lessons.md`
- Reference (every run): `SKILL/_shared/conflicts.md`
- Reference (when `rates.json` exists): `SKILL/_shared/learning.md`

Do NOT load: `_shared/reporting.md` (stage 04), the whole BQ again (use the lines in
`findings.json`), other runs.

## Process
1. Read lessons and conflicts **before** interpreting any flag.
2. For each finding id in `findings.json` and `rates.json`, write one table row in
   `review.md`: id, line, what it is, decision, reason. Decision is one of:
   - `KEEP` (real, goes in the report), `DOWNGRADE` (real, minor or advisory),
   - `DROP` (false alarm: name the rule that clears it, e.g. lesson 14 annotation, lesson 4
     pro-rata coincidence),
   - `ASK` (only Zaim can decide: margin below 1.5×, install-only markup, cost basis).
3. Pro-rata first: before any grade-mismatch or overcharge decision on a subcon rate, test
   pro-rata at the specified grade (`_shared/taxonomy.md`, Layer E).
4. Systematic shift in `rates.json` → one collective advisory ("request latest pricelist");
   downgrade the individual band flags it explains.
5. Add judgment-only findings with new ids `J01…`: Layer B room-to-room consistency,
   Layer D margin (only with cost data), Layer E cross-reference (only with a drawing or
   quote), and in Mode 2 Layer G (cost drivers, scope gaps, quantity plausibility, VE,
   budget target, comparison).
6. Any `ASK` → list the questions under `## Questions for Zaim` (one round).

## Outputs
- `review.md` → `RUN/03_review/` (copied from the stamp; one row per id)

## Check
`python3 SKILL/_tools/gate.py RUN 03` — passes when every `F`/`R` id from stage 02 appears
in `review.md` with a decision. No unreviewed flag reaches the report.
