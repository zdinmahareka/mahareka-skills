---
name: bq-error-checker
description: Mahareka BQ/BOQ review, audit, error checking and commercial review, with a self-learning rate memory (RateBase). Use this skill WHENEVER the user uploads a Bill of Quantities, BQ, BOQ, quotation, subcon quote, or costing sheet (xlsx or PDF) and asks to check, review, audit, verify, semak, analyse, or "ada error tak" — including casual phrasing like "tolong tengok BQ ni", "betul ke harga ni", or just "audit this". Also use when the user asks whether anything is overpriced or underpriced, asks about rate anomalies, price trends, markup checks, weird or suspicious quantities, arithmetic, cost drivers, or which items carry most of the project value; when comparing two or more BQs or quotations; and for Value Engineering requests — "find VE", "value engineer this", "how can we reduce this quotation", "buat option RM90k", "create budget option", "kurangkan harga ni". Covers all trades, not just built-in furniture.
---

# Mahareka BQ Error Checker — entry and routing

Audits a BQ or quotation and presents the findings as a QS would to the Commercial Director.
**User = Zaim, Commercial Director, Mahareka Construction. All amounts MYR. Reply in the user's
language (natural BM + English technical terms, or English). Output-first, no filler.**

Skill version **2.0** — rebuilt to the Mahareka ICM Standard (Interpretable Context
Methodology). Rules, taxonomy and report formats are unchanged from v1.1; they moved to
`_shared/` and the workflow moved into four checked stages.

## Where things live

| Folder | Holds | Changes |
|---|---|---|
| `CONTEXT.md` | the pipeline on one screen | rarely |
| `stages/NN_*/CONTEXT.md` | one contract per stage: inputs, process, outputs, check | rarely |
| `_shared/` | the factory: taxonomy, conventions, lessons, learning, reporting, conflicts | on re-package |
| `_templates/` | blank stamps: `run/` (a new audit) and `report-mode1.md` | rarely |
| `_tools/` | `new_run.py`, `check_bq.py`, `rate_learn.py`, `gate.py` | on re-package |
| **RUN** (outside the skill) | the product: one folder per audit, made by `new_run.py` | every audit |

Rates are never in this skill. `QS_RATEBASE` (owned by `mahareka-qs-agent`) and
`Rate_History.xlsx` live in project knowledge.

## Start here

1. Make the run folder, then work stage by stage:
   `python3 SKILL/_tools/new_run.py --project <code> --input <file>` (SKILL = this skill's
   folder). It prints RUN.
2. Read `CONTEXT.md`, then only the contract of the stage you are on.
3. After each stage: `python3 SKILL/_tools/gate.py RUN <stage>`. A fail stops the run.
4. Where am I? `python3 SKILL/_tools/gate.py RUN status`.

## Route by task

| Task | Go to |
|---|---|
| Any BQ check, audit, VE, budget option, comparison | `CONTEXT.md` → `stages/01_intake/` |
| What counts as an error | `_shared/taxonomy.md` |
| Mahareka BQ rules (UOM, rounding, markup, grades) | `_shared/conventions.md` |
| Known error patterns | `_shared/lessons.md` |
| Rate memory protocol (Layer F) | `_shared/learning.md` |
| Mode 2 report standard | `_shared/reporting.md` |
| Known conflicts with other skills | `_shared/conflicts.md` |

## Boundaries

Pricing and rate build-ups → `mahareka-qs-agent`. Site reports and programme →
`site-lookahead-v2`. Building or auditing skills → `mahareka-skill-builder`. This skill
audits BQ documents and presents the commercial review.
