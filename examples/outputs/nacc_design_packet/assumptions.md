# Design Packet Assumptions

- Task type is currently routed as `prediction_cognitive_decline`.
- The packet is a draft for human approval, not an executable cohort specification.
- The core NACC clinical/UDS table has not been selected inside this packet unless provided elsewhere.
- Local NACC dictionary binding is required before confirming any mapping.
- Time zero, baseline window, outcome definition, follow-up window, missingness handling, and version harmonization remain unresolved unless explicitly answered by the user.
- Minimum follow-up requirements may introduce selection bias if treated as baseline eligibility without justification.
- APOE availability may introduce selection bias and must be reported in attrition if required.
- No patient-level data should be output before explicit cohort-construction approval.

## Source questions carried into this packet

- `time_zero`: Is time zero/index visit the first visit, the first eligible visit, or a specific measurement/event date?
- `baseline_window`: What visits or time range belong to the baseline window, and which variables must be measured before time zero?
- `minimum_followup`: Is the minimum follow-up requirement an eligibility criterion or an outcome-ascertainment requirement?
- `missingness`: For APOE, cognitive scales, and diagnostic status, should missing values cause exclusion, be encoded as missing, or be handled through sensitivity analyses?
- `uds_version`: Does the cohort mix UDS/form versions, and which fields may be structurally missing by version?
- `baseline_dementia_free`: Should baseline dementia-free status use NACCUDSD, CDRGLOB, DEMENTED, or a composite rule?
- `outcome_definition`: Should cognitive decline be defined by MMSE decline, MoCA decline, NACCUDSD conversion, CDR worsening, or a composite endpoint?
- `outcome_window`: When does the outcome window start after time zero, and does it end at a visit number, calendar time, or fixed follow-up horizon?
- `scale_harmonization`: How should MMSE/MoCA, UDS version, language, or center differences be handled?
- `death_dropout`: Should death/dropout be treated as censoring, a competing event, or a missing-outcome mechanism?
