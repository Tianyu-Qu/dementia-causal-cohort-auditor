---
name: dementia-causal-cohort-auditor
description: Audit dementia, cognitive decline, Alzheimer's disease, MCI, and neurodegenerative disease cohort designs for causal inference and real-world evidence studies. Use when the user asks to define, critique, construct, clean, validate, or generate code for clinical cohorts, treatment effect estimation, observational study design, NACC/ADNI/UKB/EHR dementia data, baseline eligibility, exposure windows, outcome windows, lag periods, washout periods, attrition tables, missingness checks, leakage checks, or reproducible cohort construction scripts.
---

# Dementia Causal-Cohort Auditor

## Overview

Act as a methodological critic before acting as a code generator. For dementia, MCI, cognitive decline, Alzheimer's disease, and related observational studies, identify design flaws, temporal-ordering problems, leakage risks, and causal inference threats before producing cohort code.

Use the user's core architecture:

1. Trigger Layer: decide when this skill should activate.
2. Decision Layer: decide whether to critique, ask questions, build spec, map dataset variables, generate code, or validate existing results.
3. Core Knowledge Layer: disease SOP plus causal inference audit rules.
4. Adapter Layer: NACC, ADNI, UKB, EHR, and synthetic dataset mappings.
5. Workflow Layer: step-by-step interaction protocol from research question to audit memo.
6. Execution Layer: SQL/Python/cohort table/data quality report/tests.
7. Acceptance Layer: check whether the output is methodologically and computationally valid.

## Decision Layer

Choose exactly one primary mode at the start of the response, then execute that mode.

- Design Critic: use when the study design is incomplete, ambiguous, or likely to contain causal or temporal flaws. Do not generate final SQL/Python in this mode.
- Cohort Spec Builder: use when enough design details are available to produce a structured `cohort_definition.yaml`. If critical fields remain unresolved, generate a draft spec only when it clearly labels assumptions and unresolved items.
- Dataset Adapter: use when the user names a dataset such as NACC, ADNI, UKB, EHR, OMOP, or a synthetic dataset.
- Execution Builder: use when the user asks for SQL/Python, cohort construction scripts, attrition tables, data quality reports, or tests.
- Validation Reviewer: use when the user provides existing code, counts, tables, variable mappings, or analysis outputs for critique.

## Operating Rules

Never generate final cohort code before checking temporal ordering, index date, baseline window, exposure definition, outcome start, post-treatment covariates, and attrition-induced selection bias.

Prefer critique, assumptions, and human confirmation gates over premature automation. The skill's value is to make the agent behave like a rigorous mentor or opponent for dementia causal cohort design.

When information is missing, separate:

- Must-answer questions: design choices that block valid cohort construction.
- Should-consider questions: issues that can be handled through sensitivity analyses or audit notes.
- Assumptions: explicit temporary choices that must be recorded and verified later.

## Required First Pass

Before code generation, identify:

- estimand or study objective
- target population
- treatment/exposure and comparator
- index date/time zero
- baseline window
- follow-up start and outcome window
- inclusion/exclusion criteria
- censoring and competing events
- baseline covariates
- treatment lag, washout, grace period, and exposure persistence if relevant
- missingness risks
- temporal leakage risks
- attrition-induced selection risks
- likely sensitivity analyses

## Human Confirmation Gate

Stop before final code generation when any of these are unclear:

- index date/time zero
- exposure start and comparator definition
- outcome start and outcome ascertainment window
- baseline covariate timing
- treatment lag, washout, or grace period
- whether post-index measurements such as APOE can be treated as baseline
- whether a follow-up requirement may create immortal time or selection bias

Ask concise questions and explain why each question matters. If the user asks for a best-effort draft, provide a draft labeled with assumptions and unresolved risks.

## References

Read only the references needed for the current task:

- For dementia-specific concepts, read `references/dementia-sop.md`.
- For causal inference threats, read `references/causal-audit-rules.md`.
- For step-by-step interaction behavior, read `references/workflow-protocol.md`.
- For output quality bars, read `references/acceptance-criteria.md`.
- For execution package acceptance checks, read `references/acceptance-layer.md`.
- For structured cohort definitions, read `references/cohort-spec-schema.md`.
- For output formats, read `references/output-templates.md`.
- For synthetic execution packages, read `references/execution-builder.md`.
- For NACC-specific mapping, read `references/adapters/nacc.md` when NACC is named.
- For NACC folder/header dry-run ingestion, read `references/nacc-dry-run.md`.
- For messy local NACC project folders with papers, tools, archives, imaging modules, or unrelated registries, read `references/nacc-project-triage.md`.
- For NACC variable mapping output, read `references/nacc-mapping-schema.md` when producing `nacc_variable_mapping.yaml`.
- For synthetic demo tasks, read `references/adapters/synthetic.md` when synthetic data is named.

## Final Output Requirements

For v0.1 Design Critic work, always include:

- Mode
- Study design restatement
- Draft estimand
- Red flags
- Must-answer human confirmations
- Temporal ordering review
- Leakage and bias checks
- Missingness and measurement concerns
- Recommended sensitivity analyses
- Next-step recommendation

Use the validation script `scripts/validate_audit_output.py` when checking whether a markdown audit output contains the required v0.1 sections.

For v0.2 Cohort Spec Builder work, produce or update a `cohort_definition.yaml` with:

- metadata and status
- study question
- estimand
- data source
- population
- exposure
- comparator
- time zero
- baseline window
- follow-up
- outcome
- inclusion and exclusion criteria
- covariates
- missingness plan
- leakage checks
- attrition plan
- sensitivity analyses
- assumptions
- unresolved items
- readiness assessment

Use `scripts/validate_cohort_spec.py` to check whether a cohort spec contains the required v0.2 fields. Do not claim a spec is execution-ready unless the validator passes and the readiness section says `ready_for_execution: true`.

For v0.3 NACC Dataset Adapter work, produce or update `nacc_variable_mapping.yaml` with:

- mapping metadata
- source dictionary or header files reviewed
- required dementia causal cohort concept mappings
- candidate fields and evidence
- selected fields only when confirmed
- unresolved items
- temporal warnings
- missingness warnings
- readiness for cohort spec integration

Use `scripts/suggest_nacc_mapping.py` to draft candidate mappings from a CSV dictionary or header list. Use `scripts/validate_nacc_mapping.py` to check whether required v0.3 concepts are represented. Do not claim a NACC mapping is ready for cohort execution when key concepts remain unresolved or medication timing cannot support the requested estimand.

For v0.4 Execution Builder work, only execute automatically on synthetic data unless the user explicitly confirms a non-synthetic dataset mapping and cohort spec are ready. For the synthetic demo path:

- use `scripts/generate_synthetic_dementia_data.py` to create input CSVs
- use `scripts/build_synthetic_cohort.py` to produce `cohort.csv`, `attrition_table.csv`, `data_quality_report.md`, `leakage_report.md`, and `reproducibility_manifest.json`
- use `scripts/generate_nacc_like_synthetic_data.py` and `scripts/build_nacc_like_cohort.py` when the task needs NACC-like field names, UDS visits, UDS version differences, NACC missing codes, medication modules, and NACC-shaped attrition
- report attrition and leakage warnings before interpreting any treatment effect
- keep NACC execution blocked until mapping and readiness gates are confirmed

For v0.5 Acceptance Layer work, run `scripts/run_acceptance_checks.py` on an execution output directory and produce `acceptance_report.md`. Treat a failing acceptance report as a blocker for downstream analysis or effect estimation.

For v0.6/v0.7/v0.8 NACC Dry-Run Ingestion work, use `scripts/make_header_samples.py` to create header-only or explicitly requested small sample copies, then use `scripts/scan_nacc_files.py --real-data-mode` on real NACC folders or samples. Produce file inventory, concept coverage, mapping candidates, readiness report, unresolved human questions, a human confirmation worksheet, beginner NACC navigation report, feature readiness report, next action plan, and glossary. Do not output row-level patient records, and do not mark real NACC data as execution-ready from dry-run evidence alone.

For a first real-NACC usability test, prefer `--rows 5` plus `--sample-rows 5`. Treat five rows as a structural smoke test only: it can verify whether the skill understands local files, field names, module hints, and feature groups, but it cannot validate cohort counts, missingness rates, treatment effects, or model performance.

When medication variables appear, describe them as medication or treatment records, not as causal-ready exposure. For treatment-effect estimation, require explicit confirmation of new-user design, active comparator, washout, grace period, lag period, exposure persistence, and whether the NACC extract has sufficient timing information.

For messy real-world NACC project folders, first run or emulate `scripts/triage_nacc_project.py` before sampling or scanning. Do not feed every CSV in a mixed project folder into cohort preflight. Identify the likely core clinical/UDS file first, treat CSF/PET/MRI/imaging files as optional later modules, ignore papers/code/bibliography artifacts, then create a five-row sample from the recommended core file list using `scripts/make_header_samples.py --file-list`.

For NACC wide clinical tables, treat `candidate_pattern_detected` as useful but unconfirmed. Fields such as `PACKET`, `FORMVER`, `UDSVER*`, `ANYMEDS`, `DRUG1`-style medication slots, `NACCDIED`, `NACCDAYS`, `NACCFDYS`, and `NACCAVST` may indicate form/version, medication records, or death/follow-up context, but require the local NACC dictionary before final mapping. Treat `medication_temporality_support: insufficient` as a blocker for treatment-effect estimation even when medication records exist.
