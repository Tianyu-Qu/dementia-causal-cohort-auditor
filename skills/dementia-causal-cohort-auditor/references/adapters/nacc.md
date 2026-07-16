# NACC Adapter

Use this reference only when NACC is named. This v0.3 adapter is data-dictionary-driven: it can suggest candidate mappings for dementia causal cohort concepts, but it must not treat any variable mapping as final until checked against the user's local NACC release, modules, and data dictionary.

Official orientation: NACC describes the UDS as longitudinal data collected since 2005 during standardized annual ADRC evaluations, with participants ranging from cognitively normal to MCI to demented. NACC also states that the Researcher's Data Dictionary is the primary resource for analyzing NACC clinical and demographic data, and that the compact Data Element Dictionary lists variables with data type, allowable codes, and skip-pattern information.

## Mapping Principles

- Do not assume variable names without checking the user's NACC data dictionary or data release documentation.
- Separate visit-level variables from participant-level variables.
- Treat UDS version, form version, packet type, module availability, and data release date as part of the mapping context.
- Treat first visit, first eligible visit, and treatment/index date as different possible anchors.
- Flag variables that may be measured after the index date.
- Preserve NACC-specific missing value codes and document recoding.
- Treat NACC-derived variables, often prefixed with `NACC`, as convenient but not automatically preferable; confirm derivation rules and timing.
- Treat structural missingness caused by UDS version differences as different from ordinary item missingness.

## Required Input Before Final Mapping

- NACC release or extract date.
- UDS version(s) and packet types represented in the data.
- File list or table list.
- Data dictionary or at least CSV headers.
- Missing-value code rules.
- Whether medication, diagnosis, neuropsychological, genetic, neuropathology, biomarker, or imaging modules are available.

## Core Dementia Causal Cohort Concepts

Map these first for v0.3:

| Concept ID | Meaning | Grain | Common candidate names to check | Required? |
| --- | --- | --- | --- | --- |
| participant_id | Participant identifier | participant | `NACCID` | yes |
| center_id | ADRC/center identifier | participant or visit | `NACCADC` | no |
| visit_id | Visit number/order | visit | `NACCVNUM`, visit number fields | yes |
| visit_date | Visit month/day/year or date proxy | visit | `VISITMO`, `VISITDAY`, `VISITYR` | yes |
| age_at_visit | Age at visit | visit | `NACCAGE`, age fields | yes |
| sex | Sex | participant | `SEX` | yes |
| education | Years of education | participant | `EDUC` | recommended |
| race_ethnicity | Race/ethnicity | participant | race and Hispanic ethnicity fields | recommended |
| apoe | APOE genotype or e4 count/status | participant | `NACCNE4S`, APOE fields | yes for APOE-restricted cohorts |
| cognitive_status | Normal/MCI/dementia status | visit | `NACCUDSD`, syndrome or cognitive status fields | yes |
| dementia_status | Dementia indicator/diagnosis | visit | `NACCUDSD`, dementia diagnosis fields | yes |
| mci_status | MCI indicator/diagnosis | visit | `NACCUDSD`, MCI fields | recommended |
| cdr_global | Global CDR | visit | `CDRGLOB` | recommended |
| cdr_sum | CDR sum of boxes | visit | `CDRSUM` | recommended |
| cognitive_score | Cognitive test score | visit | `NACCMMSE`, MoCA or neuropsychological score fields | yes if outcome is cognitive decline |
| medication_exposure | Medication or ADRD-specific treatment exposure | visit | medication module fields, A4/A4a fields | yes for treatment studies |
| death_status | Death indicator/date | participant or follow-up | death fields | recommended |
| dropout_ltfu | Dropout/loss to follow-up proxy | visit/process | follow-up availability, visit gaps, status fields | recommended |

Candidate names are hints, not final mappings. Always check the supplied dictionary.

## Mapping Status Values

- `confirmed`: supported by the user's data dictionary and study design.
- `candidate`: plausible candidate requiring human confirmation.
- `unresolved`: no reliable candidate yet.
- `not_available`: concept is not available in the provided data.

## Required NACC Questions Before Execution

- Which NACC data release and modules are available?
- What variable dictionary accompanies the data?
- Is time represented as visit date, visit number, age, months from baseline, or another field?
- Which variable defines dementia-free baseline?
- Is APOE measured for everyone or a selected subset?
- Are medication variables visit-level, historical, current-use, or ever-use?
- Are medication variables granular enough to support new-user, active-comparator, washout, grace-period, and lag-period definitions?
- Does the cohort combine UDS versions, and if so which variables are structurally unavailable in some periods?
- Are cognitive outcome variables comparable across UDS versions, language, center, and test battery changes?
- Is two-follow-up availability an eligibility rule or outcome-ascertainment rule?

## v0.3 Output

When NACC mapping is requested, produce `nacc_variable_mapping.yaml` with:

- mapping metadata
- source files/dictionaries reviewed
- concept mappings with status and evidence
- unresolved items
- temporal warnings
- missingness warnings
- readiness for cohort spec integration

Use `scripts/suggest_nacc_mapping.py` to draft a candidate mapping from a CSV data dictionary or header list. Use `scripts/validate_nacc_mapping.py` to check that required v0.3 concept mappings are represented.
