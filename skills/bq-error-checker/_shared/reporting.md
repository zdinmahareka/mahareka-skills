# Commercial Audit Reporting Standard

Source: `BQ_Audit_Report_Presentation_Standard.md`, installed by Zaim 03 Sep 2026.
Folded into this skill at v1.1. This file governs **Report Mode 2 (Commercial Audit)** only.

This file does not carry rates. It carries **how findings are analysed and presented**.
The rate benchmark comes from `QS_RATEBASE` via `mahareka-qs-agent` and from `Rate_History.xlsx`
via Layer F. Never take a number from this file.

```
Rate & Cost Memory   → tells you WHAT the benchmark is
This file            → tells you HOW to interpret and present it
```

---

## Core reporting principle

Do not summarise the BQ. Present like a QS briefing the Commercial Director.

For every important issue, answer all six:

1. What is the issue?
2. What is the current figure?
3. What is the benchmark?
4. How big is the difference?
5. Why does it matter?
6. What should Zaim do?

The report must let Zaim answer one question: **"What actually needs my attention?"**

Never say an amount is expensive because the total is high.

---

## The six concepts — never confuse them

| Concept | Meaning |
|---|---|
| **RATE** | How much per unit |
| **QUANTITY** | How much work is measured |
| **SPECIFICATION** | What quality / material / design is provided |
| **SCOPE** | What work is actually included |
| **AMOUNT** | Quantity × Rate |
| **ARITHMETIC** | Whether the calculation itself is correct |

Worked example of correct interpretation:

> 20 single eyeballs → 20 twin eyeballs is **not** a rate increase.
> The electrical point quantity stays at 20 and the wiring rate is unchanged.
> The specification changed, producing ~40 light heads instead of 20.
> The additional cost is therefore a **fitting/specification** cost, not a point-quantity cost.

Always identify which of the four factors is driving a movement: rate, quantity,
specification, or additional scope.

---

## Report structure — Mode 2

Use only the sections that carry a genuine finding. If a section is clean, say so in one
line. Never manufacture findings to fill a heading.

```
# BQ PRICING AUDIT — [project]
Project:  |  BQ Total: RM  |  Overall Assessment: 🟢 / 🟠 / 🔴

## Executive Summary          (3–6 bullets, findings first, never an item list)
1.  🚨 Priority Findings
2.  Overpriced / High Rate Items
3.  Underpriced / Margin-Risk Items
4.  📏 Quantity Anomalies
5.  🧮 Arithmetic Check
6.  📊 Rate Analysis
7.  💰 Major Cost Drivers
8.  ⚠️ Rates Requiring Zaim's Input
9.  ⚠️ Commercial Risks
10. 💡 Value Engineering Opportunities
11. Final Recommendation + Commercial Conclusion
```

### 1. Priority Findings

| Priority | Item | Finding | Financial Impact | Recommended Action |
|---|---|---|---:|---|

- 🔴 **HIGH** — check before issuing the quotation
- 🟠 **MEDIUM** — review / monitor
- 🟢 **LOW** — acceptable, worth noting

After the table, explain the 2–3 most important findings in prose.

### 2. Overpriced / High Rate Items

| Item | Current Rate | Benchmark | Difference | Movement | Assessment |
|---|---:|---:|---:|---:|---|

Classifications: 🔴 Significantly High · 🟠 Slightly High · 🟢 Reasonable ·
🔵 Low / Potentially Underpriced · ⚠️ Unable to Assess

**Always show the mathematics**, then interpret:

```
RM135 − RM120 = RM15
RM15 ÷ RM120 = 12.5%
→ "Noticeable but not necessarily excessive."
```

Do not call every increase overpriced.

### 3. Underpriced / Margin-Risk Items

| Item | Current Rate | Benchmark | Difference | Risk |
|---|---:|---:|---:|---|

State whether the low rate causes: low margin · loss-making work · insufficient labour
allowance · missing material or accessory · subcontractor exposure · future VO ·
incorrect specification assumption.

If nothing is underpriced, write "No clear underpriced items identified." and move on.

### 4. Quantity Anomalies

Only quantities that look unusual. Wording is **"Looks unusual — verify against
drawing / site measurement"**, never "wrong", unless it can be proven.

Typical triggers: same-sized room with materially different quantity · window sqft
inconsistent with a comparable unit · point count out of line with the RCP · suspicious
cabinet run length · duplicate quantities · quantity carrying RM0 · item measured LS when
a measurable quantity exists · fitting count not matching wiring point count.

### 5. Arithmetic Check

Verify: `Qty × Rate = Amount` · `Section Total = Σ items` · `Grand Total = Σ sections`.
Present only errors and material checks. Status: ✅ Correct · ⚠️ Rounding · ❌ Error.

Close with one line: **"Arithmetic Status: ✅ No arithmetic error detected"** or
**"❌ n discrepancies detected"** with the impact on the grand total calculated.

### 6. Rate Analysis

Never dump every rate unless a full rate schedule is asked for. Show meaningful movements
only, then interpret. The interpretation is the point:

> "The ceiling rate has not increased. The higher ceiling amount is caused by quantity,
> not rate."

### 7. Major Cost Drivers

`Contribution % = Item or Section Amount ÷ BQ Total × 100`

| Rank | Section / Item | Amount | % of Total |
|---:|---|---:|---:|

Interpretation bands: **>20% Critical** · **15–20% Major** · **10–15% Significant** ·
**<10% Secondary** unless it is an easy VE.

Use Pareto thinking — identify the small number of items carrying most of the value.
Where the BQ supports it, present three levels: by trade, by sub-trade, and by room ×
trade. State the cumulative % so the 80% cut-off is visible.

### 8. Rates Requiring Zaim's Input

Do **not** invent a benchmark and do **not** pretend confidence.

| Item | Current Rate | Why Confirmation Is Needed | What I Need |
|---|---:|---|---|

Ask only for information that materially changes the assessment: supplier rate ·
subcon rate · brand · thickness · construction detail · drawing · specification · cost
price · unit height/depth. No unnecessary questions.

Every genuinely absent rate is also a **ratebase gap** — say so, and offer to stage it.

### 9. Commercial Risks

Present separately from rate issues: RM0 or free items · missing rate · missing quantity ·
ambiguous specification · large LS allowance · duplicate scope · missing scope ·
VO exposure · item priced differently between rooms without a stated reason ·
absent Preliminaries · scope silently omitted rather than excluded in writing.

### 10. Value Engineering

| VE Item | Current Scope | Proposed VE | Estimated Saving | Design Impact |
|---|---|---|---:|---|

Impact: 🟢 LOW · 🟠 MEDIUM · 🔴 HIGH

**VE priority order — follow it:**
1. Defer items that can easily be installed later
2. Simplify decorative specification
3. Reduce unnecessary quantity
4. Simplify design
5. Substitute material
6. Reduce rate — last resort only

**Protect:** safety · structural work · waterproofing · essential electrical ·
essential plumbing · technical compliance · workmanship quality.

### 11. Final Recommendation

Classify every finding, then close with a short commercial conclusion in Zaim's voice —
what you would do if you were reviewing this before it went to the client.

- ✅ **KEEP** — reasonable items
- ⚠️ **CHECK** — needs verification
- 🔴 **REPRICE** — genuinely too high or too low
- 📏 **REMEASURE** — abnormal quantities
- 💡 **VE** — best savings opportunities

---

## Budget-target requests

"Make an RM90k option" / "reduce this to RM80k" is **never a percentage discount**.

Start from the current BQ, identify actual items to change / simplify / reduce / defer /
exclude, and calculate item by item:

```
Original BQ
 + repricing corrections (fix loss-making lines FIRST)
 − VE item 1
 − VE item 2
 …
 = Revised estimated BQ
```

Reprice before you cut. Cutting a BQ that still contains below-cost lines just locks the
loss in. Then state plainly what the client retains and what has been sacrificed.

---

## Comparing two or more BQs

Compare: total · scope · quantities · rates · specifications · added items · removed
items · rate movement · quantity movement · cost drivers.

Never stop at "Quotation B is RM10,000 higher." Split the difference into:

| Effect | Example |
|---|---|
| **Rate** | RM120/pt → RM135/pt = +RM15 = +12.5% |
| **Quantity** | 20 pts → 30 pts = +10 pts = +50% |
| **Specification** | Single eyeball → twin eyeball |
| **Scope** | 2 airconds → 3 airconds |

Quantify each effect where the data allows. Preferred conclusion shape:

> "The total moved from RM89,713 to RM98,451, but the measured area is almost identical.
> Core rates are stable; the difference is additional scope, different specifications and
> several high-value built-in items."

---

## Depth

**Default = Management Level.** Exceptions, risks, cost concentration and opportunities.
Do not list hundreds of correct items.

Escalate to item-by-item only on: "full audit" · "deep audit" · "audit everything" ·
"audit all rates" · "detailed QS audit".

---

## Style

Use: clean tables · RM figures · unit rates · percentages · explicit calculations ·
short interpretation under each table · **bold conclusions** · 🟢 🟠 🔴 ⚠️ only where
they help scanning.

Avoid: long essays · generic QS theory · repeating the BQ · listing normal items ·
making everything sound like a problem · saying "overpriced" without explaining why ·
mixing a quantity increase with a rate increase.

**Explanation standard.** Not "Rate increased" but:

> "Light-point wiring moved from RM120/point to RM135/point, +RM15 or +12.5%. Noticeable
> but not excessive against the available Mahareka benchmark."

Not "Living lighting is expensive" but:

> "The design uses 20 twin eyeballs rather than 20 singles. Point quantity is unchanged at
> 20, but the specification produces roughly 40 light heads, so the additional cost is
> specification, not point quantity."
