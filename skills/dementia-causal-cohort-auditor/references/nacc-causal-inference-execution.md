# NACC Causal Inference-Specific Execution

Use this reference for v0.17 when the user asks for treatment-effect estimation or causal inference execution.

## Scope

v0.17 adds a causal-specific execution template and readiness gate. It does not construct a treatment-effect cohort and does not estimate effects.

The key rule is strict:

NACC medication records are not automatically causal-ready exposure histories.

## Script

Run:

```powershell
python skills/dementia-causal-cohort-auditor/scripts/generate_nacc_causal_execution_package.py --output-dir <OUTPUT_DIR>
```

Optional:

```powershell
python skills/dementia-causal-cohort-auditor/scripts/generate_nacc_causal_execution_package.py --output-dir <OUTPUT_DIR> --estimation-family ate --nacc-medication-temporality insufficient
```

## Outputs

- `causal_execution_spec.yaml`
- `causal_pseudocode.py`
- `target_trial_checklist.md`
- `causal_readiness_report.md`
- `causal_validation_test_plan.md`
- `causal_template_manifest.json`

## Required Causal Gate

Do not build a causal cohort until all are approved:

- target-trial protocol
- treatment strategy
- active comparator or justified control
- new-user definition
- washout window
- grace period
- lag window
- time zero
- baseline covariate window
- outcome definition/window
- censoring and competing-event handling
- positivity assessment
- confounding adjustment plan
- local dictionary-confirmed exposure timing

## NACC Medication Rule

Fields such as `ANYMEDS`, `MEDS`, `DRUG1`-style medication slots, or treatment-name records may indicate medication records, but they do not by themselves establish:

- start date
- stop date
- current use at time zero
- persistence
- discontinuation
- washout eligibility
- grace period membership
- lag-window exposure status

If temporality is not confirmed, v0.17 must output a blocker instead of a causal cohort.
