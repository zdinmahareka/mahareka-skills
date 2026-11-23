# Mahareka Skills — entry

Mahareka's own skills for the Hermes agents only, built to the Mahareka ICM Standard.
Private. Rates, registries and client data never live here: they stay in each machine's
KNOWLEDGE folder (`$MAHAREKA_KNOWLEDGE`, default `~/mahareka-knowledge`).

## Where things live

| Path | Holds |
|---|---|
| `skills/<name>/` | one skill each, exactly as it installs (`SKILL.md` at its top) |
| `skills/mahareka-skill-builder/references/icm-standard.md` | the standard: shapes, rules M1–M10, walk test |
| `tests/` | regression and structure tests (synthetic data only) |
| `tools/install-hermes.sh` | installs skills into a Hermes profile (backs up the old copy) |

## Skills

| Skill | Version | Shape |
|---|---|---|
| `mahareka-skill-builder` | 2.0 | Shelves (Type B) |
| `bq-error-checker` | 2.0 | ICM Pipeline, 4 stages (ICM pilot) |
| `chief-of-staff` | 1.0 | Shelves (Type B): routes work to the Virtual Office staff |

## Route by task

| Task | Go to |
|---|---|
| Build or audit a skill | `skills/mahareka-skill-builder/SKILL.md` |
| Reshape a skill to ICM | `skills/mahareka-skill-builder/references/icm-standard.md`, section 4 |
| Test everything | `python3 -m unittest discover -s tests` |
| Install on a Hermes machine | `bash tools/install-hermes.sh <skills dir>` |
