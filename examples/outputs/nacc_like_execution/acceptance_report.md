# Acceptance Report

- Status: PASS
- Package: F:\Healthcare\Dementia Causal-Cohort Auditor\examples\outputs\nacc_like_execution
- Data source: nacc_like_synthetic
- Schema: nacc_like
- Cohort rows: 3
- Final attrition count: 3

## Blocking Failures

- None.

## Warnings

- None.

## Checks

| Check | Result | Detail |
| --- | --- | --- |
| required_files | PASS | All required files exist. |
| attrition_monotone | PASS | Attrition counts: [9, 9, 7, 7, 7, 6, 6, 5, 5, 4, 3, 3] |
| cohort_row_count_matches_attrition | PASS | cohort rows=3, final attrition=3 |
| unique_participant_ids | PASS | No duplicate participant identifiers. |
| baseline_before_or_at_time_zero | PASS | Violations: [] |
| followup_after_time_zero | PASS | Violations: [] |
| baseline_age_rule | PASS | Violations: [] |
| baseline_dementia_free_rule | PASS | Violations: [] |
| apoe_available_rule | PASS | Violations: [] |
| followup_outcome_available_rule | PASS | Violations: [] |
| leakage_report_temporal_warning | PASS | Leakage report contains temporal warning. |
| leakage_report_apoe_warning | PASS | Leakage report mentions APOE selection risk. |
| leakage_report_followup_warning | PASS | Leakage report mentions follow-up selection risk. |
| data_quality_report_missingness | PASS | Data quality report mentions missingness or structural missingness. |

## Recommendation

Package is acceptable for methodological review; do not interpret treatment effects without design sign-off.
