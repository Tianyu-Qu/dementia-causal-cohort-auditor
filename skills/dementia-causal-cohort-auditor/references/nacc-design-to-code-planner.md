# NACC Design-to-Code Planner

Use this reference after v0.12 design approval packet creation and v0.13 aggregate validation, before any executable cohort construction.

## Purpose

Convert an approved or review-ready NACC cohort design into a build plan and pseudocode:

- `build_plan.md`
- `build_pseudocode.py`
- `implementation_checklist.md`
- `validation_test_plan.md`
- `planner_manifest.json`

This stage must not read patient-level rows and must not create cohort outputs.

## Workflow

1. Locate the v0.12 design packet directory.
2. Locate the v0.13 aggregate validation directory if available.
3. Run:

   ```powershell
   python skills/dementia-causal-cohort-auditor/scripts/plan_nacc_cohort_build.py --design-packet-dir <DESIGN_PACKET_DIR> --aggregate-validation-dir <AGGREGATE_VALIDATION_DIR> --output-dir <PLANNER_OUTPUT_DIR>
   ```

4. Review the plan with the user.
5. Stop before executable cohort construction.

## Required Gate

The planner may generate a blocked draft even when the design packet is unresolved. It must clearly keep:

```yaml
cohort_construction_performed: false
ready_for_executable_cohort_build: false
```

Only move to executable construction when the user has approved:

- time zero/index visit
- baseline window
- baseline dementia-free rule
- outcome definition and follow-up window
- minimum follow-up role
- APOE missingness handling
- UDS/form-version harmonization
- death/dropout handling
- selected field mappings and local dictionary confirmation

## Agent Behavior

- Treat `build_pseudocode.py` as pseudocode, not runnable production code.
- Explain blockers plainly.
- Do not silently promote unresolved mappings to selected fields.
- Do not read real patient rows.
- Do not emit `cohort.csv`, `feature_table.csv`, or patient-level outputs.
