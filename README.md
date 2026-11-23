# mahareka-skills

Mahareka's own skills, built to the **Mahareka ICM Standard** (Interpretable Context
Methodology: the folder structure is the agent's architecture). See `AGENTS.md`.

## Install in Claude

```bash
python3 tools/package.py
```

Upload each `dist/<name>.zip` in Claude: Settings → Capabilities → Skills. A skill with the
same name is replaced.

## Install in Hermes

Copy `skills/<name>/` over the agent's copy (for example
`~/.hermes/profiles/<profile>/skills/construction/<name>/`). Mission Control records the change
as a new revision, so it can be rolled back there.

## Test

```bash
python3 -m unittest discover -s tests
```
