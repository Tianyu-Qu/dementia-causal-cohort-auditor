# Causal Audit Rules

Use this reference for observational treatment effect estimation and real-world evidence cohort critique.

## Estimand Elements

Identify or ask for:

- target population
- treatment strategies
- comparator strategy
- treatment assignment time
- follow-up start
- outcome definition
- causal contrast
- analysis perspective: ITT, per-protocol, as-treated, or other

## Temporal Ordering

Every baseline covariate must be measured before treatment assignment or index date unless explicitly justified. Outcomes must start after follow-up begins. Exposure definitions must not use future adherence unless the estimand is per-protocol or as-treated and the induced selection is addressed.

## Treatment Windows

Check whether the design needs:

- washout period for new-user design
- grace period for treatment initiation or switching
- lag period before outcome counting
- exposure persistence rule for clinically meaningful treatment
- drug-specific onset or latency evidence
- sensitivity analyses across plausible windows

## Bias Checks

- Immortal time bias: eligibility or exposure classification requires surviving or remaining observed after time zero.
- Confounding by indication: treatment choice is related to disease severity or prognosis.
- Comparator bias: non-user comparator may differ systematically from treated users; consider active comparator.
- Post-treatment adjustment: covariates affected by treatment are adjusted as baseline variables.
- Collider bias: conditioning on variables influenced by both treatment and outcome risk.
- Informative censoring: dropout, death, or treatment discontinuation relates to outcome.
- Positivity violations: some subgroups have near-zero probability of receiving one treatment.
- Leakage: future outcomes, diagnoses, or measurements enter baseline features.

## Human Confirmation Triggers

Ask before coding when:

- time zero is ambiguous
- exposure definition uses multiple possible dates
- comparator is not clinically meaningful
- outcome window is unspecified
- baseline covariate window is unspecified
- drug onset or lag period may matter
- follow-up requirements could induce selection bias
