# Known conflicts — declared, not silently resolved

These are logged. Do not fix any of them as a side effect of another task.

1. **Second rate memory.** RESOLVED in v2.1 (Zaim, 26 Nov 2026: one ratebase). Until v2.0
   this skill kept its own rate workbook beside `QS_RATEBASE` owned by `mahareka-qs-agent`.
   The workbook, its script and every instruction to read or append it are removed; rates a
   BQ teaches are handed to `mahareka-qs-agent` in the report. Logged by
   `mahareka-skill-builder` at v1.0.
2. **Rounding rule.** RESOLVED in v2.1 (Zaim, 26 Nov 2026). The flat rounding this skill
   carried is retired. Rounding is rule R-ALL-42, owned by `mahareka-qs-agent`: read the value
   there; it is not restated here.
3. **"not included" annotation.** Layer A treats text in the AMOUNT column as a violation.
   `conventions.md` and lesson 14 say the annotation is acceptable per Zaim convention and
   must never be flagged. Unresolved. Interim handling: do not flag the annotation itself,
   but **do** flag a line that carries a quantity and sits inside the priced schedule while
   showing no rate — that is a scope-claim risk regardless of the annotation rule.
4. **Authority.** Where this skill and `mahareka-qs-agent` disagree on a rate, the QS agent
   and `QS_RATEBASE` win. This skill audits documents; it does not own rates.
