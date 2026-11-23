# NN_<verb> — <the stage's one job, as a phrase>

One job: <one sentence>.

## Inputs
- Working (this run): `RUN/<previous stage>/<file>`
- Reference (every run): `SKILL/_shared/<rules>.md`

Do NOT load: <the shelves and earlier outputs this stage must not see>, other runs.

## Process
1. If an input is missing or empty, stop and say which.
2. <step; a step that is code names its command>
3. <step>

## Outputs
- `<file>` → `RUN/NN_<verb>/`

## Check
<Exactly one: "Zaim reads …" or "`PY SKILL/_tools/gate.py RUN NN` — passes when …".>
