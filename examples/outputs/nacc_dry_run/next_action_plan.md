# Next Action Plan

## Immediate next steps

1. Confirm the NACC release, UDS versions, and module list against the official local data dictionary.
2. Review `nacc_variable_mapping_candidates.yaml` and select fields only when their meanings match the study objective.
3. Decide the first task profile: classification/prediction/trajectory/representation learning/treatment-effect/survival.
4. Treat five-row samples as structural smoke tests only; use aggregate full-data checks before final cohort construction.

## If your goal is treatment-effect estimation

1. Verify whether the NACC extract includes A4/A4a or other medication/treatment modules.
2. Decide whether medication records can define incident treatment, prevalent use, active comparator, or only descriptive covariates.
3. Specify washout, grace period, lag window, exposure persistence, and outcome start before code generation.

## Current blockers from dry run

- All required surface concepts are present, but human confirmation is required before execution.
