# Acceptance Report

- Status: FAIL
- Package: examples\outputs\synthetic_execution
- Data source: synthetic
- Schema: simple
- Cohort rows: 4
- Final attrition count: 4

## Blocking Failures

- followup_outcome_available_rule: Violations: ['S008']

## Warnings

- None.

## Checks

| Check | Result | Detail |
| --- | --- | --- |
| required_files | PASS | All required files exist. |
| attrition_monotone | PASS | Attrition counts: [8, 8, 8, 7, 6, 5, 4] |
| cohort_row_count_matches_attrition | PASS | cohort rows=4, final attrition=4 |
| unique_participant_ids | PASS | No duplicate participant identifiers. |
| baseline_before_or_at_time_zero | PASS | Violations: [] |
| followup_after_time_zero | PASS | Violations: [] |
| baseline_age_rule | PASS | Violations: [] |
| baseline_dementia_free_rule | PASS | Violations: [] |
| apoe_available_rule | PASS | Violations: [] |
| followup_outcome_available_rule | FAIL | Violations: ['S008'] |
| leakage_report_temporal_warning | PASS | Leakage report contains temporal warning. |
| leakage_report_apoe_warning | PASS | Leakage report mentions APOE selection risk. |
| leakage_report_followup_warning | PASS | Leakage report mentions follow-up selection risk. |
| data_quality_report_missingness | PASS | Data quality report mentions missingness or structural missingness. |

## Recommendation

Fix blocking failures before downstream analysis.
