# Synthetic Adapter Draft

Use this reference for examples and public demos that avoid real patient data.

## Expected Synthetic Tables

- `patients`: participant-level demographics and genotype fields.
- `visits`: visit-level age, cognition, diagnosis, and dates.
- `medications`: exposure starts, stops, dose, and class.
- `outcomes`: outcome dates and labels.

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
