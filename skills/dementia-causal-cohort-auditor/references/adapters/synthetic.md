# Synthetic Adapter Draft

Use this reference for examples and public demos that avoid real patient data.

## Expected Synthetic Tables

- `patients`: participant-level demographics and genotype fields.
- `visits`: visit-level age, cognition, diagnosis, and dates.
- `medications`: exposure starts, stops, dose, and class.
- `outcomes`: outcome dates and labels.

## v0.4 Synthetic CSV Schema

`patients.csv`:

- `participant_id`
- `sex`
- `education_years`
- `apoe_e4_count`

`visits.csv`:

- `participant_id`
- `visit_id`
- `visit_date`
- `age`
- `cognitive_status`
- `mmse`

`medications.csv`:

- `participant_id`
- `drug`
- `start_date`

`outcomes.csv`:

- `participant_id`
- `outcome`
- `outcome_date`

## Demo Data Should Include

- participants under and over age 65
- baseline dementia cases
- incident dementia cases
- missing APOE
- duplicate visits
- inconsistent visit order
- post-index covariate leakage
- early outcomes inside a possible lag window
- loss to follow-up and death indicators

## Synthetic Demo Rule

Synthetic examples must be labeled synthetic and must not resemble or disclose real patient records.

Use `scripts/generate_synthetic_dementia_data.py` to generate v0.4 demo data and `scripts/build_synthetic_cohort.py` to produce cohort execution outputs.

For a closer NACC-shaped demo, use `scripts/generate_nacc_like_synthetic_data.py` and `scripts/build_nacc_like_cohort.py`. Prefer the NACC-like demo when testing adapter logic, attrition structure, UDS version issues, NACC missing codes, and visit-level temporal ordering.
