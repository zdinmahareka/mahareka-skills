@AGENTS.md

# Working rules
- Merging: Claude merges its own PRs once tests pass, without asking (Zaim, 23 Nov 2026 — same rule as Mission Control). Skills reach Claude and the agents only when Zaim uploads them or sends the agents their message.
- Tests: `python3 -m unittest discover -s tests` and `python3 skills/mahareka-skill-builder/scripts/icm_check.py --all skills`.
- Never commit rates, ratebase/registry workbooks, client BQs, names, tokens or secrets. Test data is synthetic.
- A reshape moves text verbatim; rule changes are separate and need Zaim's OK. Declared conflicts stay declared.
- Keep `name:` and trigger descriptions stable so a new version installs over the old one.
- Only a skill's entry is named `SKILL.md` (Hermes and Mission Control count every `SKILL.md`).
