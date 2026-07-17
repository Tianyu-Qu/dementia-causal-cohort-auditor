#!/usr/bin/env python
"""Build the first executable NACC-like prediction cohort package.

v0.15 intentionally supports one task family first:
prediction / cognitive decline on NACC-like inputs. It is safe for synthetic
or explicitly approved data execution, and it writes a reviewable cohort
package plus acceptance-ready reports.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path


MISSING_CODES = {"", "-4", "-7", "-8", "-9", "8", "88", "888", "9", "99", "999"}
DEMENTIA_CODES = {"4", "dementia"}


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


def has_value(value: object) -> bool:
    return str(value).strip() not in MISSING_CODES


def parse_visit_date(row: dict[str, str]) -> date | None:
    if not has_value(row.get("VISITMO", "")) or not has_value(row.get("VISITDAY", "")) or not has_value(row.get("VISITYR", "")):
        return None
    try:
        return date(int(row["VISITYR"]), int(row["VISITMO"]), int(row["VISITDAY"]))
    except ValueError:
        return None


def as_int(value: object) -> int | None:
    if not has_value(value):
        return None
    try:
        return int(float(str(value)))
    except ValueError:
        return None


def distinct_ids(rows: list[dict[str, object]]) -> int:
    return len({str(row["NACCID"]) for row in rows})


def deduplicate_visits(visits: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    seen: set[tuple[str, str]] = set()
    deduped = []
    duplicate_count = 0
    for row in visits:
        key = (row.get("NACCID", ""), row.get("NACCVNUM", ""))
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        deduped.append(row)
    return deduped, duplicate_count


def choose_baseline(visits: list[dict[str, str]]) -> dict[str, str] | None:
    dated = [(parse_visit_date(row), row) for row in visits]
    dated = [(dt, row) for dt, row in dated if dt is not None]
    if not dated:
        return None
    return min(dated, key=lambda item: (item[0], as_int(item[1].get("NACCVNUM", "")) or 999999))[1]


def followups_after(visits: list[dict[str, str]], baseline: dict[str, str]) -> list[dict[str, str]]:
    baseline_date = parse_visit_date(baseline)
    if baseline_date is None:
        return []
    candidates = []
    for row in visits:
        dt = parse_visit_date(row)
        if dt is not None and dt > baseline_date:
            candidates.append((dt, row))
    return [row for _, row in sorted(candidates, key=lambda item: (item[0], as_int(item[1].get("NACCVNUM", "")) or 999999))]


def build(input_dir: Path, output_dir: Path, run_acceptance: bool = True) -> None:
    participants = read_csv(input_dir / "participants.csv")
    visits_raw = read_csv(input_dir / "uds_visits.csv")
    visits, duplicate_visit_rows = deduplicate_visits(visits_raw)

    participant_by_id = {row["NACCID"]: row for row in participants}
    visits_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in visits:
        visits_by_id[row["NACCID"]].append(row)

    rows: list[dict[str, object]] = [{"NACCID": row["NACCID"], "participant": row} for row in participants]
    attrition: list[Stage] = [Stage("all_participants", len(rows), 0)]

    def apply(stage: str, predicate) -> None:
        nonlocal rows
        before = distinct_ids(rows)
        rows = [row for row in rows if predicate(row)]
        after = distinct_ids(rows)
        attrition.append(Stage(stage, after, before - after))

    baseline_by_id: dict[str, dict[str, str] | None] = {}
    followups_by_id: dict[str, list[dict[str, str]]] = {}

    apply("has_uds_visit_records", lambda row: len(visits_by_id[str(row["NACCID"])]) >= 1)
    apply("has_valid_visit_order_or_date", lambda row: all(parse_visit_date(v) is not None for v in visits_by_id[str(row["NACCID"])]))

    for row in rows:
        naccid = str(row["NACCID"])
        baseline = choose_baseline(visits_by_id[naccid])
        baseline_by_id[naccid] = baseline
        followups_by_id[naccid] = followups_after(visits_by_id[naccid], baseline) if baseline else []

    apply("has_baseline_index_visit", lambda row: baseline_by_id.get(str(row["NACCID"])) is not None)
    apply("baseline_age_eligible", lambda row: (as_int(baseline_by_id[str(row["NACCID"])]["NACCAGE"]) or -1) >= 65)  # type: ignore[index]
    apply("baseline_dementia_free", lambda row: str(baseline_by_id[str(row["NACCID"])]["NACCUDSD"]).lower() not in DEMENTIA_CODES)  # type: ignore[index]
    apply("apoe_available", lambda row: has_value(row["participant"].get("NACCNE4S", "")))  # type: ignore[index]
    apply("has_baseline_cognitive_features", lambda row: has_value(baseline_by_id[str(row["NACCID"])]["NACCMMSE"]) and has_value(baseline_by_id[str(row["NACCID"])]["CDRGLOB"]))  # type: ignore[index]
    apply("has_post_index_followup_visit", lambda row: len(followups_by_id[str(row["NACCID"])]) >= 1)
    apply("has_followup_mmse_outcome", lambda row: any(has_value(v.get("NACCMMSE", "")) for v in followups_by_id[str(row["NACCID"])]))

    cohort_index = []
    feature_rows = []
    outcome_rows = []
    cohort_rows = []
    for row in rows:
        naccid = str(row["NACCID"])
        participant = participant_by_id[naccid]
        baseline = baseline_by_id[naccid]
        assert baseline is not None
        baseline_dt = parse_visit_date(baseline)
        outcome_visit = [visit for visit in followups_by_id[naccid] if has_value(visit.get("NACCMMSE", ""))][-1]
        outcome_dt = parse_visit_date(outcome_visit)
        assert baseline_dt is not None and outcome_dt is not None

        baseline_mmse = as_int(baseline["NACCMMSE"])
        outcome_mmse = as_int(outcome_visit["NACCMMSE"])
        assert baseline_mmse is not None and outcome_mmse is not None
        mmse_change = outcome_mmse - baseline_mmse
        decline_label = 1 if mmse_change <= -1 else 0

        cohort_index.append(
            {
                "NACCID": naccid,
                "index_NACCVNUM": baseline["NACCVNUM"],
                "index_visit_date": baseline_dt.isoformat(),
                "outcome_NACCVNUM": outcome_visit["NACCVNUM"],
                "outcome_visit_date": outcome_dt.isoformat(),
            }
        )
        feature_rows.append(
            {
                "NACCID": naccid,
                "index_visit_date": baseline_dt.isoformat(),
                "baseline_NACCAGE": baseline["NACCAGE"],
                "SEX": participant.get("SEX", ""),
                "EDUC": participant.get("EDUC", ""),
                "NACCNE4S": participant.get("NACCNE4S", ""),
                "baseline_NACCUDSD": baseline["NACCUDSD"],
                "baseline_CDRGLOB": baseline["CDRGLOB"],
                "baseline_CDRSUM": baseline["CDRSUM"],
                "baseline_NACCMMSE": baseline["NACCMMSE"],
                "baseline_UDSVER": baseline.get("UDSVER", ""),
            }
        )
        outcome_rows.append(
            {
                "NACCID": naccid,
                "index_visit_date": baseline_dt.isoformat(),
                "outcome_visit_date": outcome_dt.isoformat(),
                "outcome_NACCMMSE": outcome_visit["NACCMMSE"],
                "mmse_change": mmse_change,
                "cognitive_decline_label": decline_label,
            }
        )
        cohort_rows.append({**cohort_index[-1], **feature_rows[-1], **outcome_rows[-1]})

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "cohort_index.csv", cohort_index, list(cohort_index[0].keys()) if cohort_index else ["NACCID"])
    write_csv(output_dir / "feature_table.csv", feature_rows, list(feature_rows[0].keys()) if feature_rows else ["NACCID"])
    write_csv(output_dir / "outcome_table.csv", outcome_rows, list(outcome_rows[0].keys()) if outcome_rows else ["NACCID"])
    write_csv(output_dir / "cohort.csv", cohort_rows, list(cohort_rows[0].keys()) if cohort_rows else ["NACCID"])
    write_csv(output_dir / "attrition_table.csv", [stage.__dict__ for stage in attrition], ["stage", "n", "excluded_at_stage"])
    write_reports(output_dir, participants, visits_raw, duplicate_visit_rows, cohort_rows)

    if run_acceptance:
        subprocess.run(
            [sys.executable, str(Path(__file__).with_name("run_acceptance_checks.py")), str(output_dir)],
            check=False,
            capture_output=True,
            text=True,
        )


def write_reports(
    output_dir: Path,
    participants: list[dict[str, str]],
    visits_raw: list[dict[str, str]],
    duplicate_visit_rows: int,
    cohort_rows: list[dict[str, object]],
) -> None:
    missing_apoe = sum(1 for row in participants if not has_value(row.get("NACCNE4S", "")))
    structural_mmse_missing = sum(1 for row in visits_raw if row.get("UDSVER") == "4" and not has_value(row.get("NACCMMSE", "")))
    baseline_uds = Counter(str(row.get("baseline_UDSVER", "")) for row in cohort_rows)
    decline_counts = Counter(str(row.get("cognitive_decline_label", "")) for row in cohort_rows)

    dq_lines = [
        "# NACC Prediction Cohort Data Quality Report",
        "",
        f"- Included participants: {len(cohort_rows)}",
        f"- Duplicate raw `(NACCID, NACCVNUM)` visit rows removed before construction: {duplicate_visit_rows}",
        f"- Participants with missing APOE/e4 count codes in source participants table: {missing_apoe}",
        f"- UDSv4 rows with structural/missing MMSE-like code: {structural_mmse_missing}",
        f"- Baseline UDS version counts: {dict(baseline_uds)}",
        f"- Cognitive decline label counts: {dict(decline_counts)}",
    ]
    (output_dir / "data_quality_report.md").write_text("\n".join(dq_lines) + "\n", encoding="utf-8")

    leakage_rows = []
    for row in cohort_rows:
        if str(row["outcome_visit_date"]) <= str(row["index_visit_date"]):
            leakage_rows.append(f"- {row['NACCID']}: outcome visit not after index")
    leakage_lines = [
        "# NACC Prediction Cohort Leakage Report",
        "",
        "## Temporal Checks",
        "",
        *(leakage_rows or ["- No deterministic temporal leakage detected: every outcome visit is after index."]),
        "",
        "## Design Warnings",
        "",
        "- Baseline predictors are limited to index-visit or time-invariant fields.",
        "- Outcome MMSE is taken from post-index follow-up visits only.",
        "- APOE availability restriction can create selection bias and must be reported in attrition.",
        "- Requiring follow-up can condition on future observation; interpret as outcome ascertainment unless approved otherwise.",
        "- UDS/form-version differences can create structural missingness and should be assessed before downstream modeling.",
    ]
    (output_dir / "leakage_report.md").write_text("\n".join(leakage_lines) + "\n", encoding="utf-8")

    manifest = {
        "schema_version": "0.15",
        "created_by": "dementia-causal-cohort-auditor",
        "data_source": "nacc_prediction_synthetic",
        "cohort_task": "prediction_cognitive_decline",
        "patient_level_output": True,
        "execution_scope": "synthetic_or_explicitly_approved",
        "rules": {
            "time_zero": "first valid NACC-like UDS visit",
            "baseline_window": "index visit only",
            "age_rule": "baseline NACCAGE >= 65",
            "baseline_dementia_rule": "baseline NACCUDSD not in dementia codes",
            "apoe_rule": "NACCNE4S not in missing-like codes",
            "followup_rule": "at least one post-index visit with non-missing NACCMMSE",
            "outcome_rule": "cognitive_decline_label = 1 when follow-up NACCMMSE - baseline NACCMMSE <= -1",
        },
        "outputs": [
            "cohort_index.csv",
            "feature_table.csv",
            "outcome_table.csv",
            "cohort.csv",
            "attrition_table.csv",
            "data_quality_report.md",
            "leakage_report.md",
            "acceptance_report.md",
            "reproducibility_manifest.json",
        ],
    }
    (output_dir / "reproducibility_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build v0.15 NACC-like prediction/cognitive-decline cohort package.")
    parser.add_argument("--input-dir", type=Path, default=Path("examples/inputs/nacc_like_synthetic"))
    parser.add_argument("--output-dir", type=Path, default=Path("examples/outputs/nacc_prediction_execution"))
    parser.add_argument("--skip-acceptance", action="store_true")
    args = parser.parse_args()
    build(args.input_dir, args.output_dir, run_acceptance=not args.skip_acceptance)
    print(f"Wrote NACC prediction cohort package to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
