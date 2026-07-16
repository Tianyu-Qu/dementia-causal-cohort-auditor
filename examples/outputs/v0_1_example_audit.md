## Mode

Design Critic.

## Study Design Restatement

The proposed study is an observational treatment effect study comparing Drug A versus Drug B among adults aged 65 or older who are dementia-free at baseline, have APOE information, and have at least two follow-up visits. The intended outcome is slowing cognitive decline, but the cognitive instrument, minimum meaningful change, and outcome window are not yet specified.

## Draft Estimand

- Target population: adults aged 65 or older who are eligible for either Drug A or Drug B and are dementia-free at time zero.
- Treatment/exposure: Drug A initiation.
- Comparator: Drug B initiation.
- Time zero: unresolved; likely first eligible treatment initiation date.
- Follow-up start: unresolved; may require a lag period after treatment initiation.
- Outcome: unresolved cognitive decline definition.
- Causal contrast: unresolved; likely Drug A versus Drug B effect on cognitive decline over a fixed follow-up window.

## Red Flags

- Time zero is not defined. Without this, baseline eligibility, covariate timing, exposure assignment, and outcome timing cannot be validated.
- Requiring at least two follow-up visits may induce selection bias if early death, dropout, or rapid decline prevents follow-up.
- APOE availability may be non-random and could create selection bias if genotyping depends on family history, disease severity, or research-center practices.
- Drug onset and outcome latency are unspecified. Cognitive outcomes may need a lag window and sensitivity analyses.
- Comparator design is unspecified. An active-comparator new-user design may be needed to reduce confounding by indication.

## Must-Answer Human Confirmations

1. What is time zero: first Drug A/B initiation, first eligible visit, or another anchor? Why it matters: all baseline and follow-up windows depend on it.
2. Should this be a new-user active-comparator design with a washout period? Why it matters: prior use can bias treatment effect estimates.
3. How is dementia-free baseline defined? Why it matters: diagnosis, cognitive status, and CDR-like measures may disagree.
4. When should outcome counting begin after treatment initiation? Why it matters: drug onset or latency can make immediate outcomes biologically implausible.
5. Is APOE measured before time zero required, or is post-time-zero APOE allowed? Why it matters: post-index availability can create selection and leakage concerns.
6. Should the two-follow-up requirement be an eligibility rule or an outcome ascertainment rule? Why it matters: making it eligibility can create immortal time or survivor bias.

## Temporal Ordering Review

| Design object | Proposed timing | Risk | Required clarification |
| --- | --- | --- | --- |
| Time zero | Not specified | Invalid baseline and outcome ordering | Define anchor date |
| Baseline covariates | Not specified | Post-treatment adjustment risk | Define pre-index window |
| Exposure | Drug A versus Drug B | Prior use and persistence unclear | Define new-user, washout, grace rules |
| Outcome | Cognitive decline | Outcome window and lag unclear | Define instrument, change threshold, start date |

## Leakage and Bias Checks

- Immortal time: possible if two follow-up visits are required after baseline before cohort entry.
- Post-treatment adjustment: possible if cognition, comorbidities, or medication variables are measured after treatment start.
- Confounding by indication: likely if Drug A and Drug B are prescribed for different clinical profiles.
- Informative censoring: likely if dropout or death relates to cognition or treatment.
- Positivity: unknown until treatment distributions by age, baseline cognition, APOE, and comorbidity are inspected.

## Missingness and Measurement Concerns

- APOE missingness may not be random.
- Cognitive test missingness may depend on disease severity, visit modality, center, language, or dropout.
- Diagnosis and cognitive score definitions may conflict and need a hierarchy.

## Recommended Sensitivity Analyses

- Lag windows: 0, 30, 90, and 180 days after treatment initiation.
- Follow-up requirement: compare requiring two visits at baseline versus treating follow-up availability as part of outcome ascertainment.
- APOE handling: complete-case analysis versus missingness indicator or imputation strategy.
- Estimand: ITT-like new-user analysis versus as-treated analysis with censoring at discontinuation/switch.

## Next-Step Recommendation

Answer the must-confirm questions, then convert the study into a structured `cohort_definition.yaml` before generating SQL or Python.
