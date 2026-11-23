---
name: mahareka-<domain>-<function>
description: <what it does, in one clause>. Use whenever <EN triggers, including casual typing> — "<BM trigger>", "<BM trigger>". Also use when <neighbouring situations>.
---

# <Skill title> — entry and routing

<One line: what it produces and for whom.> **User = Zaim, Commercial Director, Mahareka
Construction. Reply in the user's language (BM natural + English technical, or English).**

Skill version **1.0** — built to the Mahareka ICM Standard.

## Where things live

| Folder | Holds | Changes |
|---|---|---|
| `CONTEXT.md` | the pipeline on one screen | rarely |
| `stages/NN_*/CONTEXT.md` | one contract per stage | rarely |
| `_shared/` | the factory: rules, conventions, standards | on re-package |
| `_templates/run/` | the stamp of one run | rarely |
| `_tools/` | `new_run.py`, `gate.py`, engines | on re-package |
| **RUN** (outside the skill) | the product: one folder per run | every run |

## Start here

1. `PY SKILL/_tools/new_run.py --project <code> --input <file>` prints RUN.
2. Read `CONTEXT.md`, then only the contract of the stage you are on.
3. After each stage: `PY SKILL/_tools/gate.py RUN <stage>`. A fail stops the run.

## Route by task

| Task | Go to |
|---|---|
| <task> | `stages/01_<verb>/` |

## Boundaries

<neighbour skill> → `<name>`. This skill does <one thing>.
