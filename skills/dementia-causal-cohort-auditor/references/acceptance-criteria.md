# Acceptance Criteria

Use this reference to judge whether an output is ready to hand off.

## v0.1 Design Critic Acceptance

An audit is acceptable when it includes:

- selected mode
- study design restatement
- draft estimand
- critical red flags
- must-answer human confirmations
- temporal ordering review
- leakage and bias checks
- missingness and measurement concerns
- sensitivity analysis recommendations
- clear next-step recommendation

## Methodological Acceptance

The audit must not:

- silently assume time zero
- silently assume baseline covariate timing
- treat "at least two follow-ups" as harmless
- ignore drug onset, washout, lag, or grace periods when treatment is involved
- use future measurements as baseline variables without flagging leakage
- conflate cohort eligibility, exposure classification, and outcome ascertainment

## Computational Acceptance

When execution is requested in later versions, every computable rule must have:

- a field or mapping
- a time window
- an inclusion/exclusion stage
- an attrition count expectation
- a validation check

Unmapped or unresolved rules must be explicitly listed.

## v0.2 Cohort Spec Acceptance

A `cohort_definition.yaml` is acceptable when:

- it contains every required top-level field in `references/cohort-spec-schema.md`
- it lists unresolved human decisions instead of silently assuming them
- time zero, baseline window, exposure timing, outcome timing, and follow-up are explicit
- inclusion and exclusion criteria are represented as reviewable objects, not only prose
- every baseline covariate has a timing or leakage note
- readiness is explicit

A spec is not execution-ready when `unresolved_items` contains any blocking item or `readiness.ready_for_execution` is false.

## v0.5 Execution Package Acceptance

An execution package is acceptable when:

- all required output files exist
- attrition counts are monotone non-increasing
- final attrition count equals the number of cohort rows
- there are no duplicate participant identifiers in the cohort
- baseline timing is on or before time zero
- follow-up timing is after time zero
- baseline age, dementia-free status, APOE availability, and outcome availability satisfy the cohort rules
- leakage and data quality reports contain visible warnings rather than burying assumptions

Use `references/acceptance-layer.md` for detailed checks and `scripts/run_acceptance_checks.py` to generate `acceptance_report.md`.
