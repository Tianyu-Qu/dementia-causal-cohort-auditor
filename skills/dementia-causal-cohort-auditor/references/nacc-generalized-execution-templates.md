# NACC Generalized Execution Templates

Use this reference for v0.16 when extending beyond prediction/cognitive-decline execution.

## Scope

v0.16 adds execution templates, not new real-data cohort builders, for:

- classification / phenotyping
- survival / progression
- biomarker-linked cohorts

The templates define required concepts, pseudocode, implementation checklists, and validation test plans. They must not read patient-level data or output cohort files.

## Script

Run:

```powershell
python skills/dementia-causal-cohort-auditor/scripts/generate_nacc_execution_template.py --task-family classification --output-dir <TEMPLATE_DIR>
python skills/dementia-causal-cohort-auditor/scripts/generate_nacc_execution_template.py --task-family survival_progression --output-dir <TEMPLATE_DIR>
python skills/dementia-causal-cohort-auditor/scripts/generate_nacc_execution_template.py --task-family biomarker_linked --output-dir <TEMPLATE_DIR>
```

## Outputs

Each template directory contains:

- `template_spec.yaml`
- `template_pseudocode.py`
- `implementation_checklist.md`
- `validation_test_plan.md`
- `template_manifest.json`
- `README.md`

## Required Gate

Keep:

```yaml
patient_level_data_read: false
cohort_construction_performed: false
real_data_outputs_created: false
```

Do not generate `cohort.csv`, `feature_table.csv`, `cohort_index.csv`, or any patient-level outputs in v0.16.

## Task-specific checks

Classification:

- confirm label definition
- prevent diagnostic label leakage into predictors
- report class counts and phenotype exclusivity

Survival/progression:

- define event, censoring, competing events, and time scale
- require event after time zero
- avoid immortal time and future follow-up conditioning

Biomarker-linked:

- identify biomarker module and linkage window
- report biomarker-selection attrition
- handle module-specific timing and missingness
