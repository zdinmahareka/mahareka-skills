# Layer F — Rate Intelligence Protocol

## One ratebase (v2.1 — Zaim, 26 Nov 2026)
The benchmark is `QS_RATEBASE`, owned by `mahareka-qs-agent`, and nothing else. This skill keeps
no rate memory of its own: it reads rates through the owner's engines (`ratebase.py`,
`bif_prorata.py`, `bur_calc.py`, run with PY from KNOWLEDGE) and it never writes one. A rate it
learns in an audit is handed over in the report for `mahareka-qs-agent` to store.
Until v2.0 this skill kept a second rate workbook of its own; that is retired.

- Read the ratebase's standing rules before any margin/pro-rata math — they override skill defaults
- BASIS: `COST` (subcon) or `SELL` (client BQ) — never mix in comparisons
- STATUS in the ratebase: `verified` | `pending` | `flagged` | `superseded`; compare against `verified` only
- Rounding of a sell rate follows rule R-ALL-42 (owned by `mahareka-qs-agent`): read it there

## Matching
1. Normalize BQ description → candidate item (strip dims, room names, brands to grade/spec)
2. Match on item + UOM + BASIS; if grade differs, compare within-grade only
3. For BIF with non-standard dims: pro-rate the standard rate BEFORE comparing (else every custom dim false-flags)
4. No match = **ratebase gap** → list it for the handover, no flag

## Analysis rules
- **Band:** compare vs median of `verified` rates, same BASIS. Outside ±15% (tunable via user instruction) → flag, ALWAYS with history context: item, last n rates, dates, projects, % deviation
- **Systematic shift:** ≥60% of matched lines from one subcon deviate same direction within a similar % band → probable pricelist revision → advisory "request latest pricelist from [subcon]" and DOWNGRADE individual flags to one collective advisory. Suspect revision first; never open with accusation.
- **Single deviation:** one line off, siblings within band → probable error → hard flag with RM impact
- **Drift:** same item rising/falling across ≥3 chronological entries → trend advisory + suggest updating Rate Schedule / requesting refreshed pricelist
- **Fingerprint:** per-subcon reliability from how earlier flags were resolved. SMC/Eva Leong seeded as reliable. Reliable subcon + deviation → lean "genuine change". Unknown subcon → full cold check, no benefit of doubt.
- **Threshold reinforcement:** repeated `false alarm` for an item class → recommend widening that class's band; repeated `confirmed error` → tighten. State the recommendation; Zaim decides.

## Handover (stage 04) — hand over, never store
- Every checked rate the ratebase does not hold (or that changed): listed under "For the ratebase" with PROJECT/SUBCON/DATE, for `mahareka-qs-agent` to store as `pending`
- **Ask-when-unsure protocol:** anything unknown (cost basis, spec, vendor, scope) → ask Zaim in the consolidated question round; his answer goes to the ratebase through `mahareka-qs-agent`, same session
- Every flag Zaim resolves in-session: recorded in `review.md` and listed in the report (`confirmed error` / `false alarm` / `genuine change`)
- End of session: state counts: n rates compared, n ratebase gaps, n flags, n resolutions.
