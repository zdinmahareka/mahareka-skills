# Known Error Patterns (Lessons Learned — seeded from live audits)

Format: [Project / ref / party, date] — pattern — detection rule

1. **[N033 / SMC, May 2026] Decimal typo in client BQ.** Tall unit RM72/fr vs loaded cost 722/fr. → Sibling sanity check mandatory; rate ÷10 of family = red flag.
2. **[N033] Under-measured fr.** Console sold 5 fr; drawing = 2,700mm = 9 fr (4 × 652mm modules). → Always take off fr from drawing, cross-check vs door module count.
3. **[N033] Qty discrepancy BQ vs drawing.** Back panel 63 sf vs drawing 53 sf. → Back panel = W×H visible face, from drawing not memory.
4. **[N033] FALSE-FLAG RISK — pro-rata coincidence.** BU 168 & DWR 255 looked exactly like E0 column but were E1 pro-rated H860→H900. → ALWAYS test pro-rata at specified grade BEFORE flagging grade mismatch. False accusations = 0 tolerance.
5. **[N033] FIU pricing basis.** Fridge unit = wall-unit rate pro-rated for depth (D300→D580), not custom lump sum.
6. **[N033] Side-noted items.** Sink "2 door" RM200 = PVC foam-board sink-zone doors; dish rack in drawing remarks (RM105) — verify charged or free. → List every side-noted item in/out of total.
7. **[N033] Ventilation covers ≈ 1 per appliance zone (RM15/pc).** Sanity-check count vs appliance zones.
8. **[N033] Two-tone finish (Mieco SF-9005+SF-9007) = E1, no surcharge observed.**
9. **[N042 / SMC] Eva Leong arithmetic verified correct.** SMC/Eva = reliable subcon; deviations lean "pricelist changed" before "error".
10. **[General] Legacy-sheet contamination.** 31-sheet mega-template workbooks carry stale sheets from old projects (Darla, Yaseem, Belfield) → #REF! errors, old-client data. → Only audit the active sheet; warn if legacy sheets present.
11. **[General] Markup coefficient inconsistency.** 1.37 / 1.4 / 1.5 all found historically. Only BIF 1.5 confirmed. → Flag any other implied coefficient.

12. **[LEA/Tn Nizam, Jul 2026] Hidden rows = deactivated options.** Herringbone SPC options hidden + amount zeroed = correct workflow. Rule: skip hidden rows; hidden row with amount ≠ 0 = hard flag. Hidden helper columns (dual QTY) = use QTY nearest the RATE column.
13. **[LEA/Tn Nizam, Jul 2026] Own-supply items have different cost basis than SMC pricelist.** LED strip (material RM13/m), fluted panel (mat 8–13 + labour 5–8/sqft, min RM400), quartz 125/fr, sintered 220/fr — check RateBase BASIS/vendor before flagging vs SMC rates.
14. **[LEA/Tn Nizam, Jul 2026] 'Rate Only'/'not included' text in Amount column is acceptable** per Zaim — exclude from math, don't flag.

15. **[LEA/Tn Nizam, Jul 2026] Blockboard Melamine Finish = SMC equivalent loaded rate ×1.30** (pro-rata first, then +30%). Previous 1.03×/1.06× flags = false alarm from applying aluminium-vendor costs to blockboard lines. Match material spec to correct cost basis BEFORE margin math.
16. **[Standing] Ask-when-unsure protocol:** unknown cost basis/spec/vendor → ask Zaim, save answer to Rate_History same session. Memory updates NEVER require skill re-packaging; only rule changes do.

17. **[Rule confirmed Jul 2026] SMC melamine doors do NOT pro-rate** — table rate flat regardless of height (SMC basis = body + melamine door bundled). Non-melamine doors = per sqft, separate line. Earlier N033 door-pro-rata reconstruction was coincidental fit, superseded.
18. **[Rule confirmed Jul 2026] Concrete Table section** = site already has concrete structure → doors/drawers/shelf/partition only, no carcass.

*(Append new lessons here at each skill re-package. Interim lessons live in Rate_History NOTES.)*
