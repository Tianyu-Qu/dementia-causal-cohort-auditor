# NACC Task Intent Questions

Primary task: Prediction / cognitive decline

These questions must be answered before design approval and cohort construction.

## Must-answer questions

- [time_zero] Is time zero/index visit the first visit, the first eligible visit, or a specific measurement/event date?
- [baseline_window] What visits or time range belong to the baseline window, and which variables must be measured before time zero?
- [minimum_followup] Is the minimum follow-up requirement an eligibility criterion or an outcome-ascertainment requirement?
- [missingness] For APOE, cognitive scales, and diagnostic status, should missing values cause exclusion, be encoded as missing, or be handled through sensitivity analyses?
- [uds_version] Does the cohort mix UDS/form versions, and which fields may be structurally missing by version?
- [baseline_dementia_free] Should baseline dementia-free status use NACCUDSD, CDRGLOB, DEMENTED, or a composite rule?
- [outcome_definition] Should cognitive decline be defined by MMSE decline, MoCA decline, NACCUDSD conversion, CDR worsening, or a composite endpoint?
- [outcome_window] When does the outcome window start after time zero, and does it end at a visit number, calendar time, or fixed follow-up horizon?
- [scale_harmonization] How should MMSE/MoCA, UDS version, language, or center differences be handled?
- [death_dropout] Should death/dropout be treated as censoring, a competing event, or a missing-outcome mechanism?

## Approval gate

Do not run cohort construction until these questions are resolved and a human approves the design packet.
