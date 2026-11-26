# Error taxonomy — Layers A to G

What counts as a finding, by layer. Scripts do A–C (`_tools/check_bq.py`); F is judgment against the one ratebase since v2.1; stage 03 applies the judgment in B, D, E and G. Unchanged from v1.1.

### Layer A — Arithmetic (script)
- Qty × Rate = Amount per line (tolerance RM1)
- Section subtotals = Σ lines; grand total = Σ subtotals
- #REF!/#VALUE!/#DIV0 errors; text in numeric columns
  — *see Known conflicts: the "not included" annotation rule contradicts
  `conventions.md` and lesson 14, and is awaiting Zaim's ruling*

### Layer B — Rate anomaly (script + judgment)
- **Sibling sanity:** rate wildly out of family among comparable items = probable decimal
  typo (proven: RM72/fr among RM290–690 siblings, N033)
- ×10 / ÷10 decimal patterns; zero/blank rate with non-zero amount and vice versa;
  duplicate lines
- **Room-to-room consistency:** the same description carrying two different rates in two
  sections, with no stated reason, is a flag in its own right — it is the defect a client
  finds fastest

### Layer C — Structure & conventions (script)
- Numbering sequential, no skips/repeats
- UOM from the standard list in `conventions.md` (never "ITEM")
- Qty=0 ghost rows
- Non-SMC-scope lines (quartz, backsplash, solid surface): qty filled, Rate & Amount BLANK
- **Missing RATE column, or a priced line with no rate, is a hard error** — it creates
  remeasurement and variation-order risk
- **Absent Preliminaries** in a substantial BQ is a commercial risk, not a formatting note

### Layer D — Margin (only when cost data available)
- Implied markup per line vs the 1.5× rule (markup on cost, never margin). Any line below
  1.5× → flag for Zaim's decision, NEVER approve silently
- The 1.5× rule is **cabinet/joinery only**. Install-only, structural, and every other
  trade → ASK ZAIM, never assume
- A line selling **at or below verified cost** is the highest-priority finding class in the
  taxonomy — rank it above any overpricing

### Layer E — Cross-reference (only when drawing / subcon quote also provided)
- 3-way qty: BQ vs subcon quote vs drawing (back panel = W×H visible face; cabinet fr =
  run ÷ 304.8mm cross-checked vs ~652mm door modules)
- **PRO-RATA FIRST (critical):** when a subcon rate doesn't match the expected grade
  column, TEST pro-rata at the specified grade before flagging grade mismatch or
  overcharge. `rate × (H_act ÷ H_std) × (D_act ÷ D_std)`; carcass by H and D, doors by H
  only. Coincidental column matches happen. **False accusations against a subcon = 0
  tolerance.**

### Layer F — Rate Intelligence / Learning (script + judgment)
Read `learning.md` for the full protocol. Summary:
- Match BQ lines to `QS_RATEBASE` (through `mahareka-qs-agent`'s engines) via normalized description + UOM + grade
- **Band check:** outside historical band (default ±15%, tunable) → flag with history
  context
- **Systematic shift vs single deviation:** many items shifted ~same % = probable pricelist
  revision → "request latest pricelist" (suspect revision FIRST, never accuse first). One
  item off with normal siblings = probable error → hard flag
- **Drift:** consistent direction across projects/time = trend advisory
- **Subcon fingerprint:** known-reliable vendors (SMC/Eva Leong: verified accurate) lean
  "price changed"; unknown vendors get cold full checks
- **Hand over, never store:** new/changed rates are listed in the report for
  `mahareka-qs-agent` to store as `pending` until Zaim verifies; flag resolutions are listed
  there too (`confirmed error` / `false alarm` / `genuine change`)

### Layer G — Commercial review (judgment, Mode 2 only)
Governed by `reporting.md`. Covers cost-driver concentration and Pareto
analysis, scope gaps and VO exposure, quantity plausibility against design intent, Value
Engineering, budget-target construction, and multi-BQ comparison decomposed into rate /
quantity / specification / scope effects.

Layer G interprets; it never sets a rate. Every figure it uses comes from Layers D–F or
from `QS_RATEBASE`.

