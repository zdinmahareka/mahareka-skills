# bq-error-checker: README

Version 2.1 · desk: Hakim (Commercial & QS) · Hermes agents only · owner: Zaim

## Purpose
Check a BQ, BOQ, quotation, subcon quote or costing sheet before it goes out or gets accepted,
and present the findings the way a QS would to the Commercial Director.

## What it does
- Audits one document, or compares several: arithmetic, quantities, units, rates against
  the one ratebase, known error patterns, and the items that carry most of the value.
- Covers value engineering and budget options on the same evidence ("find VE", "buat option
  RM90k").
- Writes a report in one of two modes. Rates the ratebase does not hold, or that changed, are
  listed in the report for `mahareka-qs-agent` to store. This skill stores no rate.
- It never quotes a rate from its own files. The benchmark is `QS_RATEBASE` only (owned by
  `mahareka-qs-agent`), read through that skill's own engines.
- It does not build prices. Pricing and rate build-ups belong to `mahareka-qs-agent`.

## Why it exists
A wrong BQ costs money either way: a missed error is paid for, and a false accusation against
a subcon damages the relationship. The check has to be the same every time, judge evidence and
not impressions, and never let an unreviewed flag reach Zaim. Version 2.0 put the work into
four checked stages so that each step can be seen and repeated. Version 2.1 retired the skill's
own rate history, so there is one ratebase and no second set of rates growing beside it.

## When it runs
- When Zaim sends a BQ or quotation (xlsx or PDF) and asks to check, review, audit, verify or
  "semak", or asks "ada error tak", "betul ke harga ni".
- When he asks whether something is overpriced or underpriced, about rate anomalies, markup,
  odd quantities, or cost drivers.
- When he wants two or more BQs compared, or a VE or budget option.
- It is not scheduled. It runs only when asked.

## How it works
1. `_tools/where.py` finds the Python to use, the KNOWLEDGE folder and the RUNS folder.
2. `_tools/new_run.py` makes one run folder per audit, outside the skill, and copies the input
   there untouched.
3. Four stages, each with a contract in `stages/NN_*/CONTEXT.md` and a gate (`_tools/gate.py`):
   **01 intake** (pick the sheet, set mode and depth, ask every question once) → **02 checks**
   (bootstrap the rate authority, then the scripts) → **03 review** (every finding gets a
   decision; rates are compared against the ratebase) → **04 report** (the report, and the
   list of rates for the ratebase).
4. A failed gate stops the run. Status is whatever is on disk in the run folder.

## Using it (Zaim)
Send the file and say what you want: a check, a comparison, or an option at a target figure.
Answer the intake questions once. Read the report. If it lists rates "for the ratebase", tell
Hakim which ones to store: they go into the ratebase through `mahareka-qs-agent`, as pending.

## Maintaining it
- The pipeline on one screen: `CONTEXT.md`. Rules: `_shared/conventions.md` and
  `_shared/taxonomy.md`. Known error patterns: `_shared/lessons.md`. Rate memory protocol:
  `_shared/learning.md`. Report standard: `_shared/reporting.md`.
- Conflicts with other skills are declared in `_shared/conflicts.md`. Two were resolved in
  2.1 on Zaim's decision (the second rate memory, the old rounding rule); the rest stay
  declared until he approves a fix. They are never fixed as a side effect.
- The source is the `mahareka-skills` repo. Tests: `tests/test_bq_pipeline.py` (a full run on a
  synthetic BQ), `tests/test_rules_kept.py` (safety lines that must never be dropped) and
  `icm_check.py`.
- Changing a rule needs Zaim's approval and a version bump. Keep `name:` and the description
  stable so a new version installs over the old one.
