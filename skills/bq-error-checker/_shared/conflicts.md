# Known conflicts — declared, not silently resolved

These are logged. Do not fix any of them as a side effect of another task.

1. **Second rate memory.** This skill maintains `Rate_History.xlsx` alongside
   `QS_RATEBASE.xlsx` owned by `mahareka-qs-agent`. Two memories for one domain. Logged by
   `mahareka-skill-builder` at v1.0; remediation not approved.
2. **Rounding rule.** `conventions.md` carries flat MROUND-5. The QS ratebase
   uses tiered rounding (R-ALL-42): >=100 → nearest 5, 20-99 → nearest 1, <20 → nearest
   0.10. The flat rule is retired but still present in three files here. Awaiting
   remediation.
3. **"not included" annotation.** Layer A treats text in the AMOUNT column as a violation.
   `conventions.md` and lesson 14 say the annotation is acceptable per Zaim convention and
   must never be flagged. Unresolved. Interim handling: do not flag the annotation itself,
   but **do** flag a line that carries a quantity and sits inside the priced schedule while
   showing no rate — that is a scope-claim risk regardless of the annotation rule.
4. **Authority.** Where this skill and `mahareka-qs-agent` disagree on a rate, the QS agent
   and `QS_RATEBASE` win. This skill audits documents; it does not own rates.

