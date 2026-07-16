# NACC Beginner Glossary

| Term | Practical meaning |
| --- | --- |
| NACCID | Participant identifier. Treat as protected row-level information; reports should summarize it, not list values. |
| NACCADC | ADRC/center identifier. Useful for center effects, harmonization checks, and clustered validation. |
| NACCVNUM | Visit number/order. Useful for longitudinal ordering, but still verify date fields when time windows matter. |
| VISITMO/VISITDAY/VISITYR | Visit date components. Needed for baseline, index date, follow-up windows, and lag checks. |
| NACCAGE | Age at visit. Often the safest age anchor for visit-level cohort definitions. |
| SEX | Sex variable. Verify coding in the local dictionary before modeling. |
| EDUC | Years of education or education code. Common confounder/prognostic feature. |
| NACCNE4S | APOE e4 count/status candidate. Availability may be selective; do not silently restrict without attrition reporting. |
| NACCUDSD | Cognitive status / UDS diagnosis candidate. Confirm coding before defining dementia-free baseline. |
| CDRGLOB | Global Clinical Dementia Rating. Useful baseline severity/outcome feature. |
| CDRSUM | CDR sum of boxes. Useful severity/outcome feature. |
| NACCMMSE | MMSE-like cognitive score candidate. Check UDS version, language, missing codes, and comparability. |
| UDSVER/NACCUDSV | UDS version indicator. Important because structural missingness and form content change across versions. |
| Medication records | NACC may contain medication/treatment records, but these are not automatically causal exposure definitions. |
