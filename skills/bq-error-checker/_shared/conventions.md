# Mahareka BQ Conventions (validation reference)

## Column standard
`ITEM | DESCRIPTION | QTY | UNIT | RATE | AMOUNT` — navy section headers, alternating shading, yellow rate cells, orange subtotals, navy grand total, freeze row 3, landscape.

## Valid UOM list (ONLY these)
`m` `mr` `sqft` `sqm` `fr` `nos` `set` `unit` `pair` `ls` `lot` `point` `trip` `month` `visit` `%` `p/pc` `p/set` `p/fr` `p/sf`
- Areas = sqft; linear = mr; cabinet runs = fr; lump sum = ls. NEVER "ITEM" as UOM.

## Annotation rules
- `Rate Only` / `NOT INCLUDED` / `not included` text — ACCEPTABLE anywhere including Amount column (Zaim convention). Exclude from arithmetic, never flag.
- `free` → only valid together with RM0 rate
- **HIDDEN ROWS/COLUMNS = deactivated options.** Never read hidden rows into totals or checks. Hidden row with non-zero Amount = ERROR (inflates total) — flag hard. Hidden helper columns (e.g. duplicate QTY, GROUP, CODE) must be ignored; use the QTY column adjacent to UNIT/RATE/AMOUNT.

## Numbering
Sections integer (1, 2, 3…), sub-sections X.Y, items a) b) c) sequential — no skips, no repeats. `TOTAL AMOUNT` row per section, formula-linked.

## Standard section order (library order)
PR Preliminaries → DM Demolition → ST Structure → WP Wall & Partition → CL Ceiling → FL Floor → WF Wall Finishes → DW Door/Window/Glass → EL Electrical → EV ELV/ICT → AC ACMV → PL Plumbing → SP Sanitary → FP Fire Protection → WT Waterproofing → CP Carpentry/BIF → LF Loose Furniture → KE Kitchen Specialist → MT Metal → FC Façade → SG Signage → TC T&C/Handover → PS Prov/PC Sums. (Grouping by PHASE or AREA is allowed as a wrapper.)

## Pricing rules
- Cabinet/joinery (BIF): client sees ONE loaded composite rate per fr = carcass + door + 45° handle + end panel apportioned + surcharges. Sell = loaded cost × 1.5 (markup on cost), rounded nearest RM5. Never show accessory breakdown to client.
- Install-only items: markup is ZAIM'S DECISION every time — never assume.
- Non-SMC-scope in BIF section (quartz/backsplash/solid surface): qty filled, Rate & Amount BLANK.
- Known historical markup coefficients in the wild: 1.37, 1.4, 1.5 — only 1.5 is the confirmed BIF standard; if another coefficient appears, flag for unification, don't silently accept.

## Electrical structural rule
Wiring point items separate from supply-&-install fitting items; install-only lines marked `(INSTALL ONLY, FITTINGS NOT INCLUDED)`.

## Dimension & module conventions (BIF)
- Decimal feet notation: 12'5" = 12.5 fr; fr take-off = run(mm) ÷ 304.8
- Standard door module ≈ 652mm; cross-check fr vs module count
- Pro-rata: `rate × (H_act ÷ H_std) × (D_act ÷ D_std)` — carcass by H and D; doors by H only; end panels by height; FIU from wall-unit rate pro-rated for depth
- Min charges: TTU 450mm; sliding wardrobe 4'/set; doors 1 sqft; cut-to-size glass 2 sqft/pc (W&H round up 150mm)

## Grade mapping (SMC)
- E1 = Lendecor, Mieco ("White Chipboard" carcass col / "Mel/ABS" door col)
- E0 = Maxworld, Topmix
- E2 Ply/SE0 = Topply, Panel Plus
- Melamine quoted on E1 basis. Special colours: +RM2/sqft metallic, +RM4/sqft acrylic orig & matt; PVC foamboard colour +4 (1S) / +6 (2S) per sqft.
