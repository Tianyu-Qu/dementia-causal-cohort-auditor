# NACC Dry-Run Ingestion

Use this reference for v0.6 NACC dictionary/header ingestion.

## Purpose

Perform a read-only preflight scan of a NACC-like folder before cohort construction. The scan should summarize file structure, headers, row counts, key concept coverage, missing required concepts, unresolved human questions, and readiness. It must not output row-level participant records.

## Inputs

- A folder containing CSV or TSV files.
- Files may be real NACC extracts, local data dictionaries, header-only samples, or NACC-like synthetic inputs.

## Outputs

- `nacc_file_inventory.csv`
- `nacc_file_inventory.md`
- `nacc_concept_coverage.yaml`
- `nacc_variable_mapping_candidates.yaml`
- `nacc_readiness_report.md`
- `unresolved_human_questions.md`

## Required Concept Groups

- identifiers: `NACCID`
- center: `NACCADC`
- visit order: `NACCVNUM`
- visit date: `VISITMO`, `VISITDAY`, `VISITYR`
- baseline age: `NACCAGE`
- demographics: `SEX`, `EDUC`
- genetics: `NACCNE4S` or APOE candidates
- diagnosis/cognitive status: `NACCUDSD`
- CDR: `CDRGLOB`, `CDRSUM`
- cognitive score: `NACCMMSE` or another score candidate
- medication/exposure: medication or drug fields
- follow-up status: death, dropout, or last contact fields
- UDS version: `UDSVER` or related version fields

## Readiness

Set readiness to `not_ready` when required concepts are missing or when visit time cannot be reconstructed. Set `needs_human_confirmation` when all required surface concepts are present but medication timing, diagnosis meaning, missing-code rules, or UDS version compatibility still need review.

Do not mark real NACC data as execution-ready from a dry run alone.
