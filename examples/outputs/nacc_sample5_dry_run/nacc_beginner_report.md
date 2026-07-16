# Beginner NACC Navigation Report

## Plain-English status

- Scanned files: 4
- Rows visible to this dry run: 20
- Real-data safety mode: true
- Overall readiness: needs_human_confirmation
- Inferred grains: {'participant_or_module': 2, 'visit_or_longitudinal': 2}

This report is meant for users who know modeling/code but do not yet know NACC well. It translates file headers and tiny samples into practical next steps.

## What this sample appears to contain

- participant_id
- center_id
- visit_id
- visit_date
- age_at_visit
- sex
- education
- apoe
- cognitive_status
- cdr_global
- cdr_sum
- cognitive_score
- medication_records
- medication_temporality_support
- death_dropout
- uds_version

## What is missing or unresolved

- No tracked concept is completely missing from headers, but human confirmation is still required.

## Medication warning

- NACC medication/treatment fields, when present, should be interpreted as medication records, not causal-ready exposure.
- They are not automatically a treatment exposure variable.
- Medication records detected: yes
- Medication timing support detected: yes
- For treatment-effect estimation, the user must still define active comparator, new-user status, washout, grace period, lag period, and exposure persistence.

## Blockers / gates

- All required surface concepts are present, but human confirmation is required before execution.
- Real-data mode is enabled; dry-run evidence alone must not authorize execution.

## Suggested first real-data experiment

Use a five-row sample only to verify that the skill can understand the local NACC release structure. Do not estimate effects or train a final model from five rows.

Recommended command pattern:

```powershell
python skills/dementia-causal-cohort-auditor/scripts/make_header_samples.py --input-dir <REAL_NACC_DIR> --output-dir <SAFE_SAMPLE_DIR> --rows 5
python skills/dementia-causal-cohort-auditor/scripts/scan_nacc_files.py --input-dir <SAFE_SAMPLE_DIR> --output-dir <DRY_RUN_OUTPUT_DIR> --sample-rows 5 --real-data-mode
```
