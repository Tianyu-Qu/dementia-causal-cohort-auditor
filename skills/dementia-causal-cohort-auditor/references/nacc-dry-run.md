# NACC Dry-Run Ingestion

Use this reference for v0.6-v0.8 NACC dictionary/header/sample ingestion.

## Purpose

Perform a read-only preflight scan of a NACC-like folder before cohort construction. The scan should summarize file structure, headers, row counts, small-sample aggregate summaries, key concept coverage, missing concepts, unresolved human questions, beginner-friendly interpretation, feature readiness, and next actions. It must not output row-level participant records.

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
- `human_confirmation_worksheet.md`
- `nacc_beginner_report.md`
- `feature_readiness_report.md`
- `next_action_plan.md`
- `nacc_glossary.md`

## Safety Mode

Use `scripts/make_header_samples.py` before scanning real NACC folders. It defaults to header-only copies (`--rows 0`). For the first practical real-NACC skill test, `--rows 5` is acceptable when the user explicitly wants to validate local structure from a tiny sample.

Use `scripts/scan_nacc_files.py --real-data-mode` for real NACC folders or samples. In real-data mode, readiness for execution must remain `no`.

Recommended first real-data smoke test:

```powershell
python skills/dementia-causal-cohort-auditor/scripts/make_header_samples.py --input-dir <REAL_NACC_DIR> --output-dir <SAFE_SAMPLE_DIR> --rows 5
python skills/dementia-causal-cohort-auditor/scripts/scan_nacc_files.py --input-dir <SAFE_SAMPLE_DIR> --output-dir <DRY_RUN_OUTPUT_DIR> --sample-rows 5 --real-data-mode
```

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
- medication records: medication, drug, or ADRD treatment fields; not automatically treatment exposure
- medication temporality support: start/stop/current-use fields needed to construct exposure windows
- follow-up status: death, dropout, or last contact fields
- UDS version: `UDSVER` or related version fields

## Readiness

Set readiness to `not_ready` when required concepts are missing or when visit time cannot be reconstructed. Set `needs_human_confirmation` when all required surface concepts are present but diagnosis meaning, missing-code rules, UDS version compatibility, or medication exposure constructability still need review.

Do not mark real NACC data as execution-ready from a dry run alone.

## Beginner-Friendly Interpretation

When reporting to a user who knows ML/DL but not NACC, translate detected fields into task readiness:

- Dementia classification can often start once participant, visit, demographic, and cognitive-status concepts are mapped.
- Cognitive decline prediction needs longitudinal order and follow-up outcomes.
- Trajectory modeling needs visit spacing, UDS version checks, and dropout awareness.
- Representation learning can treat medication as optional unless treatment-effect claims are intended.
- Treatment-effect estimation requires medication records plus explicit exposure construction rules; records alone are insufficient.
