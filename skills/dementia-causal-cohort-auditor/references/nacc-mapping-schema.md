# NACC Mapping Schema

Use this reference for v0.3 Dataset Adapter mode when producing `nacc_variable_mapping.yaml`.

## Required Top-Level Fields

- `schema_version`
- `adapter`
- `mapping_metadata`
- `source_dictionary`
- `core_concepts`
- `unresolved_items`
- `temporal_warnings`
- `missingness_warnings`
- `readiness`

## Concept Mapping Format

```yaml
core_concepts:
  - concept_id: participant_id
    label: Participant identifier
    required: true
    status: candidate
    grain: participant
    candidate_fields:
      - field: NACCID
        evidence: exact name match in supplied dictionary
    selected_field: unresolved
    timing_rule: time invariant identifier
    notes: Confirm uniqueness across files.
```

## Required v0.3 Concepts

- `participant_id`
- `visit_id`
- `visit_date`
- `age_at_visit`
- `sex`
- `apoe`
- `cognitive_status`
- `dementia_status`
- `cognitive_score`
- `medication_records`

The validator requires these concept IDs to appear, but it does not require them to be confirmed. For backward compatibility, older mappings with `medication_exposure` are still accepted as aliases, but new mappings should use `medication_records` and optionally `medication_temporality_support`.

## Readiness Logic

Set `readiness.ready_for_cohort_spec: false` when:

- any required concept is `unresolved` or `not_available`
- time ordering cannot be reconstructed
- medication records or temporality fields are insufficient for the proposed treatment-effect design
- missing-value codes have not been reviewed
- UDS version differences may change variable availability

## Human Confirmation Rule

Do not promote a candidate field to `selected_field` unless the user's dictionary, file structure, and study design support it.
