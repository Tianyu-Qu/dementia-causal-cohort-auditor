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

## v0.5 Acceptance Layer

- Generate executable cohort tests.
- Produce an `acceptance_report.md`.
- Check temporal validity, attrition explanations, and missingness rules.

## v0.6 Synthetic Demo

- Add synthetic dementia cohort data.
- Include known design traps for demos and tests.
- Make the repo runnable without restricted patient data.

## v1.0 Public Release

- Stabilize skill behavior, examples, tests, and documentation.
- Include CI.
- Document limitations and safety boundaries.
