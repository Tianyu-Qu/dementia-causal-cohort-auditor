# Output Templates

## v0.1 Design Audit Template

```markdown
## Mode

Design Critic

## Study Design Restatement

[Restate the research question in cohort and causal inference terms.]

## Draft Estimand

- Target population:
- Treatment/exposure:
- Comparator:
- Time zero:
- Follow-up start:
- Outcome:
- Causal contrast:

## Red Flags

- [Critical issue and why it matters.]

## Must-Answer Human Confirmations

1. [Question] Why it matters: [reason].

## Temporal Ordering Review

| Design object | Proposed timing | Risk | Required clarification |
| --- | --- | --- | --- |
| Time zero |  |  |  |
| Baseline covariates |  |  |  |
| Exposure |  |  |  |
| Outcome |  |  |  |

## Leakage and Bias Checks

- Immortal time:
- Post-treatment adjustment:
- Confounding by indication:
- Informative censoring:
- Positivity:

## Missingness and Measurement Concerns

- [Concern.]

## Recommended Sensitivity Analyses

- [Sensitivity analysis.]

## Next-Step Recommendation

[One concrete next step.]
```

## v0.4 Execution Package Manifest Template

```json
{
  "schema_version": "0.4",
  "created_by": "dementia-causal-cohort-auditor",
  "data_source": "synthetic",
  "rules": {
    "time_zero": "first DrugA or DrugB start date",
    "baseline_visit": "latest visit on or before time zero",
    "age_rule": "baseline age >= 65",
    "baseline_dementia_rule": "baseline cognitive_status != dementia",
    "apoe_rule": "apoe_e4_count not missing",
    "followup_rule": "at least one visit after time zero"
  },
  "outputs": [
    "cohort.csv",
    "attrition_table.csv",
    "data_quality_report.md",
    "leakage_report.md"
  ]
}
```

## v0.3 NACC Variable Mapping Template

```yaml
schema_version: "0.3"
adapter: nacc
mapping_metadata:
  status: draft
  created_by: dementia-causal-cohort-auditor
  release_or_extract_date: unresolved
  uds_versions: []
  notes: Candidate mapping; confirm against the local NACC data dictionary before execution.

source_dictionary:
  files_reviewed: []
  dictionary_format: unresolved
  missing_code_rules_reviewed: false

core_concepts:
  - concept_id: participant_id
    label: Participant identifier
    required: true
    status: unresolved
    grain: participant
    candidate_fields: []
    selected_field: unresolved
    timing_rule: time invariant identifier
    notes: ""

unresolved_items: []
temporal_warnings: []
missingness_warnings: []

readiness:
  ready_for_cohort_spec: false
  blocking_issues: []
```

## v0.2 Cohort Definition Template

```yaml
schema_version: "0.2"
metadata:
  status: needs_human_confirmation
  created_by: dementia-causal-cohort-auditor
  study_phase: cohort_spec_builder
  notes: Draft spec generated after design audit.

study_question: ""

estimand:
  target_population: ""
  treatment_strategy: ""
  comparator_strategy: ""
  assignment_time: ""
  follow_up_start: ""
  outcome: ""
  causal_contrast: ""

data_source:
  name: ""
  adapter: ""
  required_files: []
  data_dictionary_required: true

population:
  description: ""

exposure:
  name: ""
  definition: ""
  timing: ""
  washout_period: unresolved
  grace_period: unresolved
  lag_period: unresolved

comparator:
  name: ""
  definition: ""
  timing: ""

time_zero:
  definition: unresolved
  candidate_definitions: []
  rationale: ""

baseline_window:
  start: unresolved
  end: unresolved
  covariate_timing_rule: all baseline covariates must be measured before or at time zero unless explicitly justified

follow_up:
  start: unresolved
  end: unresolved
  censoring_events: []
  competing_events: []

outcome:
  name: ""
  definition: unresolved
  measurement_window: unresolved
  minimum_meaningful_change: unresolved

inclusion_criteria: []
exclusion_criteria: []
covariates: []

missingness_plan:
  required_checks: []
  planned_handling: unresolved

leakage_checks:
  required_checks: []

attrition_plan:
  stages: []
  count_field: participant_id

sensitivity_analyses: []
assumptions: []
unresolved_items: []

readiness:
  ready_for_execution: false
  blocking_issues: []
```
