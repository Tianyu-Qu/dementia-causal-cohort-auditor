# Roadmap

## v0.1 Design Critic MVP

- Create the Codex skill.
- Encode the seven-layer architecture.
- Support dementia cohort design critique.
- Produce red flags, human confirmation questions, temporal ordering review, leakage checks, and sensitivity analysis suggestions.
- Add a validator for required audit sections.

## v0.2 Structured Cohort Spec

- Generate `cohort_definition.yaml`.
- Validate required cohort spec fields.
- Record assumptions and unresolved design decisions.
- Keep execution blocked until readiness criteria pass.

## v0.3 NACC Adapter

- Add a stronger NACC concept mapping reference.
- Map common dementia, cognition, visit, APOE, and medication concepts.
- Require local data dictionary confirmation before final mapping.
- Generate candidate `nacc_variable_mapping.yaml` files from dictionary/header inputs.
- Validate that required NACC mapping concepts are represented.

## v0.4 Execution Builder

- Generate SQL/Python cohort construction code from a confirmed spec.
- Generate attrition table logic.
- Generate data quality and leakage checks.
- Provide a runnable synthetic execution path before real NACC execution.
- Add a NACC-like synthetic execution path with NACC-style fields and attrition.

## v0.5 Acceptance Layer

- Generate executable cohort tests.
- Produce an `acceptance_report.md`.
- Check temporal validity, attrition explanations, and missingness rules.
- Treat failed acceptance checks as blockers for downstream effect estimation.

## v0.6 NACC Dry-Run Ingestion

- Scan CSV/TSV folders or header-only samples.
- Produce file inventory, concept coverage, mapping candidates, readiness, and unresolved questions.
- Avoid row-level patient outputs.
- Keep real NACC execution gated behind human confirmation.

## v0.7 Real NACC Preflight

- Create header-only or explicitly requested small sample folders.
- Add real-data dry-run mode.
- Produce phased readiness and a human confirmation worksheet.
- Prepare for the first real NACC processing experiment without enabling execution.

## v0.8 Beginner-Friendly Real-NACC Smoke Test

- Support explicitly requested five-row sample scans.
- Produce beginner NACC navigation, feature readiness, next action, and glossary reports.
- Translate concept coverage into task-specific readiness for ML users who do not know NACC well.
- Distinguish medication/treatment records from causal-ready exposure variables.
- Keep real NACC execution blocked until aggregate evidence and human design gates are complete.

## v0.9 Messy Project Triage

- Add metadata/header-only triage for mixed local folders.
- Identify likely core clinical/UDS tables before sampling.
- Classify CSF, PET, MRI, imaging, archives, and irrelevant project artifacts.
- Allow five-row samples from a recommended file list.
- Encode a flexible agent navigation protocol instead of assuming all useful behavior must be scripted.

## v0.10 NACC Wide-Table Concept Detection

- Detect NACC wide-table field patterns for form/version, medication records, and death/follow-up context.
- Distinguish exact dictionary candidates from pattern candidates.
- Mark pattern candidates as requiring local dictionary confirmation.
- Keep medication records separate from medication temporality needed for causal exposure construction.

## v0.11 NACC Task-Intent Router

- Route natural-language NACC cohort ideas into task families.
- Support prediction, classification, trajectory, survival/progression, biomarker-linked, causal, and representation-learning tasks.
- Generate `task_profile.yaml` and `task_questions.md`.
- Keep design approval and cohort construction blocked until human questions are resolved.

## v0.12 NACC Design Approval Packet

- Convert task intent outputs into a formal design packet.
- Generate `cohort_definition_draft.yaml`, `mapping_draft.yaml`, `assumptions.md`, and `human_approval_checklist.md`.
- Keep mappings unresolved and execution blocked.
- Require human approval before aggregate validation, code planning, or cohort construction.

## v0.13 NACC Aggregate Validation

- Run aggregate-only checks on selected NACC core clinical/UDS data.
- Summarize field coverage, visit structure, missingness, APOE support, cognitive outcome support, form/version context, and follow-up/death context.
- Suppress NACCID values and never output patient rows or a constructed cohort.
- Keep cohort construction blocked until human design approval and mapping/missing-code gates are complete.

## v0.14 Design-to-Code Planner

- Convert an approved or review-ready NACC design packet into a build plan.
- Generate pseudocode, implementation checklist, and validation test plan.
- Do not read patient-level rows.
- Do not output cohort files.
- Keep executable cohort construction blocked until v0.15 approval conditions are met.

## v0.15 First Executable Cohort Construction

- Implement one executable task family first: NACC prediction / cognitive decline.
- Produce cohort index, feature table, outcome table, combined cohort, attrition, data-quality, leakage, reproducibility, and acceptance reports.
- Validate output through the acceptance layer.
- Keep real NACC patient-level execution gated behind explicit approval and confirmed design/mapping.

## v0.15.1 Real NACC Guarded Execution Pilot

- Run the prediction/cognitive-decline builder on one real NACC core file after explicit approval.
- Support only `investigator_ftldlbd_nacc70.csv`.
- Produce real patient-level outputs only in a local private directory that must not be committed.
- Summarize only aggregate counts and acceptance status in chat.
- Refuse execution and write a blocker report when authorization, required fields, or approved pilot rules are missing.

## v0.16 Generalize Execution Templates

- Add execution templates for classification/phenotyping, survival/progression, and biomarker-linked cohorts.
- Generate task-specific pseudocode, required concept specs, implementation checklists, and validation test plans.
- Do not read patient-level data or output cohort files.
- Keep generated test-output directories out of GitHub unless explicitly curated.

## v1.0 Public Release

- Stabilize skill behavior, examples, tests, and documentation.
- Include CI.
- Document limitations and safety boundaries.
