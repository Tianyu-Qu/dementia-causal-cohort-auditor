# Real NACC Guarded Execution Pilot

Use this reference for v0.15.1 when the user explicitly asks to test whether the skill can construct a real NACC cohort from the local messy NACC project.

## Scope

This pilot is intentionally narrow:

- Core file must be `investigator_ftldlbd_nacc70.csv`.
- Task must be prediction / cognitive decline.
- Population rule: age >=65, baseline dementia-free, APOE available.
- Outcome rule: at least one post-index MMSE follow-up; cognitive decline label is follow-up MMSE minus baseline MMSE <= -1.
- Output goes to a local private directory and must not be committed.

## Required Command

Only run after explicit user approval:

```powershell
python skills/dementia-causal-cohort-auditor/scripts/build_real_nacc_prediction_pilot.py --core-file "<REAL_NACC_DIR>\investigator_ftldlbd_nacc70.csv" --output-dir "<LOCAL_PRIVATE_OUTPUT_DIR>" --allow-real-data --approved-pilot-rules
```

Without both `--allow-real-data` and `--approved-pilot-rules`, the script must refuse execution and write a blocker report.

## Outputs

The pilot writes patient-level files locally:

- `cohort_index.csv`
- `feature_table.csv`
- `outcome_table.csv`
- `cohort.csv`
- `attrition_table.csv`
- `data_quality_report.md`
- `leakage_report.md`
- `reproducibility_manifest.json`
- `acceptance_report.md`
- `privacy_notice.md`

## Reporting Boundary

When summarizing results in chat:

- report only aggregate counts, attrition stages, acceptance status, and warnings
- do not paste NACCID values
- do not paste patient rows
- do not commit output directories

## Gate

This is a guarded pilot, not a frozen scientific cohort. Before scientific use, require local dictionary confirmation of field semantics, missing-code rules, UDS/form-version handling, outcome definition, and final human approval.
