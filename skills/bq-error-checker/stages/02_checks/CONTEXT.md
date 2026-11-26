# 02_checks — let the scripts find the evidence

One job: bootstrap the rate authority, run the deterministic checks (Layers A–C), and save
their raw output. No judgment here; that is stage 03 (rate intelligence, Layer F, included).

## Inputs
- Working (this run): `RUN/01_intake/intake.md` (sheet, basis, subcon, project)
- Working (this run): the file named in `intake.md` (in `RUN/00_input/`, or
  `RUN/01_intake/reconstructed.xlsx` for a PDF)
- Reference (every run): `KNOWLEDGE/qs_boot.py` (owned by `mahareka-qs-agent`)
  — run `python SKILL/_tools/where.py` first: it prints PY, KNOWLEDGE and the file. It
  already sits on the machine; where.py finds it (env, `~/mahareka-knowledge`, else the
  installed `mahareka-qs-agent` skill). It never searches home, so an archive or download copy
  is never used. Never copy or move it.

Do NOT load: `_shared/` (stage 03 interprets), `QS_RATEBASE` contents, other runs.

## Process
1. Bootstrap the rate authority and save what it prints:
   `(cd KNOWLEDGE && PY qs_boot.py) > RUN/02_checks/boot.txt 2>&1`.
   If `qs_boot.py` is not there, write `DEGRADED: qs_boot.py missing` into `boot.txt`.
   DEGRADED → the gate fails; name the files to re-upload and stop. INTACT but FLAGGED →
   raise the flags before trusting any number (stage 03 lists them as `ASK`). Never
   hand-calculate as a silent fallback; use `ratebase.py`, `bif_prorata.py`, `bur_calc.py`.
2. Layers A–C: `PY SKILL/_tools/check_bq.py <file> --sheet "<sheet>" --json RUN/02_checks/findings.json`
3. No rate comparison here. Since v2.1 this skill keeps no rate memory of its own (one
   ratebase: Zaim, 26 Nov 2026). Rates are compared in stage 03, against `QS_RATEBASE`
   through the engines above.

## Outputs
- `boot.txt`, `findings.json` → `RUN/02_checks/`

## Check
`PY SKILL/_tools/gate.py RUN 02` — passes when the rate authority is not DEGRADED,
and `findings.json` parsed the sheet named in `intake.md`. Every finding gets an id (`F01…`)
for stage 03.
