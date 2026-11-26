---
name: mahareka-skill-builder
description: Builds new Claude skills for Mahareka to the house standard, and audits existing ones. Use whenever the user wants to create, design, scaffold, plan, review, fix, or version a skill — "buat skill baru", "nak buat skill untuk X", "create a skill", "audit my skills", "check skill ni betul tak", "skill ni kenapa tak trigger", "tambah memory dalam skill". Also use when deciding whether something should be a skill at all, when a skill needs converting to the two-layer architecture, when two skills contradict each other, or when packaging a skill for backup or transfer to another Claude account. Covers all Mahareka domains, not just QS.
---

# Mahareka Skill Builder

**User = Zaim, Commercial Director, Mahareka Construction. Reply in the user's language (BM natural + English technical, or English). Generated skills: English instructions, EN + BM triggers. Output-first, tables for comparisons.**

## Architecture — read this first

This skill is the **instruction layer** plus, since v2.0, the **ICM method**. It ships no Mahareka data.
The standard and the registry live in the **KNOWLEDGE folder** already on each Hermes machine (`$MAHAREKA_KNOWLEDGE`, else `~/mahareka-knowledge`, else `~/mahareka-shared/Work/mahareka-knowledge`; never an archive or download copy; never copy or move it) — the layer Zaim replaces himself. Since v2.2 the engines ship in this skill's `scripts/` (they are static code and hold no data). Hermes agents only. **PY** = the Python recorded in `~/.mahareka/python` (it has openpyxl); use `py` where that is the Python command.

```
SKILL (this folder)   instructions · frozen · changes only on a version bump
  references/icm-standard.md   the Mahareka ICM Standard (shape of complex skills)
  assets/icm/                  pipeline starters: SKILL.entry.md, CONTEXT.root.md, stage-CONTEXT.md, run/, _tools/, README.md
  assets/type-a/ · type-b/     one-file and shelves starters
  scripts/sb_boot.py           bootstrap: run first
  scripts/new_skill.py         a new skill from the starters, in the right shape
  scripts/skill_check.py       audit against the 11 principles
  scripts/icm_check.py         structure checker for rules M1–M11
  scripts/registry.py          staged, append-only registry updates
KNOWLEDGE FOLDER     MAHAREKA_STANDARD.md
  = the live layer    SKILL_REGISTRY.xlsx   ← the memory that learns
```

The ICM files are method, not data: they hold no rates, names or project facts, so they ship with the skill.

The split is forced as well as chosen: an `.xlsx` is a zip archive internally (`PK\x03\x04`), so a skill package containing the registry is rejected with *"Zip cannot contain nested zip files"*. Workbook memory can never ship inside a skill.

Version expected: **1.0**. Builder version **2.3** (2.0 added the ICM layer; 2.1 added rule M11 and gate G14: every skill has a `README.md` for people; 2.2 runs on Hermes: the engines moved into `scripts/`, `new_skill.py` replaces `skill_scaffold.py`, and registry updates are staged for Zaim; 2.3 keeps two lessons learned on MatDuo: when not to convert a skill, and how to triage `skill_check.py` findings; the standard version is unchanged). The builder follows every rule it enforces — if it ever violates the standard, that is a defect, not an exception.

## The loop

```
Build or audit a skill
  → register it in PORTFOLIO, log the audit in AUDIT_LOG
  → what broke goes to LESSONS, what worked goes to PATTERNS,
    triggers that fired go to TRIGGERS
  → registry.py writes SKILL_REGISTRY.staged.xlsx beside the registry
  → Zaim replaces SKILL_REGISTRY.xlsx with it in KNOWLEDGE FOLDER
  → the next skill is built better
```

Never tell Zaim to replace anything "in the skill" — the skill holds no data. Always say **the KNOWLEDGE folder**.

## Workflow

0. **Bootstrap first, every session.** `PY scripts/sb_boot.py` (from this skill's folder)
   Verifies the tools in this skill and the live layer in the KNOWLEDGE folder, reports registry state and portfolio health (which skills are blocked or unregistered), and warns when a staged registry has not been replaced yet. DEGRADED → name the missing files and **stop**. Never build or audit from memory.

1. **Classify before building.** Read `MAHAREKA_STANDARD.md` in the KNOWLEDGE folder (`sb_boot.py` prints where it is), then ask the four classification questions:
   1. Does it produce a number, rate, or decision that must be reproducible months later?
   2. Does using it create knowledge the next use should inherit?
   3. Does it need fixed knowledge longer than ~200 lines?
   4. Otherwise → Type A.

   | Type | Ships | Subtypes |
   |---|---|---|
   | A | SKILL.md only | A1 style/format · A2 procedure |
   | B | SKILL.md + static references | B1 knowledge · B2 template/output spec |
   | C | SKILL.md + engines + memory + bootstrap | C1 memory agent · C2 auditor · C3 producer |

   **Then pick the shape** (`references/icm-standard.md`, section 1): Type A → one file · Type B → shelves (`SKILL.md` + `_shared/`) · Type C, or any procedure with 3+ steps and a pause to check between them → **ICM Pipeline** (router `SKILL.md`, root `CONTEXT.md`, stage contracts, a run stamp, run folders outside the skill, a gate per stage).

   **Actively argue Zaim down a type when the evidence says so.** Building Type C for a Type A problem adds files that can go missing, drift, and contradict other skills. `site-lookahead-v2` is correctly Type B despite heavy output — it has no growing memory. Say so plainly and give the reason.

   **The same applies to converting.** Do not reshape a working, verified skill into ICM for the shape alone. For example, `mahareka-qs-agent` boots INTACT and its selftest passes. ICM changes the layout, not the accuracy, and reshaping a live skill puts its data at risk. Convert only when there is a real failure between steps, or when Zaim wants formal checkpoints. Inside a skill, keep quick lookups out of the stages: only multi-step jobs belong in the pipeline.

2. **Gather the answers, batched into ONE round.** Name · purpose in one clause · trigger phrasings EN and BM including casual typing · what it must never do · boundary against neighbouring skills · for Type C: what the memory stores, its schema, and one regression case with a known answer.

3. **Build from the starters.**
   ```
   PY scripts/new_skill.py --name mahareka-<domain>-<function> --type C \
     --purpose "..." --triggers-en "..." --triggers-bm "..." \
     --stages intake,work,report [--register]
   ```
   It writes the right shape into the skills folder this machine recorded (`<skills dir>/mahareka/<name>/`): Type A → one file, Type B → `SKILL.md` + `_shared/`, Type C → an ICM Pipeline (router, `CONTEXT.md`, one contract per stage, the run stamp, `new_run.py`, a starter `gate.py`). Every shape gets a `README.md` with its sections. It refuses when the name already exists, fills name and description, and runs `icm_check.py` on the result. Everything left as `<placeholder>` is yours to write, following `references/icm-standard.md`. Never hand-build the folder layout when `new_skill.py` can make it. Reference build: `bq-error-checker` v2.0.

   A Type C skill's memory workbook is not created here: it belongs in the KNOWLEDGE folder, and Zaim puts it there (rule M10). `skill_scaffold.py` (Claude Projects) is retired on Hermes.

4. **Audit.** `PY scripts/skill_check.py <path>` — or `--all` for every skill in the folder this machine recorded (`--all <folder>` for another one).
   Reports BLOCKER / WARN / INFO against the 11 principles plus cross-skill rule conflicts and the README rule. Exit 1 on any blocker. Run it on every new skill before handing over, and re-run `--all` whenever a shared rule changes. `--log` stages one AUDIT_LOG row per skill.

   **Triage the findings before you report them.** The 11 principles were written for Claude-zip packaging and moved to Hermes unchanged, so many of its blockers do not apply on Hermes:
   - **P2 "no bootstrap":** it tags every skill that has a `.py` file as Type C. Check whether the skill already has `gate.py`, `tests/` or a selftest before you call this real.
   - **P1 "memory shipped inside":** on Hermes the skill folder is writable, and the tool counts `config.json`, `examples/*.xlsx` and run templates as memory. Report only true growing data.
   - **mahareka-qs-agent's in-skill ratebase:** this is Zaim's decision (one ratebase, MatDuo only). Report it as an unrecorded "invariant broken on purpose", not as a defect.
   - **Real risk:** CROSS findings (stale owned rules such as flat RM5 rounding, or a second rate memory), missing BM triggers (the skill may not fire), and no decision-authority statement.

   Report shape for Zaim:
   - the verdict and totals
   - 🔴 real risk
   - 🟡 cheap fixes
   - ⚪ tool noise and why
   - ordered recommendations, each waiting for approve
   - the full findings as a white-filled `.xlsx` with SUMMARY and FINDINGS tabs

   Remediation of any skill is its own approved job.

   ICM structure: `PY scripts/icm_check.py <path>` (or `--all <folder>`, from this skill's folder). Checks M1–M11: a `README.md` with its five sections, one `SKILL.md` only, contracts complete with exactly one Check, stage numbering, paths that resolve, ~8k tokens per stage. Exit 1 on any blocker.

5. **Verify by running, not by reading.** Copy the skill into a clean folder, run its bootstrap or first tool there, and run its acceptance test. A package that has not been executed has not been tested.

6. **Register — append-only.** Add the skill to PORTFOLIO (`PY scripts/registry.py add-skill …`, or `new_skill.py --register`), the run to AUDIT_LOG (`skill_check.py --log`), anything that broke to LESSONS (`registry.py lesson …`), new patterns to PATTERNS. The tools never write the registry: they stage `SKILL_REGISTRY.staged.xlsx` beside it and print the replace instruction; relay it to Zaim.

   **Never delete a registry row.** A retired or merged skill is marked `STATUS=SUPERSEDED` with a pointer to its replacement and stays in PORTFOLIO — the audit history is the only record of how the portfolio got here. AUDIT_LOG is strictly append-only: one row per skill per run, so drift is visible over time.

   Registry STATUS vocabulary: `VERIFIED` (audited in place and passing) · `BUDGETARY` (scaffolded, not yet audited where it runs) · `PENDING` (awaiting Zaim's decision, e.g. remediation approval) · `SUPERSEDED` (retired or merged, row retained).

7. **Ship gates.** Before handing any skill over, clear the 14 gates (G1–G12 in the registry's GATES tab, plus G13 and G14) — G1 archetype justified, G2 triggers, G3 two layers, G4 bootstrap (the skill's own first tool runs on this Hermes machine and stops loudly when something is missing), G5 loud failure, G6 write path, G7 append-only, G8 no hardcoded data, G9 decision authority, G10 regression passes, G11 no stale owned rules, G12 restored and executed (copied into a clean folder on a Hermes machine and run there), **G13 ICM shape** (Type B/C: the shape matches the type and `icm_check.py` passes; new in v2.0 — add the G13 row to the registry's GATES tab at the next publish), **G14 README** (the skill has `README.md` with Purpose, What, Why, When, How, plus Using it and Maintaining it, written from the skill's own files; `icm_check.py` fails a skill without it; new in v2.1 — add the G14 row at the next publish). State `Gate Gx pending — [what is needed]` in the output whenever one is unresolved. G12 is not optional: a package that has not been executed has not been tested.

8. **Decision authority.** Builder decides alone: archetype recommendation, file layout, trigger wording, scaffold output, audit findings. **ALWAYS ASK ZAIM:** overriding a recommended archetype, remediating an existing skill (it is disruptive and belongs in its own job), changing a rule owned by another skill, retiring or merging a skill, anything that edits `mahareka-qs-agent` or its ratebase.

## Cross-skill consistency

One skill owns each shared rule; others reference the owner by name and never restate the value. Current owners are listed in `MAHAREKA_STANDARD.md`. When a rule changes, run `PY scripts/skill_check.py --all` — stale copies surface as CROSS blockers.

Known open conflict at v1.0: `bq-error-checker` maintains a second rate memory beside `QS_RATEBASE.xlsx` and carries the retired flat MROUND-5 rounding in three files. Logged, remediation not yet approved. **Do not fix it as a side effect of another task.** `bq-error-checker` v2.0 (the ICM pilot) moved these conflicts verbatim to `bq-error-checker/_shared/conflicts.md`; they are still open.

## What this skill will not do

- Write project instructions or account profiles — v1 covers skills only
- Generate a skill without a stated purpose and triggers — that produces a skill that never fires
- Ship a Type C package without a regression case — there would be no way to prove it still works
- Silently repair another skill

## Boundaries

Pricing and rate questions → `mahareka-qs-agent`. BQ document audits → `bq-error-checker`. Site reports → `site-lookahead-v2`. This skill builds and audits skills; it does not do their work.
