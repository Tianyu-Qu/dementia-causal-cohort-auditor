# NACC First Executable Cohort

Use this reference for v0.15 after design-to-code planning when the user asks to build the first executable NACC cohort package.

## Scope

v0.15 supports one task family first:

- prediction / cognitive decline

The default safe path is NACC-like synthetic data. Real NACC execution requires explicit user approval plus an approved design and mapping.

## Script

Run:

```powershell
python skills/dementia-causal-cohort-auditor/scripts/build_nacc_prediction_cohort.py --input-dir <NACC_LIKE_INPUT_DIR> --output-dir <COHORT_OUTPUT_DIR>
```

The script writes:

- `cohort_index.csv`
- `feature_table.csv`
- `outcome_table.csv`
- `cohort.csv`
- `attrition_table.csv`
- `data_quality_report.md`
- `leakage_report.md`
- `reproducibility_manifest.json`
- `acceptance_report.md`

## Default Prediction Design

- Time zero: first valid NACC-like UDS visit.
- Baseline window: index visit only.
- Population: baseline age >=65, baseline dementia-free, APOE available.
- Follow-up: at least one post-index visit with non-missing MMSE.
- Outcome: `cognitive_decline_label = 1` when follow-up MMSE minus baseline MMSE is <= -1.

## Required Acceptance

Run or verify `scripts/run_acceptance_checks.py` on the package directory. The acceptance report must check:

- required package files
- attrition monotonicity
- one row per participant
- outcome visit after index
- baseline age rule
- baseline dementia-free rule
- APOE availability
- baseline and follow-up MMSE availability
- cognitive-decline label calculation
- leakage and missingness reports

## Gate

This is the first executable path, but it is not a treatment-effect estimator and not a general NACC cohort engine.

For real NACC, do not run patient-level construction unless the user explicitly approves execution and the design packet/mapping are approved.
