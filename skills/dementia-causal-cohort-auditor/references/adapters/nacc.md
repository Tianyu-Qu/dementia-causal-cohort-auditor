# NACC Adapter Draft

Use this reference only when NACC is named. This v0.1 adapter is intentionally conservative and should prompt for a local data dictionary before final mapping.

## Mapping Principles

- Do not assume variable names without checking the user's NACC data dictionary or data release documentation.
- Separate visit-level variables from participant-level variables.
- Treat first visit, first eligible visit, and treatment/index date as different possible anchors.
- Flag variables that may be measured after the index date.
- Preserve NACC-specific missing value codes and document recoding.

## Concepts to Map

- participant identifier
- visit identifier or visit date/order
- age at visit
- sex
- education
- APOE genotype or e4 carrier status
- cognitive status
- dementia diagnosis
- MCI diagnosis
- cognitive test scores
- medication or exposure proxy
- death/dropout/loss-to-follow-up

## Required NACC Questions

- Which NACC data release and modules are available?
- What variable dictionary accompanies the data?
- Is time represented as visit date, visit number, age, months from baseline, or another field?
- Which variable defines dementia-free baseline?
- Is APOE measured for everyone or a selected subset?
- Are medication variables visit-level, historical, current-use, or ever-use?
