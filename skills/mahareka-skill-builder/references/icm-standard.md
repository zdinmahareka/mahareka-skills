# Mahareka ICM Standard v1.0 — how a complex skill is shaped

ICM (Interpretable Context Methodology): the folder structure is the agent's architecture.
Numbered folders carry the order, each folder's `CONTEXT.md` says what it reads, does,
writes and how it is checked, and plain files carry the state. One agent reading the right
file at the right moment replaces a long all-in-one prompt.

Read this at Workflow step 1 (pick the shape) and step 4 (audit). The pilot that proves it
is `bq-error-checker` v2.0; copy from it when unsure.

## 1. Pick the shape from the type

| Type | Shape | Entry `SKILL.md` |
|---|---|---|
| A (style, short procedure) | none: one file | the whole skill |
| B (procedure + fixed knowledge) | **Shelves**: `SKILL.md` + `_shared/` (or `references/`) | the procedure; detail on shelves |
| C, or any procedure with 3+ steps and a pause to check between them | **Pipeline**: stages + run folders | a router only, body ≤ 60 lines |

Argue down, as always. A pipeline for a job done twice is scaffolding, not architecture.
Three real stages beat seven imagined ones. Stage boundaries go where Zaim naturally stops
to check something.

Other ICM forms exist (record library, knowledge bundle, context map, system map). Use one
only when the repeating unit is a record, a body of knowledge, the company, or a codebase;
say why in the root `CONTEXT.md`.

## 2. Pipeline layout

```
<skill>/                       the FACTORY: read-only in a session, stable across runs
├─ SKILL.md                    L0: triggers, identity, "where things live", route-by-task, boundaries
├─ CONTEXT.md                  L1: the pipeline on one screen, plus invariants broken on purpose
├─ stages/
│  ├─ 01_<verb>/CONTEXT.md     L2: one contract per stage
│  └─ 02_<verb>/CONTEXT.md
├─ _shared/                    L3: rules, conventions, lessons, report standards (one home per fact)
├─ _templates/
│  └─ run/                     the stamp of one run: RUN.md + blank output files
└─ _tools/                     new_run.py, gate.py, the engines

RUN = RUNS/<runs_dir>/<date>_<project>/         the PRODUCT: one folder per run
├─ 00_input/                   the files as uploaded, never edited
├─ 01_<verb>/  output + check.md
└─ 02_<verb>/  output + check.md
```

RUN lives outside the skill so runs never mix with the installed skills: RUNS is
`$MAHAREKA_RUNS`, default `~/mahareka-runs`. `new_run.py` makes it and prints its path.
Data the skills read (ratebase, registry, memory workbooks) lives in KNOWLEDGE:
`$MAHAREKA_KNOWLEDGE`, default `~/mahareka-knowledge`. Mahareka skills are for the Hermes
agents only.

## 3. The rules (M1–M10)

- **M1 Entry routes, never holds content.** Pipeline `SKILL.md` body ≤ 60 lines: who it is for,
  where things live, how to start a run, route by task, boundaries. Rules live on shelves.
- **M2 One folder, one job.** Each stage does one step and says so in its first line.
- **M3 Every stage has a contract** (`assets/icm/stage-CONTEXT.md`): `## Inputs` with exact
  paths split into Working (this run, `RUN/…`) and Reference (every run, `SKILL/…`), a
  `Do NOT load:` line, a numbered `## Process`, `## Outputs`, and exactly one `## Check`.
- **M4 Factory apart from product.** Contracts, rules and templates in the skill; everything a
  run produces in RUN. A new run is a copy of `_templates/run/`, never a blank page.
- **M5 Every stage ends at a check.** A script gate writes `RUN/<stage>/check.md`, first line
  `pass` or `fail: <why>`; a fail stops the run. Or the check is a person: Zaim checks the
  first stage (direction) and the last (the deliverable); the middle is scripted.
- **M6 Load only what the step needs:** contract + references + inputs under about 8,000
  tokens. Too big → split the stage or narrow its Inputs; never compress.
- **M7 One home per fact.** A rule is written once, in one `_shared/` file; contracts point
  at it. Across skills the owner rule still applies (`MAHAREKA_STANDARD.md`).
- **M8 Status lives on disk.** What exists in RUN plus each `check.md` is the status;
  `gate.py RUN status` prints it. No status kept anywhere else.
- **M9 Names.** Stages `NN_kebab` from `01`, no gaps. Underscore folders are about the skill,
  not the work. **Only the entry is named `SKILL.md`**: Hermes and Mission Control count every
  `SKILL.md` as a skill, so templates are named `SKILL.entry.md`.
- **M10 No data in the skill.** Memory workbooks stay in KNOWLEDGE (an `.xlsx` is a
  zip and cannot ship inside a skill package). The skill ships rules, contracts, templates
  and tools.

Break a rule only on purpose, and write why under "Invariants broken on purpose" in the root
`CONTEXT.md`. A break with no reason is a defect.

## 4. Converting an existing skill

1. Inventory every file and section. Move nothing yet.
2. Classify each section: catalog → `SKILL.md`; how a step works → a stage `CONTEXT.md`;
   stable rules → `_shared/`; per-run files → `_templates/run/`; stale → say so, never delete.
3. Move text **verbatim**. A reshape never rewrites a rule; rule changes are their own job,
   approved by Zaim. Declared conflicts stay declared (move them to `_shared/conflicts.md`).
4. Keep `name:` and the trigger description identical, so the replacement installs over the
   old skill and still fires.
5. Major version bump. Run `scripts/icm_check.py`, then a real run end to end (G12).

## 5. Walk test (a cold agent, no memory)

1. From `SKILL.md`, can it say where to go for the current task within two more reads?
2. Does every stage contract name exact inputs, the job, the outputs and one check?
3. Can it state a run's status purely from what is on disk?
4. Is any routing file carrying rules? Move them to a shelf.
5. Is any fact in two places? Pick one home.
6. Does `scripts/icm_check.py` pass?

## Credit

Method: Interpretable Context Methodology, Van Clief & McDermott, arXiv:2603.16021 (MIT).
Adapted from `RinDig/icm-architect` (MIT). This standard is Mahareka's adaptation for skills.
