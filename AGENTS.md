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
| `tools/install-hermes.sh` | installs skills into this machine's recorded Hermes skills folder; keeps a copy that was edited on the machine |
| `tools/skill_state.py` | tells whether an installed skill is unedited (recorded at install, or a version in this repo's history) |
| `tools/patch_qs_agent.py` | the approved changes to the installed QS agent (windows, rule R-MASTER) |

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
| Install on a Hermes machine | first time: `MAHAREKA_SET_DIR=1 bash tools/install-hermes.sh <skills dir>`; after that auto-update runs it |

## Install rules

- **One folder per machine.** The first install records it in `~/.mahareka/skills-dir`; any other folder is refused. A machine with no recorded folder installs nothing (the laptop loads MatDuo's copy through Hermes's `skills.external_dirs`).
- **Local edits are kept.** Hermes edits skills itself (curator, `skill_manage`). A copy that is not exactly a version this repo produced is left alone; the run ends with exit 3 and `KEPT (local_change): <name>`. Zaim decides: merge the edits into the repo, or `MAHAREKA_REPLACE="<name>"` (the old copy still goes to `~/mc-backups/skills/`).
- **`_local/` belongs to the machine.** It is never compared and is carried over on every replace.
