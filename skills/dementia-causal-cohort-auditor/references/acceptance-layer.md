# Acceptance Layer

Use this reference for v0.5 Acceptance Layer work.

## Purpose

The acceptance layer checks whether a cohort execution package is safe to hand off for review. It does not prove the causal design is correct; it verifies that the generated package is internally consistent and that critical methodological warnings are visible.

## Required Package Files

- `cohort.csv`
- `attrition_table.csv`
- `data_quality_report.md`
- `leakage_report.md`
- `reproducibility_manifest.json`

## Required Checks

- All required files exist.
- Attrition counts are monotone non-increasing.
- Final attrition count equals the number of cohort rows.
- Cohort contains no duplicate participant identifiers.
- Baseline visit date is on or before time zero.
- Follow-up visit date is after time zero.
- Baseline age meets the age rule.
- Baseline dementia exclusion rule is satisfied.
- APOE/genetic field is non-missing when required.
- Follow-up cognitive outcome is non-missing.
- Reports mention key design warnings: APOE selection, follow-up selection, and temporal leakage.

## Result Status

- `PASS`: no blocking failures.
- `WARN`: no blocking failures, but warnings remain.
- `FAIL`: one or more blocking failures.

Use `scripts/run_acceptance_checks.py` to generate `acceptance_report.md`.
