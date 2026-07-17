# NACC Cohort Builder Validation Test Plan

These tests are for the future executable builder. v0.14 does not construct a cohort.

## test_no_patient_ids_in_logs

- Purpose: Builder logs and reports must not list NACCID values.
- Expected result: pass before releasing any cohort package.

## test_attrition_monotonic

- Purpose: Attrition participant counts must be monotonic non-increasing.
- Expected result: pass before releasing any cohort package.

## test_unique_index_visit

- Purpose: Each participant must have exactly one index visit.
- Expected result: pass before releasing any cohort package.

## test_outcome_after_time_zero

- Purpose: Outcome measurements must occur after time zero.
- Expected result: pass before releasing any cohort package.

## test_no_post_index_features

- Purpose: Feature table must exclude post-index variables unless explicitly approved.
- Expected result: pass before releasing any cohort package.

## test_duplicate_visit_detection

- Purpose: Duplicate participant-visit rows must be detected and handled.
- Expected result: pass before releasing any cohort package.

## test_missingness_by_form_version

- Purpose: Missingness report must stratify key fields by form/version context.
- Expected result: pass before releasing any cohort package.

## test_apoe_attrition_reported

- Purpose: APOE restriction must produce explicit attrition and missingness counts.
- Expected result: pass before releasing any cohort package.

## test_sensitivity_hooks_present

- Purpose: Approved sensitivity-analysis hooks must be represented in config.
- Expected result: pass before releasing any cohort package.
