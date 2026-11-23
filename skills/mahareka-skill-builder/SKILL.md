---
name: mahareka-skill-builder
description: Builds new Claude skills for Mahareka to the house standard, and audits existing ones. Use whenever the user wants to create, design, scaffold, plan, review, fix, or version a skill — "buat skill baru", "nak buat skill untuk X", "create a skill", "audit my skills", "check skill ni betul tak", "skill ni kenapa tak trigger", "tambah memory dalam skill". Also use when deciding whether something should be a skill at all, when a skill needs converting to the two-layer architecture, when two skills contradict each other, or when packaging a skill for backup or transfer to another Claude account. Covers all Mahareka domains, not just QS.
---

# Mahareka Skill Builder

**User = Zaim, Commercial Director, Mahareka Construction. Reply in the user's language (BM natural + English technical, or English). Generated skills: English instructions, EN + BM triggers. Output-first, tables for comparisons.**

## Architecture — read this first

This skill is the **instruction layer** plus, since v2.0, the **ICM method**. It ships no Mahareka data.
Every Mahareka engine, template and the registry live in **project knowledge** (`/mnt/project/`) — the layer Zaim replaces himself.

```
SKILL (this folder)   instructions · frozen · changes only on a version bump
  references/icm-standard.md   the Mahareka ICM Standard (shape of complex skills)
  assets/icm/                  starters: SKILL.entry.md, CONTEXT.root.md, stage-CONTEXT.md, run/, _tools/new_run.py
  scripts/icm_check.py         structure checker for rules M1–M10
PROJECT KNOWLEDGE     sb_boot.py · skill_scaffold.py · skill_check.py
  = the live layer    MAHAREKA_STANDARD.md · TYPE_A/B/C templates
                      SKILL_REGISTRY.xlsx   ← the memory that learns
```

The ICM files are method, not data: they hold no rates, names or project facts, so they ship with the skill.

The split is forced as well as chosen: an `.xlsx` is a zip archive internally (`PK\x03\x04`), so a skill package containing the registry is rejected with *"Zip cannot contain nested zip files"*. Workbook memory can never ship inside a skill.

Version expected: **1.0**. Builder version **2.0** (adds the ICM layer; the standard version is unchanged). The builder follows every rule it enforces — if it ever violates the standard, that is a defect, not an exception.

## The loop

```
Build or audit a skill
  → register it in PORTFOLIO, log the audit in AUDIT_LOG
  → what broke goes to LESSONS, what worked goes to PATTERNS,
    triggers that fired go to TRIGGERS
  → skill_scaffold publishes an updated SKILL_REGISTRY.xlsx to outputs
  → Zaim replaces it in PROJECT KNOWLEDGE
  → the next skill is built better
```

Never tell Zaim to replace anything "in the skill" — the skill holds no data. Always say **project knowledge**.

## Workflow

0. **Bootstrap first, every session.** `python3 /mnt/project/sb_boot.py`
   Verifies the live layer, checks version drift, reports registry state and portfolio health (which skills are blocked or unregistered). DEGRADED → name the missing files and **stop**. Never scaffold or audit from memory.

1. **Classify before building.** Read `/mnt/project/MAHAREKA_STANDARD.md`, then ask the four classification questions:
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

2. **Gather the answers, batched into ONE round.** Name · purpose in one clause · trigger phrasings EN and BM including casual typing · what it must never do · boundary against neighbouring skills · for Type C: what the memory stores, its schema, and one regression case with a known answer.

3. **Scaffold.**
   ```
   python3 /mnt/project/skill_scaffold.py --name mahareka-<domain>-<function> \
     --type C --subtype C1 --purpose "..." --triggers-en "..." --triggers-bm "..." \
     --memory NAME_MEMORY.xlsx --columns "ID|ITEM|..." --regression "input -> expected"
   ```
   Output is a complete package that **passes its own bootstrap and skill_check on day one** — populated SKILL.md, working engine, memory with real schema, `<short>_boot.py`, INSTALL.md with an acceptance test, SYSTEM_MAP.md, MANIFEST.md with SHA-256. Never hand-write a skill package when the scaffold can generate it.

   **ICM shape:** `skill_scaffold.py` v1.0 does not yet emit stages. For a Pipeline: scaffold as usual, then reshape with the starters in `assets/icm/` (copy, fill, rename `SKILL.entry.md` → `SKILL.md`), following `references/icm-standard.md`. Reference build: `bq-error-checker` v2.0.

4. **Audit.** `python3 /mnt/project/skill_check.py <path>` — or `--all` for the portfolio.
   Reports BLOCKER / WARN / INFO against the 11 principles plus cross-skill rule conflicts. Exit 1 on any blocker. Run it on every generated package before handing over, and re-run `--all` whenever a shared rule changes.

   ICM structure: `python3 scripts/icm_check.py <path>` (or `--all <folder>`, from this skill's folder). Checks M1–M10: one `SKILL.md` only, contracts complete with exactly one Check, stage numbering, paths that resolve, ~8k tokens per stage. Exit 1 on any blocker.

5. **Verify by running, not by reading.** Restore the package into a clean folder, run its bootstrap, and run its acceptance test. A package that has not been executed has not been tested.

6. **Register — append-only.** Add the skill to PORTFOLIO, the run to AUDIT_LOG, new patterns to PATTERNS, anything that broke to LESSONS. The scaffold stages and publishes the registry; relay the replace instruction.

   **Never delete a registry row.** A retired or merged skill is marked `STATUS=SUPERSEDED` with a pointer to its replacement and stays in PORTFOLIO — the audit history is the only record of how the portfolio got here. AUDIT_LOG is strictly append-only: one row per skill per run, so drift is visible over time.

   Registry STATUS vocabulary: `VERIFIED` (audited in place and passing) · `BUDGETARY` (scaffolded, not yet audited where it runs) · `PENDING` (awaiting Zaim's decision, e.g. remediation approval) · `SUPERSEDED` (retired or merged, row retained).

7. **Ship gates.** Before handing any skill over, clear the 13 gates (G1–G12 in the registry's GATES tab, plus G13) — G1 archetype justified, G2 triggers, G3 two layers, G4 bootstrap, G5 loud failure, G6 write path, G7 append-only, G8 no hardcoded data, G9 decision authority, G10 regression passes, G11 no stale owned rules, G12 restored and executed, **G13 ICM shape** (Type B/C: the shape matches the type and `icm_check.py` passes; new in v2.0 — add the G13 row to the registry's GATES tab at the next publish). State `Gate Gx pending — [what is needed]` in the output whenever one is unresolved. G12 is not optional: a package that has not been executed has not been tested.

8. **Decision authority.** Builder decides alone: archetype recommendation, file layout, trigger wording, scaffold output, audit findings. **ALWAYS ASK ZAIM:** overriding a recommended archetype, remediating an existing skill (it is disruptive and belongs in its own job), changing a rule owned by another skill, retiring or merging a skill, anything that edits `mahareka-qs-agent` or its ratebase.

## Cross-skill consistency

One skill owns each shared rule; others reference the owner by name and never restate the value. Current owners are listed in `MAHAREKA_STANDARD.md`. When a rule changes, run `skill_check.py --all` — stale copies surface as CROSS blockers.

Known open conflict at v1.0: `bq-error-checker` maintains a second rate memory beside `QS_RATEBASE.xlsx` and carries the retired flat MROUND-5 rounding in three files. Logged, remediation not yet approved. **Do not fix it as a side effect of another task.** `bq-error-checker` v2.0 (the ICM pilot) moved these conflicts verbatim to `bq-error-checker/_shared/conflicts.md`; they are still open.

## What this skill will not do

- Write project instructions or account profiles — v1 covers skills only
- Generate a skill without a stated purpose and triggers — that produces a skill that never fires
- Ship a Type C package without a regression case — there would be no way to prove it still works
- Silently repair another skill

## Boundaries

Pricing and rate questions → `mahareka-qs-agent`. BQ document audits → `bq-error-checker`. Site reports → `site-lookahead-v2`. This skill builds and audits skills; it does not do their work.
