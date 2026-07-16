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
