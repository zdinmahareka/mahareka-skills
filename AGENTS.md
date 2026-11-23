# Mahareka Skills — entry

Mahareka's own Claude and Hermes skills, built to the Mahareka ICM Standard.
Private. Rates, registries and client data never live here: they stay in project knowledge.

## Where things live

| Path | Holds |
|---|---|
| `skills/<name>/` | one skill each, exactly as it installs (`SKILL.md` at its top) |
| `skills/mahareka-skill-builder/references/icm-standard.md` | the standard: shapes, rules M1–M10, walk test |
| `tests/` | regression and structure tests (synthetic data only) |
| `tools/package.py` | builds `dist/<name>.zip` for upload to Claude |

## Skills

| Skill | Version | Shape |
|---|---|---|
| `mahareka-skill-builder` | 2.0 | Shelves (Type B) |
| `bq-error-checker` | 2.0 | ICM Pipeline, 4 stages (ICM pilot) |

## Route by task

| Task | Go to |
|---|---|
| Build or audit a skill | `skills/mahareka-skill-builder/SKILL.md` |
| Reshape a skill to ICM | `skills/mahareka-skill-builder/references/icm-standard.md`, section 4 |
| Test everything | `python3 -m unittest discover -s tests` |
| Package for Claude | `python3 tools/package.py` |
