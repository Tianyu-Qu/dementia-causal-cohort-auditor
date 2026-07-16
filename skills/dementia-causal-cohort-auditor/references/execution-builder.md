# Execution Builder

Use this reference for v0.4 Execution Builder mode.

## Scope

v0.4 supports a simple synthetic dementia cohort execution path. v0.4.1 adds a NACC-like synthetic execution path with NACC-style field names and structural missingness. Do not treat either path as production NACC execution. For real NACC, first require a confirmed `nacc_variable_mapping.yaml` and `cohort_definition.yaml`.

## Execution Package Outputs

An execution package should produce:

- `cohort.csv`
- `attrition_table.csv`
- `data_quality_report.md`
- `leakage_report.md`
- `reproducibility_manifest.json`

## Synthetic Cohort Rules

The v0.4 synthetic execution path uses these rules:

- Eligible treatments: `DrugA` and `DrugB`.
- Time zero: first eligible DrugA or DrugB start date.
- Baseline visit: latest visit on or before time zero.
- Age rule: baseline age must be at least 65.
- Dementia-free baseline: baseline cognitive status must not be `dementia`.
- APOE rule: APOE e4 count/status must not be missing.
- Follow-up rule: at least one visit after time zero is required for outcome ascertainment.
- Outcome demo rule: use the last post-time-zero MMSE as `followup_mmse` and compute `mmse_change = followup_mmse - baseline_mmse`.

## Required Reports

Attrition table stages:

1. all_patients
2. has_drug_a_or_b_initiation
3. has_baseline_visit
4. age_eligible
5. dementia_free_at_baseline
6. apoe_available
7. followup_available

## NACC-like Synthetic Cohort Rules

The v0.4.1 NACC-like synthetic execution path uses NACC-style CSV files:

- `participants.csv`: `NACCID`, `NACCADC`, `SEX`, `EDUC`, `NACCNE4S`
- `uds_visits.csv`: `NACCID`, `NACCVNUM`, `VISITMO`, `VISITDAY`, `VISITYR`, `NACCAGE`, `NACCUDSD`, `CDRGLOB`, `CDRSUM`, `NACCMMSE`, `UDSVER`
- `medications.csv`: `NACCID`, `NACCVNUM`, `DRUGNAME`, `DRUG_STARTMO`, `DRUG_STARTYR`, `CURRENT_USE`, `UDSVER`
- `followup_status.csv`: `NACCID`, `DECEASED`, `DROPOUT`, `LAST_CONTACT_YR`

NACC-like attrition table stages:

1. all_participants
2. has_required_uds_visit_records
3. has_valid_visit_order_or_date
4. has_treatment_exposure_module_available
5. has_active_comparator_exposure
6. has_baseline_candidate_visit
7. baseline_age_eligible
8. baseline_dementia_free
9. has_required_cognitive_status_fields
10. has_neuropsych_outcome_available
11. has_apoe_or_genetics_available
12. has_post_index_followup_visit

Use `scripts/generate_nacc_like_synthetic_data.py` and `scripts/build_nacc_like_cohort.py` for this path.

Data quality report:

- duplicate visit keys
- missing APOE count
- missing baseline MMSE among included patients
- missing follow-up MMSE among included patients
- treatment group counts

Leakage report:

- baseline visit after time zero
- outcome visit on or before time zero
- APOE availability warning
- follow-up availability selection warning

## Human Gate

For real NACC, ADNI, UKB, EHR, or OMOP data, do not execute cohort construction unless variable mapping, missing codes, time zero, baseline window, exposure timing, outcome window, and readiness are explicitly confirmed.
