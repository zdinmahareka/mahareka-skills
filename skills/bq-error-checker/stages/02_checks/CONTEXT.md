# 02_checks — let the scripts find the evidence

One job: run the deterministic checks (Layers A–C) and rate intelligence (Layer F), and save
their raw output. No judgment here; that is stage 03.

## Inputs
- Working (this run): `RUN/01_intake/intake.md` (sheet, basis, subcon, project)
- Working (this run): the file named in `intake.md` (in `RUN/00_input/`, or
  `RUN/01_intake/reconstructed.xlsx` for a PDF)
- Reference (every run): `Rate_History.xlsx` in project knowledge (`/mnt/project/`) or uploads
- Reference (every run): `/mnt/project/qs_boot.py` (owned by `mahareka-qs-agent`)

Do NOT load: `_shared/` (stage 03 interprets), `QS_RATEBASE` contents, other runs.

## Process
1. Bootstrap the rate authority and save what it prints:
   `python3 /mnt/project/qs_boot.py > RUN/02_checks/boot.txt 2>&1`.
   If `qs_boot.py` is not there, write `DEGRADED: qs_boot.py missing` into `boot.txt`.
   DEGRADED → the gate fails; name the files to re-upload and stop. Never hand-calculate as
   a silent fallback.
2. Layers A–C: `python3 SKILL/_tools/check_bq.py <file> --sheet "<sheet>" --json RUN/02_checks/findings.json`
3. Layer F, if `Rate_History.xlsx` was found:
   `python3 SKILL/_tools/rate_learn.py --lines RUN/02_checks/findings.json --history <Rate_History.xlsx> --project <project> --subcon "<subcon>" --basis <basis> --out RUN/04_report/Rate_History_updated.xlsx --json RUN/02_checks/rates.json`.
   If it was not found, run nothing: the gate writes the "no memory" note, and stage 04
   reminds Zaim to attach it next time.

## Outputs
- `boot.txt`, `findings.json`, `rates.json` (when memory was found) → `RUN/02_checks/`
- `Rate_History_updated.xlsx` → `RUN/04_report/` (memory with new rows as `pending`)

## Check
`python3 SKILL/_tools/gate.py RUN 02` — passes when the rate authority is not DEGRADED,
`findings.json` parsed the sheet named in `intake.md`, and `rates.json` is valid (or memory
was absent). Every finding gets an id (`F01…`, `R01…`) for stage 03.
