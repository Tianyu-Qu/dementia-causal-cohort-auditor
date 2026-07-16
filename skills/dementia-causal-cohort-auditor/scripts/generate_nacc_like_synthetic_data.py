#!/usr/bin/env python
"""Generate NACC-like synthetic data for execution-layer testing.

The data are public-demo synthetic records. They mimic selected NACC-style
fields and structural issues without representing real participants.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


PARTICIPANTS = [
    {"NACCID": "N001", "NACCADC": "101", "SEX": "2", "EDUC": "16", "NACCNE4S": "1"},
    {"NACCID": "N002", "NACCADC": "101", "SEX": "1", "EDUC": "12", "NACCNE4S": "0"},
    {"NACCID": "N003", "NACCADC": "102", "SEX": "2", "EDUC": "18", "NACCNE4S": "9"},
    {"NACCID": "N004", "NACCADC": "102", "SEX": "1", "EDUC": "14", "NACCNE4S": "2"},
    {"NACCID": "N005", "NACCADC": "103", "SEX": "2", "EDUC": "10", "NACCNE4S": "1"},
    {"NACCID": "N006", "NACCADC": "103", "SEX": "1", "EDUC": "16", "NACCNE4S": "0"},
    {"NACCID": "N007", "NACCADC": "104", "SEX": "2", "EDUC": "15", "NACCNE4S": "1"},
    {"NACCID": "N008", "NACCADC": "104", "SEX": "1", "EDUC": "13", "NACCNE4S": "0"},
    {"NACCID": "N009", "NACCADC": "105", "SEX": "2", "EDUC": "17", "NACCNE4S": "1"},
]

UDS_VISITS = [
    {"NACCID": "N001", "NACCVNUM": "1", "VISITMO": "1", "VISITDAY": "10", "VISITYR": "2020", "NACCAGE": "70", "NACCUDSD": "1", "CDRGLOB": "0", "CDRSUM": "0", "NACCMMSE": "29", "UDSVER": "3"},
    {"NACCID": "N001", "NACCVNUM": "2", "VISITMO": "1", "VISITDAY": "11", "VISITYR": "2021", "NACCAGE": "71", "NACCUDSD": "1", "CDRGLOB": "0", "CDRSUM": "0.5", "NACCMMSE": "28", "UDSVER": "3"},
    {"NACCID": "N002", "NACCVNUM": "1", "VISITMO": "2", "VISITDAY": "1", "VISITYR": "2020", "NACCAGE": "68", "NACCUDSD": "2", "CDRGLOB": "0.5", "CDRSUM": "1.5", "NACCMMSE": "27", "UDSVER": "3"},
    {"NACCID": "N002", "NACCVNUM": "2", "VISITMO": "2", "VISITDAY": "1", "VISITYR": "2021", "NACCAGE": "69", "NACCUDSD": "2", "CDRGLOB": "0.5", "CDRSUM": "2", "NACCMMSE": "26", "UDSVER": "3"},
    {"NACCID": "N003", "NACCVNUM": "1", "VISITMO": "3", "VISITDAY": "5", "VISITYR": "2020", "NACCAGE": "72", "NACCUDSD": "1", "CDRGLOB": "0", "CDRSUM": "0", "NACCMMSE": "30", "UDSVER": "3"},
    {"NACCID": "N003", "NACCVNUM": "2", "VISITMO": "3", "VISITDAY": "5", "VISITYR": "2021", "NACCAGE": "73", "NACCUDSD": "1", "CDRGLOB": "0", "CDRSUM": "0.5", "NACCMMSE": "29", "UDSVER": "3"},
    {"NACCID": "N004", "NACCVNUM": "1", "VISITMO": "4", "VISITDAY": "15", "VISITYR": "2020", "NACCAGE": "80", "NACCUDSD": "4", "CDRGLOB": "1", "CDRSUM": "5", "NACCMMSE": "20", "UDSVER": "3"},
    {"NACCID": "N004", "NACCVNUM": "2", "VISITMO": "4", "VISITDAY": "15", "VISITYR": "2021", "NACCAGE": "81", "NACCUDSD": "4", "CDRGLOB": "2", "CDRSUM": "8", "NACCMMSE": "18", "UDSVER": "3"},
    {"NACCID": "N005", "NACCVNUM": "1", "VISITMO": "5", "VISITDAY": "20", "VISITYR": "2020", "NACCAGE": "63", "NACCUDSD": "1", "CDRGLOB": "0", "CDRSUM": "0", "NACCMMSE": "29", "UDSVER": "3"},
    {"NACCID": "N005", "NACCVNUM": "2", "VISITMO": "5", "VISITDAY": "20", "VISITYR": "2021", "NACCAGE": "64", "NACCUDSD": "1", "CDRGLOB": "0", "CDRSUM": "0", "NACCMMSE": "28", "UDSVER": "3"},
    {"NACCID": "N006", "NACCVNUM": "1", "VISITMO": "6", "VISITDAY": "1", "VISITYR": "2020", "NACCAGE": "75", "NACCUDSD": "1", "CDRGLOB": "0", "CDRSUM": "0", "NACCMMSE": "28", "UDSVER": "3"},
    {"NACCID": "N007", "NACCVNUM": "1", "VISITMO": "7", "VISITDAY": "1", "VISITYR": "2020", "NACCAGE": "74", "NACCUDSD": "1", "CDRGLOB": "0", "CDRSUM": "0", "NACCMMSE": "29", "UDSVER": "3"},
    {"NACCID": "N007", "NACCVNUM": "1", "VISITMO": "7", "VISITDAY": "1", "VISITYR": "2020", "NACCAGE": "74", "NACCUDSD": "1", "CDRGLOB": "0", "CDRSUM": "0", "NACCMMSE": "29", "UDSVER": "3"},
    {"NACCID": "N007", "NACCVNUM": "2", "VISITMO": "7", "VISITDAY": "1", "VISITYR": "2021", "NACCAGE": "75", "NACCUDSD": "2", "CDRGLOB": "0.5", "CDRSUM": "2", "NACCMMSE": "25", "UDSVER": "3"},
    {"NACCID": "N008", "NACCVNUM": "1", "VISITMO": "8", "VISITDAY": "1", "VISITYR": "2020", "NACCAGE": "69", "NACCUDSD": "1", "CDRGLOB": "0", "CDRSUM": "0", "NACCMMSE": "29", "UDSVER": "4"},
    {"NACCID": "N008", "NACCVNUM": "2", "VISITMO": "8", "VISITDAY": "1", "VISITYR": "2021", "NACCAGE": "70", "NACCUDSD": "1", "CDRGLOB": "0", "CDRSUM": "0", "NACCMMSE": "-4", "UDSVER": "4"},
    {"NACCID": "N009", "NACCVNUM": "1", "VISITMO": "9", "VISITDAY": "1", "VISITYR": "2020", "NACCAGE": "77", "NACCUDSD": "-4", "CDRGLOB": "-4", "CDRSUM": "-4", "NACCMMSE": "-4", "UDSVER": "4"},
    {"NACCID": "N009", "NACCVNUM": "2", "VISITMO": "9", "VISITDAY": "1", "VISITYR": "2021", "NACCAGE": "78", "NACCUDSD": "-4", "CDRGLOB": "-4", "CDRSUM": "-4", "NACCMMSE": "-4", "UDSVER": "4"},
]

MEDICATIONS = [
    {"NACCID": "N001", "NACCVNUM": "1", "DRUGNAME": "DrugA", "DRUG_STARTMO": "1", "DRUG_STARTYR": "2020", "CURRENT_USE": "1", "UDSVER": "3"},
    {"NACCID": "N002", "NACCVNUM": "1", "DRUGNAME": "DrugB", "DRUG_STARTMO": "2", "DRUG_STARTYR": "2020", "CURRENT_USE": "1", "UDSVER": "3"},
    {"NACCID": "N003", "NACCVNUM": "1", "DRUGNAME": "DrugA", "DRUG_STARTMO": "3", "DRUG_STARTYR": "2020", "CURRENT_USE": "1", "UDSVER": "3"},
    {"NACCID": "N004", "NACCVNUM": "1", "DRUGNAME": "DrugB", "DRUG_STARTMO": "4", "DRUG_STARTYR": "2020", "CURRENT_USE": "1", "UDSVER": "3"},
    {"NACCID": "N005", "NACCVNUM": "1", "DRUGNAME": "DrugA", "DRUG_STARTMO": "5", "DRUG_STARTYR": "2020", "CURRENT_USE": "1", "UDSVER": "3"},
    {"NACCID": "N006", "NACCVNUM": "1", "DRUGNAME": "DrugB", "DRUG_STARTMO": "6", "DRUG_STARTYR": "2020", "CURRENT_USE": "1", "UDSVER": "3"},
    {"NACCID": "N007", "NACCVNUM": "1", "DRUGNAME": "DrugA", "DRUG_STARTMO": "7", "DRUG_STARTYR": "2020", "CURRENT_USE": "1", "UDSVER": "3"},
    {"NACCID": "N008", "NACCVNUM": "1", "DRUGNAME": "DrugB", "DRUG_STARTMO": "-4", "DRUG_STARTYR": "-4", "CURRENT_USE": "1", "UDSVER": "4"},
    {"NACCID": "N009", "NACCVNUM": "1", "DRUGNAME": "DrugA", "DRUG_STARTMO": "9", "DRUG_STARTYR": "2020", "CURRENT_USE": "1", "UDSVER": "4"},
]

FOLLOWUP_STATUS = [
    {"NACCID": "N001", "DECEASED": "0", "DROPOUT": "0", "LAST_CONTACT_YR": "2021"},
    {"NACCID": "N002", "DECEASED": "0", "DROPOUT": "0", "LAST_CONTACT_YR": "2021"},
    {"NACCID": "N003", "DECEASED": "0", "DROPOUT": "0", "LAST_CONTACT_YR": "2021"},
    {"NACCID": "N004", "DECEASED": "0", "DROPOUT": "0", "LAST_CONTACT_YR": "2021"},
    {"NACCID": "N005", "DECEASED": "0", "DROPOUT": "0", "LAST_CONTACT_YR": "2021"},
    {"NACCID": "N006", "DECEASED": "0", "DROPOUT": "1", "LAST_CONTACT_YR": "2020"},
    {"NACCID": "N007", "DECEASED": "0", "DROPOUT": "0", "LAST_CONTACT_YR": "2021"},
    {"NACCID": "N008", "DECEASED": "0", "DROPOUT": "0", "LAST_CONTACT_YR": "2021"},
    {"NACCID": "N009", "DECEASED": "1", "DROPOUT": "0", "LAST_CONTACT_YR": "2021"},
]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("examples/inputs/nacc_like_synthetic"))
    args = parser.parse_args()

    write_csv(args.output_dir / "participants.csv", PARTICIPANTS)
    write_csv(args.output_dir / "uds_visits.csv", UDS_VISITS)
    write_csv(args.output_dir / "medications.csv", MEDICATIONS)
    write_csv(args.output_dir / "followup_status.csv", FOLLOWUP_STATUS)
    print(f"Wrote NACC-like synthetic data to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
