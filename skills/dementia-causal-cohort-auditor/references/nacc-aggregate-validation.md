# NACC Aggregate Validation

Use this reference after v0.12 design approval packet creation and before design-to-code planning or cohort construction.

## Purpose

Run aggregate-only checks on selected NACC clinical/UDS data to determine whether the proposed design appears computable and where it remains blocked.

This stage may read real NACC rows when the user explicitly asks for aggregate validation, but it must not output patient-level rows, NACCID values, or a cohort table.

## Workflow

1. Confirm a likely core clinical/UDS table from v0.9 triage or provide `--core-file`.
2. Confirm the current design packet directory from v0.12 if available.
3. Run:

   ```powershell
   python skills/dementia-causal-cohort-auditor/scripts/run_nacc_aggregate_validation.py --input-dir <SELECTED_NACC_DIR> --core-file <CORE_CLINICAL_UDS_CSV> --output-dir <AGGREGATE_OUTPUT_DIR> --design-packet-dir <DESIGN_PACKET_DIR> --real-data-mode
   ```

4. Review:

   - `aggregate_validation_report.md`
   - `field_distribution_summary.csv`
   - `missingness_by_form_version.csv`
   - `visit_structure_report.md`
   - `privacy_check_report.md`
   - `aggregate_validation_manifest.json`

5. Stop before cohort construction.

## What to Check

- Required concept availability: participant ID, visit order/date, age, APOE, baseline cognitive status, cognitive scores, follow-up context, and form/version context.
- Visit structure: participants with at least two visits, duplicate participant-visit pairs, and visit count distribution.
- Baseline support: age >=65, APOE availability, and cognitive-status availability at the earliest observed visit.
- Outcome support: MMSE/MoCA/CDR/diagnosis fields with enough non-missing aggregate evidence for the proposed task.
- Structural missingness: missingness stratified by `PACKET`, `FORMVER`, `UDSVER*`, or related form/version fields when available.
- Follow-up/death context: candidate fields such as `NACCDIED`, `NACCDAYS`, `NACCFDYS`, `NACCAVST`, or `DROPACT`.

## Required Privacy Boundary

Reports must not include:

- NACCID values
- row-level patient examples
- full raw records
- constructed cohort rows

Identifier fields may be summarized only as counts or suppressed distribution rows.

## Required Gate

Aggregate validation can support design refinement and human approval, but it does not authorize cohort construction.

Keep:

```yaml
ready_for_cohort_construction: false
```

until the user approves the design, field mappings, missing-code rules, time zero, baseline window, outcome window, and leakage checks.
