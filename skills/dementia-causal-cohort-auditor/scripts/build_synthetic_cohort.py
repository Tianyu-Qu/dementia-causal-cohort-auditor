#!/usr/bin/env python
"""Build a synthetic dementia treatment cohort and reports."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ELIGIBLE_DRUGS = {"DrugA", "DrugB"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def earliest_treatment(meds: list[dict[str, str]]) -> dict[str, str] | None:
    eligible = [row for row in meds if row["drug"] in ELIGIBLE_DRUGS and row["start_date"]]
    if not eligible:
        return None
    return min(eligible, key=lambda row: row["start_date"])


def latest_baseline(visits: list[dict[str, str]], time_zero: date) -> dict[str, str] | None:
    eligible = [row for row in visits if parse_date(row["visit_date"]) <= time_zero]
    if not eligible:
        return None
    return max(eligible, key=lambda row: row["visit_date"])


def followup_visits(visits: list[dict[str, str]], time_zero: date) -> list[dict[str, str]]:
    return sorted([row for row in visits if parse_date(row["visit_date"]) > time_zero], key=lambda row: row["visit_date"])


def count_distinct(rows: list[dict[str, object]]) -> int:
    return len({str(row["participant_id"]) for row in rows})


def build(input_dir: Path, output_dir: Path) -> None:
    patients = read_csv(input_dir / "patients.csv")
    visits = read_csv(input_dir / "visits.csv")
    medications = read_csv(input_dir / "medications.csv")

    visits_by_patient: dict[str, list[dict[str, str]]] = defaultdict(list)
    meds_by_patient: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in visits:
        visits_by_patient[row["participant_id"]].append(row)
    for row in medications:
        meds_by_patient[row["participant_id"]].append(row)

    working: list[dict[str, object]] = [{"participant_id": row["participant_id"], "patient": row} for row in patients]
    attrition = [{"stage": "all_patients", "n": len(working), "excluded_at_stage": 0}]

    def apply_stage(stage: str, predicate) -> None:
        nonlocal working
        before = count_distinct(working)
        working = [row for row in working if predicate(row)]
        after = count_distinct(working)
        attrition.append({"stage": stage, "n": after, "excluded_at_stage": before - after})

    treatment_by_patient = {pid: earliest_treatment(rows) for pid, rows in meds_by_patient.items()}
    apply_stage("has_drug_a_or_b_initiation", lambda row: treatment_by_patient.get(str(row["participant_id"])) is not None)

    baselines: dict[str, dict[str, str] | None] = {}
    followups: dict[str, list[dict[str, str]]] = {}
    for row in working:
        pid = str(row["participant_id"])
        treatment = treatment_by_patient[pid]
        assert treatment is not None
        time_zero = parse_date(treatment["start_date"])
        baselines[pid] = latest_baseline(visits_by_patient[pid], time_zero)
        followups[pid] = followup_visits(visits_by_patient[pid], time_zero)

    apply_stage("has_baseline_visit", lambda row: baselines.get(str(row["participant_id"])) is not None)
    apply_stage("age_eligible", lambda row: int(str(baselines[str(row["participant_id"])]["age"])) >= 65)
    apply_stage("dementia_free_at_baseline", lambda row: str(baselines[str(row["participant_id"])]["cognitive_status"]).lower() != "dementia")
    apply_stage("apoe_available", lambda row: bool(str(row["patient"]["apoe_e4_count"]).strip()))
    apply_stage("followup_available", lambda row: len(followups.get(str(row["participant_id"]), [])) >= 1)

    cohort: list[dict[str, object]] = []
    for row in working:
        pid = str(row["participant_id"])
        patient = row["patient"]
        treatment = treatment_by_patient[pid]
        baseline = baselines[pid]
        followup = followups[pid][-1]
        assert treatment is not None
        assert baseline is not None
        baseline_mmse = baseline["mmse"]
        followup_mmse = followup["mmse"]
        mmse_change = ""
        if baseline_mmse and followup_mmse:
            mmse_change = str(int(followup_mmse) - int(baseline_mmse))
        cohort.append(
            {
                "participant_id": pid,
                "treatment": treatment["drug"],
                "time_zero": treatment["start_date"],
                "baseline_visit_date": baseline["visit_date"],
                "baseline_age": baseline["age"],
                "sex": patient["sex"],
                "education_years": patient["education_years"],
                "apoe_e4_count": patient["apoe_e4_count"],
                "baseline_cognitive_status": baseline["cognitive_status"],
                "baseline_mmse": baseline_mmse,
                "followup_visit_date": followup["visit_date"],
                "followup_mmse": followup_mmse,
                "mmse_change": mmse_change,
            }
        )

    write_csv(output_dir / "cohort.csv", cohort, list(cohort[0].keys()) if cohort else ["participant_id"])
    write_csv(output_dir / "attrition_table.csv", attrition, ["stage", "n", "excluded_at_stage"])
    write_reports(output_dir, patients, visits, cohort)


def write_reports(output_dir: Path, patients: list[dict[str, str]], visits: list[dict[str, str]], cohort: list[dict[str, object]]) -> None:
    visit_keys = Counter((row["participant_id"], row["visit_id"]) for row in visits)
    duplicate_visits = sum(1 for count in visit_keys.values() if count > 1)
    missing_apoe = sum(1 for row in patients if not row["apoe_e4_count"].strip())
    missing_baseline_mmse = sum(1 for row in cohort if not str(row["baseline_mmse"]).strip())
    missing_followup_mmse = sum(1 for row in cohort if not str(row["followup_mmse"]).strip())
    treatment_counts = Counter(str(row["treatment"]) for row in cohort)

    dq = [
        "# Data Quality Report",
        "",
        f"- Included participants: {len(cohort)}",
        f"- Duplicate visit keys in source visits: {duplicate_visits}",
        f"- Missing APOE in source patients: {missing_apoe}",
        f"- Missing baseline MMSE in included cohort: {missing_baseline_mmse}",
        f"- Missing follow-up MMSE in included cohort: {missing_followup_mmse}",
        f"- Treatment counts: {dict(treatment_counts)}",
    ]
    (output_dir / "data_quality_report.md").write_text("\n".join(dq) + "\n", encoding="utf-8")

    leakage_rows = []
    for row in cohort:
        if str(row["baseline_visit_date"]) > str(row["time_zero"]):
            leakage_rows.append(f"- {row['participant_id']}: baseline visit after time zero")
        if str(row["followup_visit_date"]) <= str(row["time_zero"]):
            leakage_rows.append(f"- {row['participant_id']}: follow-up visit on or before time zero")
    leakage = [
        "# Leakage Report",
        "",
        "## Deterministic Checks",
        "",
        *(leakage_rows or ["- No deterministic temporal leakage detected in included cohort."]),
        "",
        "## Design Warnings",
        "",
        "- APOE availability restriction may create selection bias and should be audited.",
        "- Follow-up availability restriction can induce selection bias if treated as baseline eligibility.",
    ]
    (output_dir / "leakage_report.md").write_text("\n".join(leakage) + "\n", encoding="utf-8")

    manifest = {
        "schema_version": "0.4",
        "created_by": "dementia-causal-cohort-auditor",
        "data_source": "synthetic",
        "rules": {
            "time_zero": "first DrugA or DrugB start date",
            "baseline_visit": "latest visit on or before time zero",
            "age_rule": "baseline age >= 65",
            "baseline_dementia_rule": "baseline cognitive_status != dementia",
            "apoe_rule": "apoe_e4_count not missing",
            "followup_rule": "at least one visit after time zero",
        },
        "outputs": ["cohort.csv", "attrition_table.csv", "data_quality_report.md", "leakage_report.md"],
    }
    (output_dir / "reproducibility_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("examples/inputs/synthetic"))
    parser.add_argument("--output-dir", type=Path, default=Path("examples/outputs/synthetic_execution"))
    args = parser.parse_args()

    build(args.input_dir, args.output_dir)
    print(f"Wrote synthetic cohort execution outputs to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
