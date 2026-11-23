# Layer F — Rate Intelligence Protocol (RateBase)

## Memory file: Rate_History.xlsx (6 sheets)
`README` (usage) | `RATES` (curated master) | `INBOX` (skill append target) | `RULES` (standing pricing rules) | `VENDORS` (subcon track record) | `RESOLUTIONS` (learning log)

### RATES / INBOX
Columns: `ELEMENT | ITEM | SPEC/GRADE | UOM | COST RATE | MARKUP | SELL RATE | VENDOR | SOURCE/PROJECT | DATE | STATUS | NOTES`
- COST and SELL side by side (no BASIS flag); SELL formula = ROUND(COST×MARKUP/5)×5 — preserve formulas when appending
- **Skill APPENDS ONLY to INBOX**, never directly to RATES. Zaim promotes INBOX→RATES manually after review
- Read RULES sheet before any margin/pro-rata math — rules there override skill defaults
- Read VENDORS for reliability fingerprint before interpreting deviations
- ELEMENT dropdown = Zaim's primary organisation axis; mandatory trio = RATE, UOM, SPEC
- New standing rules learned from Zaim → append to RULES sheet (numbered), not RATES
- ITEM_KEY: normalized key (lowercase, trade prefix, no dims) e.g. `bif.base_unit`, `el.point_13a`, `fl.tile_600`
- BASIS: `COST` (subcon) or `SELL` (client BQ) — never mix in comparisons
- STATUS: `verified` | `pending` | `flagged` | `superseded`
Sheet `RESOLUTIONS`: `DATE | PROJECT | FLAG | OUTCOME (confirmed error / false alarm / genuine change) | LESSON`

## Matching
1. Normalize BQ description → candidate ITEM_KEY (strip dims, room names, brands to GRADE_SPEC)
2. Match on ITEM_KEY + UOM + BASIS; if grade differs, compare within-grade only
3. For BIF with non-standard dims: pro-rate the historical standard rate BEFORE comparing (else every custom dim false-flags)
4. No match = new item → append as `pending`, no flag

## Analysis rules
- **Band:** compare vs median of `verified` rates, same BASIS. Outside ±15% (tunable via user instruction) → flag, ALWAYS with history context: item, last n rates, dates, projects, % deviation
- **Systematic shift:** ≥60% of matched lines from one subcon deviate same direction within a similar % band → probable pricelist revision → advisory "request latest pricelist from [subcon]" and DOWNGRADE individual flags to one collective advisory. Suspect revision first; never open with accusation.
- **Single deviation:** one line off, siblings within band → probable error → hard flag with RM impact
- **Drift:** same ITEM_KEY rising/falling across ≥3 chronological entries → trend advisory + suggest updating Rate Schedule / requesting refreshed pricelist
- **Fingerprint:** per-subcon reliability from RESOLUTIONS history. SMC/Eva Leong seeded as reliable. Reliable subcon + deviation → lean "genuine change". Unknown subcon → full cold check, no benefit of doubt.
- **Threshold reinforcement:** if RESOLUTIONS shows repeated `false alarm` for an item class, recommend widening that class's band; repeated `confirmed error` → tighten. State the recommendation; Zaim decides.

## Append & handover
- Every checked rate not in memory (or changed): append as `pending` with PROJECT/SUBCON/DATE
- **Ask-when-unsure protocol:** anything unknown (cost basis, spec, vendor, scope) → ask Zaim in the consolidated question round; save his answer into RATES (as rate or RULE row) + RESOLUTIONS same session
- Every flag Zaim resolves in-session: log to RESOLUTIONS immediately
- End of session: output updated Rate_History.xlsx + remind Zaim to save to project files. State counts: n verified matches, n new pending, n flags, n resolutions logged.
