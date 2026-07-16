# Cohort Spec Schema

Use this reference for v0.2 Cohort Spec Builder mode. The goal is to turn an audited study design into a structured, reviewable `cohort_definition.yaml` before generating SQL or Python.

## Core Rule

Do not hide uncertainty. If a design decision is unresolved, keep the field explicit and list it under `unresolved_items`. A draft spec can be useful, but it must not pretend to be execution-ready.

## Required Top-Level Fields

- `schema_version`
- `metadata`
- `study_question`
- `estimand`
- `data_source`
- `population`
- `exposure`
- `comparator`
- `time_zero`
- `baseline_window`
- `follow_up`
- `outcome`
- `inclusion_criteria`
- `exclusion_criteria`
- `covariates`
- `missingness_plan`
- `leakage_checks`
- `attrition_plan`
- `sensitivity_analyses`
- `assumptions`
- `unresolved_items`
- `readiness`

## Required Nested Fields

- `metadata.status`: `draft`, `needs_human_confirmation`, or `ready_for_execution`.
- `metadata.created_by`: normally `dementia-causal-cohort-auditor`.
- `estimand.target_population`
- `estimand.treatment_strategy`
- `estimand.comparator_strategy`
- `estimand.assignment_time`
- `estimand.follow_up_start`
- `estimand.outcome`
- `estimand.causal_contrast`
- `data_source.name`
- `data_source.adapter`
- `time_zero.definition`
- `baseline_window.start`
- `baseline_window.end`
- `follow_up.start`
- `follow_up.end`
- `outcome.definition`
- `readiness.ready_for_execution`
- `readiness.blocking_issues`

## Readiness Logic

Set `readiness.ready_for_execution: false` when any of these are unresolved:

- time zero
- exposure or comparator definition
- outcome start
- baseline covariate timing
- treatment lag/washout/grace period when treatment is involved
- whether follow-up requirements create selection or immortal time bias
- dataset variable mappings for required criteria

Set `metadata.status: needs_human_confirmation` when any must-answer design question remains.

## Criteria Format

Represent inclusion and exclusion criteria as lists of objects:

```yaml
inclusion_criteria:
  - id: inc_age_65
    description: Age at time zero is at least 65 years.
    computable: true
    concept: age_at_time_zero
    time_window: at_time_zero
    field_mapping: unresolved
    validation_check: age_at_time_zero >= 65
```

## Covariate Format

Each covariate should include a timing rule:

```yaml
covariates:
  - name: APOE e4 carrier status
    role: effect_modifier
    timing: time_invariant_but_availability_must_be_checked
    field_mapping: unresolved
    leakage_risk: selection_bias_if_post_index_availability_required
```

## Unresolved Item Format

```yaml
unresolved_items:
  - id: q_time_zero
    severity: blocking
    question: Is time zero first treatment initiation, first eligible visit, or another anchor?
    why_it_matters: Baseline covariates, follow-up, and outcome timing all depend on time zero.
```
