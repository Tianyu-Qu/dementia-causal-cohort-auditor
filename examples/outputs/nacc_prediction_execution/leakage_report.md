# NACC Prediction Cohort Leakage Report

## Temporal Checks

- No deterministic temporal leakage detected: every outcome visit is after index.

## Design Warnings

- Baseline predictors are limited to index-visit or time-invariant fields.
- Outcome MMSE is taken from post-index follow-up visits only.
- APOE availability restriction can create selection bias and must be reported in attrition.
- Requiring follow-up can condition on future observation; interpret as outcome ascertainment unless approved otherwise.
- UDS/form-version differences can create structural missingness and should be assessed before downstream modeling.
