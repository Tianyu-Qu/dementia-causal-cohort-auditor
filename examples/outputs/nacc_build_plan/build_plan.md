# NACC Cohort Build Plan

- Planner status: blocked_planner_draft
- Task type: prediction_cognitive_decline
- Study question: I want to build a NACC cohort of people 65+, dementia-free at baseline, at least two visits, with APOE, to predict cognitive decline.
- Patient-level data read: no
- Cohort construction performed: no
- Ready for executable cohort build: false

## Inputs Expected by the Future Builder

- Approved `cohort_definition.yaml` with resolved time zero, baseline window, outcome window, and missingness rules.
- Approved `mapping.yaml` with selected fields and dictionary-confirmed coding.
- Aggregate validation packet from v0.13.
- Local NACC core clinical/UDS table path and optional module paths.

## Concept-to-Field Plan

- participant_id: selected=unresolved; candidates=NACCID; approval=not_approved
- visit_id: selected=unresolved; candidates=NACCVNUM; approval=not_approved
- visit_date: selected=unresolved; candidates=VISITMO, VISITDAY, VISITYR; approval=not_approved
- age_at_visit: selected=unresolved; candidates=NACCAGE; approval=not_approved
- baseline_cognitive_status: selected=unresolved; candidates=NACCUDSD, DEMENTED, CDRGLOB; approval=not_approved
- longitudinal_cognitive_outcome: selected=unresolved; candidates=NACCMMSE, NACCMOCA, CDRSUM, CDRGLOB, NACCUDSD; approval=not_approved
- follow_up_availability: selected=unresolved; candidates=NACCVNUM, NACCDAYS, NACCFDYS, NACCAVST; approval=not_approved
- apoe: selected=unresolved; candidates=NACCNE4S, NACCAPOE; approval=not_approved
- sex: selected=unresolved; candidates=SEX; approval=not_approved
- education: selected=unresolved; candidates=EDUC; approval=not_approved
- cdr_global: selected=unresolved; candidates=CDRGLOB; approval=not_approved
- cdr_sum: selected=unresolved; candidates=CDRSUM; approval=not_approved
- uds_version: selected=unresolved; candidates=PACKET, FORMVER, UDSVER*, NACCFORM, NPFORMVER; approval=not_approved
- death_dropout: selected=unresolved; candidates=NACCDIED, NACCDAYS, NACCFDYS, NACCAVST, DROPACT; approval=not_approved

## Execution Stages

1. `all_core_clinical_records`: Load core NACC clinical/UDS rows with minimal selected columns.
2. `valid_participant_id`: Drop rows without a valid participant identifier; never write IDs to logs.
3. `valid_visit_order_or_date`: Create visit order and visit date; flag incomplete dates.
4. `age_eligible_if_required`: Select index candidates satisfying the approved age rule.
5. `dementia_free_baseline_if_required`: Apply the approved dementia-free baseline rule.
6. `apoe_available_if_required`: Apply the approved APOE availability rule and report attrition.
7. `follow_up_or_outcome_ascertainable`: Confirm post-index follow-up/outcome availability without temporal leakage.

## Required Builder Functions

- `load_selected_nacc_tables(config)`
- `normalize_missing_codes(df, dictionary_rules)`
- `construct_visit_date(df)`
- `select_index_visit(df, approved_time_zero_rule)`
- `apply_baseline_eligibility(df, index_df, approved_rules)`
- `derive_prediction_outcome(df, index_df, approved_outcome_rule)`
- `build_feature_table(df, index_df, approved_predictor_window)`
- `write_attrition_table(stage_counts)`
- `write_data_quality_report(checks)`
- `write_leakage_report(checks)`
- `write_reproducibility_manifest(config, inputs, code_version)`

## Blockers

- Design packet status is not approved: needs_human_confirmation
- Mapping contains unresolved selected_field entries.
- Mapping contains not_approved concepts.

## Warnings

- None.

## Gate

This plan is for human review and future implementation only. Do not run patient-level cohort construction until v0.15 conditions are met.
