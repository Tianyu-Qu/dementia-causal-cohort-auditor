# Human Approval Checklist

Task type: `prediction_cognitive_decline`

Approve every item before cohort construction.

## Design decisions

- [ ] `time_zero` resolved: Is time zero/index visit the first visit, the first eligible visit, or a specific measurement/event date?
- [ ] `baseline_window` resolved: What visits or time range belong to the baseline window, and which variables must be measured before time zero?
- [ ] `minimum_followup` resolved: Is the minimum follow-up requirement an eligibility criterion or an outcome-ascertainment requirement?
- [ ] `missingness` resolved: For APOE, cognitive scales, and diagnostic status, should missing values cause exclusion, be encoded as missing, or be handled through sensitivity analyses?
- [ ] `uds_version` resolved: Does the cohort mix UDS/form versions, and which fields may be structurally missing by version?
- [ ] `baseline_dementia_free` resolved: Should baseline dementia-free status use NACCUDSD, CDRGLOB, DEMENTED, or a composite rule?
- [ ] `outcome_definition` resolved: Should cognitive decline be defined by MMSE decline, MoCA decline, NACCUDSD conversion, CDR worsening, or a composite endpoint?
- [ ] `outcome_window` resolved: When does the outcome window start after time zero, and does it end at a visit number, calendar time, or fixed follow-up horizon?
- [ ] `scale_harmonization` resolved: How should MMSE/MoCA, UDS version, language, or center differences be handled?
- [ ] `death_dropout` resolved: Should death/dropout be treated as censoring, a competing event, or a missing-outcome mechanism?

## Mapping and data gates

- [ ] Core NACC clinical/UDS table selected.
- [ ] Local NACC data dictionary reviewed.
- [ ] Required field mappings confirmed and selected.
- [ ] Missing codes and structural missingness rules documented.
- [ ] UDS/form version compatibility reviewed.
- [ ] Aggregate validation planned before patient-level cohort output.

## Execution gate

- [ ] I approve this design packet for the next stage.
- [ ] I understand this approval is not final approval of the constructed cohort output.
