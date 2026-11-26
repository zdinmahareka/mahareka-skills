# 04_report — present it as a QS would to the Commercial Director

One job: turn the reviewed findings into the report for the mode set at intake, and hand
over what was learned.

## Inputs
- Working (this run): `RUN/01_intake/intake.md` (mode, depth, project)
- Working (this run): `RUN/03_review/review.md` (only `KEEP`, `DOWNGRADE`, `ASK` and `J` rows
  are reported; `DROP` rows appear only as a count)
- Working (this run): `RUN/02_checks/findings.json` (`info` block: lines, sections, total)
- Working (this run): `RUN/02_checks/rates.json` (`gaps`, `matched`, `source`: for the handover)
- Reference (Mode 1): `SKILL/_templates/report-mode1.md`
- Reference (Mode 2): `SKILL/_shared/reporting.md`, read in full before writing

Do NOT load: `_shared/lessons.md`, `_shared/learning.md`, the raw BQ, other runs.

## Process
1. Write `report.md` in the mode from `intake.md`. Never blend the modes.
2. Show problem lines only, never a full BQ dump. A clean section gets one line, never a
   manufactured finding. Rank flags by RM impact; a line selling at or below verified cost
   ranks first.
3. State every unresolved gate explicitly: **"Gate pending — [what's needed]."**
4. Where a subcon needs to clarify, add a WhatsApp-ready question draft (draft only; Zaim
   sends).
5. Handover, at the end of the report. This skill stores no rate (one ratebase):
   - list every **ratebase gap** from `rates.json` and every rate that changed (item, spec,
     UOM, rate, basis, vendor, project, date) under "For the ratebase", for
     `mahareka-qs-agent` to store as pending on Zaim's word; give the counts (rates compared,
     gaps, flags, resolutions) and which ratebase file they were compared with;
   - list how each rate flag was resolved (confirmed error / false alarm / genuine change);
   - if Zaim corrected a flag or taught a rule, give the exact line to add to
     `_shared/lessons.md` at the next re-package;
   - if any rate or rule was added to `QS_RATEBASE`, end by telling Zaim to download the
     published file, install it into KNOWLEDGE, and delete the old version. Never
     assume it was done (30 Jul 2026: published, never installed, stale answers followed).

## Outputs
- `report.md` → `RUN/04_report/`

## Check
Zaim reads the report. His corrections are made in place in `report.md`, and any rule he
teaches goes to the lessons line in step 5.
