# Feature and Task Readiness Report

| Task | Required concept coverage | Recommended concept gaps | Interpretation |
| --- | --- | --- | --- |
| Dementia or cognitive-status classification | surface-ready; needs human confirmation | none | Best first real-data task because it mainly needs UDS visit records and diagnosis/status variables. |
| Cognitive decline prediction | surface-ready; needs human confirmation | none | Needs longitudinal ordering and follow-up outcomes; two visits in a five-row sample prove structure, not adequacy. |
| Longitudinal trajectory modeling | surface-ready; needs human confirmation | none | Treat visit spacing, UDS version changes, and informative dropout as first-class design issues. |
| Representation learning / feature pretraining | surface-ready; needs human confirmation | none | Medication data is optional unless the representation is intended to support treatment-effect questions. |
| Treatment effect estimation | surface-ready; needs human confirmation | none | NACC medication records are not automatically treatment exposure; new-user, comparator, washout, lag, and grace windows need human confirmation. |
| Survival / progression analysis | surface-ready; needs human confirmation | none | Clarify whether death/dropout is a competing event, censoring process, or missing outcome mechanism. |

## How to read this

- `surface-ready` means headers/sample values contain plausible candidates. It does not mean the cohort is methodologically valid.
- Treatment-effect estimation has a higher bar than prediction or representation learning because medication records must be converted into a valid exposure design.
