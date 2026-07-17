# NACC Aggregate Validation Report

- Status: aggregate_supported_pending_design_approval
- Real data mode: true
- Patient-level output: no
- Cohort construction performed: no
- Ready for cohort construction: false

## Aggregate Evidence

- Core table: `uds_visits.csv`
- Total rows scanned: 18
- Unique participants: 9
- Participants with >=2 visits: 8
- Duplicate participant-visit pairs: 1
- All-row age min/median/max: 63.0 / 72.5 / 81.0
- Baseline age >=65 count: 8
- Baseline APOE available count: 8
- Baseline cognitive-status available count: 8

## Field Evidence

- participant_id: NACCID
- visit_id: NACCVNUM
- visit_date: VISITMO, VISITDAY, VISITYR
- age_at_visit: NACCAGE
- sex: participants.csv::SEX
- education: participants.csv::EDUC
- apoe: participants.csv::NACCNE4S
- baseline_cognitive_status: NACCUDSD, CDRGLOB
- cognitive_score: NACCMMSE
- cdr_global: CDRGLOB
- cdr_sum: CDRSUM
- follow_up_context: missing
- form_version_context: UDSVER

## Auxiliary Participant-Level Evidence

- apoe: participants.csv::NACCNE4S
- sex: participants.csv::SEX
- education: participants.csv::EDUC

## Blockers

- No aggregate-only blockers detected for moving to design refinement/approval.

## Warnings

- No death/follow-up context detected; dropout/censoring handling remains unresolved.

## Gate

Aggregate validation can support human design approval, but it must not approve cohort construction by itself. Proceed only after field definitions, missing-code rules, outcome definition, time zero, and follow-up rules are approved.
