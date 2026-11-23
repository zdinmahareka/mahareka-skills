# mahareka-skills

Mahareka's own skills **for the Hermes agents** (MatDuo, Mattigo), built to the **Mahareka ICM
Standard** (Interpretable Context Methodology: the folder structure is the agent's
architecture). Not for Claude uploads. See `AGENTS.md`.

## Install on a Hermes machine

```bash
bash tools/install-hermes.sh ~/.hermes/profiles/matduo/skills
```

It runs the tests, moves each old copy to `~/mc-backups/skills/`, installs the new one in the
same place, and prints where KNOWLEDGE and RUNS are. Mission Control records the change as a
new skill revision.

## Per-machine folders

| Name | Default | Holds |
|---|---|---|
| KNOWLEDGE | `$MAHAREKA_KNOWLEDGE`, else `~/mahareka-knowledge`, else found by searching home | `qs_boot.py`, QS_RATEBASE, `Rate_History.xlsx`, registry (already on the machine; never copied) |
| RUNS | `~/mahareka-runs` (`$MAHAREKA_RUNS`) | one folder per audit run |

## Test

```bash
python3 -m unittest discover -s tests
```
