#!/usr/bin/env python
"""Generate a small synthetic dementia treatment cohort dataset."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


PATIENTS = [
    {"participant_id": "S001", "sex": "F", "education_years": "16", "apoe_e4_count": "1"},
    {"participant_id": "S002", "sex": "M", "education_years": "12", "apoe_e4_count": "0"},
    {"participant_id": "S003", "sex": "F", "education_years": "18", "apoe_e4_count": ""},
    {"participant_id": "S004", "sex": "M", "education_years": "14", "apoe_e4_count": "2"},
    {"participant_id": "S005", "sex": "F", "education_years": "10", "apoe_e4_count": "1"},
    {"participant_id": "S006", "sex": "M", "education_years": "16", "apoe_e4_count": "0"},
    {"participant_id": "S007", "sex": "F", "education_years": "15", "apoe_e4_count": "1"},
    {"participant_id": "S008", "sex": "M", "education_years": "13", "apoe_e4_count": "0"},
]

VISITS = [
    {"participant_id": "S001", "visit_id": "1", "visit_date": "2020-01-10", "age": "70", "cognitive_status": "normal", "mmse": "29"},
    {"participant_id": "S001", "visit_id": "2", "visit_date": "2021-01-11", "age": "71", "cognitive_status": "normal", "mmse": "28"},
    {"participant_id": "S002", "visit_id": "1", "visit_date": "2020-02-01", "age": "68", "cognitive_status": "mci", "mmse": "27"},
    {"participant_id": "S002", "visit_id": "2", "visit_date": "2021-02-01", "age": "69", "cognitive_status": "mci", "mmse": "26"},
    {"participant_id": "S003", "visit_id": "1", "visit_date": "2020-03-05", "age": "72", "cognitive_status": "normal", "mmse": "30"},
    {"participant_id": "S003", "visit_id": "2", "visit_date": "2021-03-05", "age": "73", "cognitive_status": "normal", "mmse": "29"},
    {"participant_id": "S004", "visit_id": "1", "visit_date": "2020-04-15", "age": "80", "cognitive_status": "dementia", "mmse": "20"},
    {"participant_id": "S004", "visit_id": "2", "visit_date": "2021-04-15", "age": "81", "cognitive_status": "dementia", "mmse": "18"},
    {"participant_id": "S005", "visit_id": "1", "visit_date": "2020-05-20", "age": "63", "cognitive_status": "normal", "mmse": "29"},
    {"participant_id": "S005", "visit_id": "2", "visit_date": "2021-05-20", "age": "64", "cognitive_status": "normal", "mmse": "28"},
    {"participant_id": "S006", "visit_id": "1", "visit_date": "2020-06-01", "age": "75", "cognitive_status": "normal", "mmse": "28"},
    {"participant_id": "S007", "visit_id": "1", "visit_date": "2020-07-01", "age": "74", "cognitive_status": "normal", "mmse": "29"},
    {"participant_id": "S007", "visit_id": "1", "visit_date": "2020-07-01", "age": "74", "cognitive_status": "normal", "mmse": "29"},
    {"participant_id": "S007", "visit_id": "2", "visit_date": "2021-07-01", "age": "75", "cognitive_status": "mci", "mmse": "25"},
    {"participant_id": "S008", "visit_id": "1", "visit_date": "2020-08-01", "age": "69", "cognitive_status": "normal", "mmse": "29"},
    {"participant_id": "S008", "visit_id": "2", "visit_date": "2021-08-01", "age": "70", "cognitive_status": "normal", "mmse": ""},
]

MEDICATIONS = [
    {"participant_id": "S001", "drug": "DrugA", "start_date": "2020-01-15"},
    {"participant_id": "S002", "drug": "DrugB", "start_date": "2020-02-10"},
    {"participant_id": "S003", "drug": "DrugA", "start_date": "2020-03-10"},
    {"participant_id": "S004", "drug": "DrugB", "start_date": "2020-04-20"},
    {"participant_id": "S005", "drug": "DrugA", "start_date": "2020-05-22"},
    {"participant_id": "S006", "drug": "DrugB", "start_date": "2020-06-10"},
    {"participant_id": "S007", "drug": "DrugA", "start_date": "2020-07-10"},
    {"participant_id": "S008", "drug": "DrugB", "start_date": "2020-08-10"},
]

OUTCOMES = [
    {"participant_id": "S001", "outcome": "cognitive_decline", "outcome_date": "2021-01-11"},
    {"participant_id": "S002", "outcome": "cognitive_decline", "outcome_date": "2021-02-01"},
    {"participant_id": "S007", "outcome": "cognitive_decline", "outcome_date": "2021-07-01"},
]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("examples/inputs/synthetic"))
    args = parser.parse_args()

    write_csv(args.output_dir / "patients.csv", PATIENTS)
    write_csv(args.output_dir / "visits.csv", VISITS)
    write_csv(args.output_dir / "medications.csv", MEDICATIONS)
    write_csv(args.output_dir / "outcomes.csv", OUTCOMES)
    print(f"Wrote synthetic dementia data to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
