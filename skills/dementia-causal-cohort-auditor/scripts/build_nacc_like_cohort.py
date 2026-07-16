#!/usr/bin/env python
"""Build a cohort from NACC-like synthetic CSV files."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ELIGIBLE_DRUGS = {"DrugA", "DrugB"}
MISSING_CODES = {"", "-4", "8", "9", "88", "99"}
DEMENTIA_CODES = {"4"}


@dataclass(frozen=True)
class Stage:
    stage: str
    n: int
    excluded_at_stage: int


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def visit_date(row: dict[str, str]) -> date | None:
    if row["VISITMO"] in MISSING_CODES or row["VISITDAY"] in MISSING_CODES or row["VISITYR"] in MISSING_CODES:
        return None
    return date(int(row["VISITYR"]), int(row["VISITMO"]), int(row["VISITDAY"]))


def treatment_date(row: dict[str, str]) -> date | None:
    if row["DRUG_STARTMO"] in MISSING_CODES or row["DRUG_STARTYR"] in MISSING_CODES:
        return None
    return date(int(row["DRUG_STARTYR"]), int(row["DRUG_STARTMO"]), 15)


def has_value(value: str) -> bool:
    return value not in MISSING_CODES


def distinct_ids(rows: list[dict[str, object]]) -> int:
    return len({str(row["NACCID"]) for row in rows})


def build(input_dir: Path, output_dir: Path) -> None:
    participants = read_csv(input_dir / "participants.csv")
    visits = read_csv(input_dir / "uds_visits.csv")
    medications = read_csv(input_dir / "medications.csv")
    followup_status = read_csv(input_dir / "followup_status.csv")

    visits_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    meds_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    followup_by_id = {row["NACCID"]: row for row in followup_status}
    for row in visits:
        visits_by_id[row["NACCID"]].append(row)
    for row in medications:
        meds_by_id[row["NACCID"]].append(row)

    rows: list[dict[str, object]] = [{"NACCID": row["NACCID"], "participant": row} for row in participants]
    attrition: list[Stage] = [Stage("all_participants", len(rows), 0)]

    def apply(stage: str, predicate) -> None:
        nonlocal rows
        before = distinct_ids(rows)
        rows = [row for row in rows if predicate(row)]
        after = distinct_ids(rows)
        attrition.append(Stage(stage, after, before - after))

    apply("has_required_uds_visit_records", lambda row: len(visits_by_id[str(row["NACCID"])]) >= 1)
    apply("has_valid_visit_order_or_date", lambda row: all(visit_date(v) is not None for v in visits_by_id[str(row["NACCID"])]))

    first_treatment: dict[str, dict[str, str] | None] = {}
    first_treatment_date: dict[str, date | None] = {}
    for row in rows:
        naccid = str(row["NACCID"])
        candidates = [med for med in meds_by_id[naccid] if med["DRUGNAME"] in ELIGIBLE_DRUGS and med["CURRENT_USE"] == "1" and treatment_date(med)]
        selected = min(candidates, key=lambda med: treatment_date(med) or date.max) if candidates else None
        first_treatment[naccid] = selected
        first_treatment_date[naccid] = treatment_date(selected) if selected else None

    apply("has_treatment_exposure_module_available", lambda row: len(meds_by_id[str(row["NACCID"])]) >= 1)
    apply("has_active_comparator_exposure", lambda row: first_treatment.get(str(row["NACCID"])) is not None)

    baseline_by_id: dict[str, dict[str, str] | None] = {}
    followup_visits_by_id: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        naccid = str(row["NACCID"])
        time_zero = first_treatment_date.get(naccid)
        if time_zero is None:
            baseline_by_id[naccid] = None
            followup_visits_by_id[naccid] = []
            continue
        dated_visits = [(visit_date(v), v) for v in visits_by_id[naccid] if visit_date(v) is not None]
        baseline_candidates = [pair for pair in dated_visits if pair[0] and pair[0] <= time_zero]
        followup_candidates = [pair for pair in dated_visits if pair[0] and pair[0] > time_zero]
        baseline_by_id[naccid] = max(baseline_candidates, key=lambda pair: pair[0])[1] if baseline_candidates else None
        followup_visits_by_id[naccid] = [pair[1] for pair in sorted(followup_candidates, key=lambda pair: pair[0])]

    apply("has_baseline_candidate_visit", lambda row: baseline_by_id.get(str(row["NACCID"])) is not None)
    apply("baseline_age_eligible", lambda row: int(str(baseline_by_id[str(row["NACCID"])]["NACCAGE"])) >= 65)
    apply("baseline_dementia_free", lambda row: str(baseline_by_id[str(row["NACCID"])]["NACCUDSD"]) not in DEMENTIA_CODES)
    apply("has_required_cognitive_status_fields", lambda row: has_value(str(baseline_by_id[str(row["NACCID"])]["NACCUDSD"])) and has_value(str(baseline_by_id[str(row["NACCID"])]["CDRGLOB"])))
    apply("has_neuropsych_outcome_available", lambda row: bool(followup_visits_by_id[str(row["NACCID"])]) and has_value(str(followup_visits_by_id[str(row["NACCID"])][-1]["NACCMMSE"])))
    apply("has_apoe_or_genetics_available", lambda row: has_value(str(row["participant"]["NACCNE4S"])))
    apply("has_post_index_followup_visit", lambda row: bool(followup_visits_by_id[str(row["NACCID"])]))

    cohort: list[dict[str, object]] = []
    for row in rows:
        naccid = str(row["NACCID"])
        participant = row["participant"]
        treatment = first_treatment[naccid]
        baseline = baseline_by_id[naccid]
        followup = followup_visits_by_id[naccid][-1]
        assert treatment is not None
        assert baseline is not None
        time_zero = first_treatment_date[naccid]
        assert time_zero is not None
        cohort.append(
            {
                "NACCID": naccid,
                "NACCADC": participant["NACCADC"],
                "treatment": treatment["DRUGNAME"],
                "time_zero": time_zero.isoformat(),
                "baseline_NACCVNUM": baseline["NACCVNUM"],
                "baseline_visit_date": str(visit_date(baseline)),
                "baseline_NACCAGE": baseline["NACCAGE"],
                "SEX": participant["SEX"],
                "EDUC": participant["EDUC"],
                "NACCNE4S": participant["NACCNE4S"],
                "baseline_NACCUDSD": baseline["NACCUDSD"],
                "baseline_CDRGLOB": baseline["CDRGLOB"],
                "baseline_CDRSUM": baseline["CDRSUM"],
                "baseline_NACCMMSE": baseline["NACCMMSE"],
                "followup_NACCVNUM": followup["NACCVNUM"],
                "followup_visit_date": str(visit_date(followup)),
                "followup_NACCMMSE": followup["NACCMMSE"],
                "mmse_change": int(followup["NACCMMSE"]) - int(baseline["NACCMMSE"]),
                "UDSVER_baseline": baseline["UDSVER"],
                "DECEASED": followup_by_id.get(naccid, {}).get("DECEASED", ""),
                "DROPOUT": followup_by_id.get(naccid, {}).get("DROPOUT", ""),
            }
        )

    fields = list(cohort[0].keys()) if cohort else ["NACCID"]
    write_csv(output_dir / "cohort.csv", cohort, fields)
    write_csv(output_dir / "attrition_table.csv", [stage.__dict__ for stage in attrition], ["stage", "n", "excluded_at_stage"])
    write_reports(output_dir, participants, visits, medications, cohort)


def write_reports(
    output_dir: Path,
    participants: list[dict[str, str]],
    visits: list[dict[str, str]],
    medications: list[dict[str, str]],
    cohort: list[dict[str, object]],
) -> None:
    duplicate_visit_keys = sum(1 for count in Counter((v["NACCID"], v["NACCVNUM"]) for v in visits).values() if count > 1)
    structural_missing_rows = sum(1 for v in visits if v["UDSVER"] == "4" and v["NACCMMSE"] == "-4")
    missing_apoe = sum(1 for row in participants if not has_value(row["NACCNE4S"]))
    missing_med_start = sum(1 for row in medications if row["DRUG_STARTMO"] in MISSING_CODES or row["DRUG_STARTYR"] in MISSING_CODES)
    treatment_counts = Counter(str(row["treatment"]) for row in cohort)
    uds_versions = Counter(str(row["UDSVER_baseline"]) for row in cohort)

    dq_lines = [
        "# NACC-like Data Quality Report",
        "",
        f"- Included participants: {len(cohort)}",
        f"- Duplicate `(NACCID, NACCVNUM)` visit keys: {duplicate_visit_keys}",
        f"- Participants with missing APOE/e4 count codes: {missing_apoe}",
        f"- Medication rows with missing/structural start month or year: {missing_med_start}",
        f"- UDSv4 rows with structural NACCMMSE missing code `-4`: {structural_missing_rows}",
        f"- Treatment counts: {dict(treatment_counts)}",
        f"- Baseline UDS version counts in included cohort: {dict(uds_versions)}",
    ]
    (output_dir / "data_quality_report.md").write_text("\n".join(dq_lines) + "\n", encoding="utf-8")

    leakage_rows = []
    for row in cohort:
        if str(row["baseline_visit_date"]) > str(row["time_zero"]):
            leakage_rows.append(f"- {row['NACCID']}: baseline visit after time zero")
        if str(row["followup_visit_date"]) <= str(row["time_zero"]):
            leakage_rows.append(f"- {row['NACCID']}: follow-up visit on or before time zero")
    leakage_lines = [
        "# NACC-like Leakage Report",
        "",
        "## Deterministic Checks",
        "",
        *(leakage_rows or ["- No deterministic temporal leakage detected in included cohort."]),
        "",
        "## NACC-like Design Warnings",
        "",
        "- UDS version differences can create structural missingness and should not be treated as ordinary missingness.",
        "- Medication exposure timing may be visit-level or incomplete; confirm before new-user or lag-window analyses.",
        "- APOE availability restriction may create selected analytic cohorts.",
        "- Follow-up availability should be treated as outcome ascertainment unless explicitly justified as eligibility.",
    ]
    (output_dir / "leakage_report.md").write_text("\n".join(leakage_lines) + "\n", encoding="utf-8")

    manifest = {
        "schema_version": "0.4.1",
        "created_by": "dementia-causal-cohort-auditor",
        "data_source": "nacc_like_synthetic",
        "missing_codes": sorted(MISSING_CODES),
        "rules": {
            "time_zero": "first eligible DrugA or DrugB start month/year, approximated as day 15",
            "baseline_visit": "latest UDS visit on or before time zero",
            "age_rule": "baseline NACCAGE >= 65",
            "baseline_dementia_rule": "baseline NACCUDSD not in dementia codes",
            "apoe_rule": "NACCNE4S not in missing codes",
            "outcome_rule": "post-index follow-up visit with non-missing NACCMMSE",
        },
        "outputs": ["cohort.csv", "attrition_table.csv", "data_quality_report.md", "leakage_report.md"],
    }
    (output_dir / "reproducibility_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("examples/inputs/nacc_like_synthetic"))
    parser.add_argument("--output-dir", type=Path, default=Path("examples/outputs/nacc_like_execution"))
    args = parser.parse_args()

    build(args.input_dir, args.output_dir)
    print(f"Wrote NACC-like cohort execution outputs to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
