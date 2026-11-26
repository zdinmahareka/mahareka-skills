# mahareka-skill-builder: README

Version 2.1 · desk: MatDuo (Chief of Staff) · Hermes agents only · owner: Zaim

## Purpose
Build new Mahareka skills to one house standard, and audit the ones that exist, so every skill
has the right size, a clear trigger, and a shape that a cold agent can follow.

## What it does
- Classifies before building: Type A (one file), Type B (a file plus static references) or
  Type C (engines, memory and a bootstrap), and argues for the smaller type when the evidence
  says so.
- Picks the shape from the type: one file, shelves, or an ICM Pipeline (a router, a pipeline on
  one screen, one contract per stage, a run stamp, a gate per stage).
- Ships the ICM method: the standard (`references/icm-standard.md`, rules M1 to M11), the
  starters (`assets/icm/`) and the checker (`scripts/icm_check.py`).
- Audits a skill or the whole portfolio and reports BLOCKER, WARN and INFO.
- Keeps the registry of skills, audits, lessons and patterns append-only, in the KNOWLEDGE
  folder. The skill itself holds no data.
- It builds and audits skills. It does not do their work, and it never repairs another skill
  silently.

## Why it exists
Skills written one at a time drift: some are too big for their job, some never trigger, two of
them state the same rule differently. A single standard, a checker that can fail a skill, and a
registry that remembers what broke make the next skill better than the last one.

## When it runs
- When Zaim wants to create, design, plan, review, fix or version a skill ("buat skill baru",
  "audit my skills", "skill ni kenapa tak trigger").
- When deciding whether something should be a skill at all, or when two skills contradict each
  other.
- It is not scheduled.

## How it works
1. Bootstrap: confirm the live layer in the KNOWLEDGE folder before anything else.
2. Classify with the four questions, then pick the shape.
3. Gather name, purpose, triggers in English and Malay, limits and boundaries in one round.
4. Build from the starters, then audit: `scripts/icm_check.py <skill folder>` (or `--all`).
5. Verify by running, not by reading: restore the package into a clean folder and execute it.
6. Register append-only, then clear the ship gates G1 to G14 before handing over.

## Using it (Zaim)
Say what the skill is for and how you would ask for it. Answer the one round of questions.
You decide the things the builder may not: overriding a recommended type, remediating an
existing skill, changing a rule another skill owns, retiring or merging a skill, and anything
that touches `mahareka-qs-agent` or its ratebase. When the registry changes, replace it in the
KNOWLEDGE folder as the builder tells you.

## Maintaining it
- The standard: `references/icm-standard.md`. A rule change there needs Zaim's approval.
- Every Mahareka skill carries a `README.md` like this one (rule M11, gate G14, since 2.1);
  `icm_check.py` fails a skill without it.
- The engines in the KNOWLEDGE folder (`sb_boot.py`, `skill_scaffold.py`, `skill_check.py`)
  were written for Claude Projects. Porting them to Hermes is a separate change that is still
  open; until then, build from `assets/icm/` and check with `icm_check.py`.
- The source is the `mahareka-skills` repo. Tests: `tests/test_icm_check.py`,
  `tests/test_readme.py`. Keep `name:` and the description stable so a new version installs
  over the old one.
