# mahareka-skill-builder: README

Version 2.4 · desk: MatDuo (Chief of Staff) · Hermes agents only · owner: Zaim

## Purpose
Build new Mahareka skills to one house standard, and audit the ones that exist, so every skill
has the right size, a clear trigger, and a shape that a cold agent can follow.

## What it does
- Classifies before building: Type A (one file), Type B (a file plus static references) or
  Type C (engines, memory and a bootstrap), and argues for the smaller type when the evidence
  says so.
- Picks the shape from the type: one file, shelves, or an ICM Pipeline (a router, a pipeline on
  one screen, one contract per stage, a run stamp, a gate per stage).
- Ships the ICM method: the standard (`references/icm-standard.md`, rules M1 to M11) and the
  starters for all three shapes (`assets/`).
- Starts a new skill in the right shape with one command (`scripts/new_skill.py`).
- Audits a skill or the whole portfolio and reports BLOCKER, WARN and INFO
  (`scripts/skill_check.py` for the 11 principles, `scripts/icm_check.py` for structure).
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
1. Bootstrap: `scripts/sb_boot.py` confirms the tools and the live layer in the KNOWLEDGE
   folder before anything else. If something is missing it says what, and the work stops.
2. Classify with the four questions, then pick the shape.
3. Gather name, purpose, triggers in English and Malay, limits and boundaries in one round.
4. Build: `scripts/new_skill.py` writes the folder from the starters and runs the checker.
5. Audit: `scripts/skill_check.py` and `scripts/icm_check.py` (one skill, or `--all`).
6. Verify by running, not by reading: copy the skill into a clean folder and execute it.
7. Register append-only (`scripts/registry.py`), then clear the ship gates G1 to G14.

## Using it (Zaim)
Say what the skill is for and how you would ask for it. Answer the one round of questions.
You decide the things the builder may not: overriding a recommended type, remediating an
existing skill, changing a rule another skill owns, retiring or merging a skill, and anything
that touches `mahareka-qs-agent` or its ratebase. The tools never write the registry: they
put `SKILL_REGISTRY.staged.xlsx` beside it and tell you. Replace `SKILL_REGISTRY.xlsx` with
that file in the KNOWLEDGE folder when you accept it.

## Maintaining it
- The standard: `references/icm-standard.md`. A rule change there needs Zaim's approval.
- Every Mahareka skill carries a `README.md` like this one (rule M11, gate G14, since 2.1);
  `icm_check.py` fails a skill without it.
- Since 2.2 the engines live in `scripts/` and run on Hermes. Only two files stay in the
  KNOWLEDGE folder: `MAHAREKA_STANDARD.md` and `SKILL_REGISTRY.xlsx`. The old copies there
  (`sb_boot.py`, `skill_check.py`, `skill_scaffold.py`, written for Claude Projects) are no
  longer used.
- Two lessons that Hermes wrote into MatDuo's copy were merged into the skill in 2.3: do not
  convert a working skill to ICM for the shape alone, and triage `skill_check.py` findings
  (some of its blockers are noise on Hermes) before reporting them.
- `skill_check.py` names the owner of a shared rule and never restates its value. Its 11
  principles were moved over unchanged; only the paths and the wording for Hermes changed.
- The source is the `mahareka-skills` repo. Tests: `tests/test_icm_check.py`,
  `tests/test_readme.py`, `tests/test_skill_builder.py`. Keep `name:` and the description stable so a new version installs
  over the old one.
