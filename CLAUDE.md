@AGENTS.md

# Working rules
- Merging: Claude merges its own PRs once tests pass, without asking (Zaim, 23 Nov 2026 — same rule as Mission Control). Skills are for the Hermes agents only (not Claude uploads). Merged changes reach both machines by themselves: Mission Control's auto-update pulls this repo and runs `tools/install-hermes.sh` (Zaim, 23 Nov 2026), so `main` must always install cleanly. The installer never replaces a skill that was edited on the machine and never installs into a folder the machine has not recorded (`AGENTS.md`, Install rules).
- Tests: `python3 -m unittest discover -s tests` and `python3 skills/mahareka-skill-builder/scripts/icm_check.py --all skills`.
- Never commit rates, ratebase/registry workbooks, client BQs, names, tokens or secrets. Test data is synthetic.
- A reshape moves text verbatim; rule changes are separate and need Zaim's OK. Declared conflicts stay declared.
- Keep `name:` and trigger descriptions stable so a new version installs over the old one.
- Only a skill's entry is named `SKILL.md` (Hermes and Mission Control count every `SKILL.md`).
