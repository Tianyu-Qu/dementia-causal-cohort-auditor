#!/usr/bin/env python
"""Run v0.5 acceptance checks for a cohort execution package."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path


REQUIRED_FILES = [
    "cohort.csv",
    "attrition_table.csv",
    "data_quality_report.md",
    "leakage_report.md",
    "reproducibility_manifest.json",
]

MISSING_CODES = {"", "-4", "8", "88", "9", "99"}
DEMENTIA_CODES = {"4", "dementia"}


@dataclass
class Check:
    name: str
    result: str
    detail: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def detect_schema(cohort: list[dict[str, str]], manifest: dict[str, object]) -> str:
    data_source = str(manifest.get("data_source", ""))
    cohort_task = str(manifest.get("cohort_task", ""))
    if data_source == "nacc_prediction_synthetic" or cohort_task == "prediction_cognitive_decline":
        return "nacc_prediction"
    if data_source == "nacc_like_synthetic" or (cohort and "NACCID" in cohort[0]):
        return "nacc_like"
    return "simple"


def add(checks: list[Check], name: str, ok: bool, detail: str, warn: bool = False) -> None:
    if ok:
        checks.append(Check(name, "PASS", detail))
    elif warn:
        checks.append(Check(name, "WARN", detail))
    else:
        checks.append(Check(name, "FAIL", detail))


def run_checks(package_dir: Path) -> tuple[list[Check], dict[str, object]]:
    checks: list[Check] = []
    missing_files = [name for name in REQUIRED_FILES if not (package_dir / name).exists()]
    add(checks, "required_files", not missing_files, "All required files exist." if not missing_files else f"Missing: {missing_files}")
    if missing_files:
        return checks, {"schema": "unknown", "cohort_rows": 0, "final_attrition": None, "data_source": "unknown"}

    cohort = read_csv(package_dir / "cohort.csv")
    attrition = read_csv(package_dir / "attrition_table.csv")
    manifest = json.loads((package_dir / "reproducibility_manifest.json").read_text(encoding="utf-8"))
    leakage_report = (package_dir / "leakage_report.md").read_text(encoding="utf-8").lower()
    dq_report = (package_dir / "data_quality_report.md").read_text(encoding="utf-8").lower()
    schema = detect_schema(cohort, manifest)

    counts = [int(row["n"]) for row in attrition]
    monotone = all(left >= right for left, right in zip(counts, counts[1:]))
    add(checks, "attrition_monotone", monotone, f"Attrition counts: {counts}")
    final_count = counts[-1] if counts else None
    add(checks, "cohort_row_count_matches_attrition", final_count == len(cohort), f"cohort rows={len(cohort)}, final attrition={final_count}")

    id_field = "NACCID" if schema in {"nacc_like", "nacc_prediction"} else "participant_id"
    ids = [row[id_field] for row in cohort]
    duplicate_ids = [pid for pid, count in Counter(ids).items() if count > 1]
    add(checks, "unique_participant_ids", not duplicate_ids, "No duplicate participant identifiers." if not duplicate_ids else f"Duplicates: {duplicate_ids}")

    if schema == "nacc_prediction":
        run_nacc_prediction_checks(checks, cohort)
    elif schema == "nacc_like":
        run_nacc_like_checks(checks, cohort)
    else:
        run_simple_checks(checks, cohort)

    add(checks, "leakage_report_temporal_warning", "temporal" in leakage_report or "time zero" in leakage_report, "Leakage report contains temporal warning.", warn=True)
    add(checks, "leakage_report_apoe_warning", "apoe" in leakage_report, "Leakage report mentions APOE selection risk.", warn=True)
    add(checks, "leakage_report_followup_warning", "follow-up" in leakage_report or "followup" in leakage_report, "Leakage report mentions follow-up selection risk.", warn=True)
    add(checks, "data_quality_report_missingness", "missing" in dq_report or "structural" in dq_report, "Data quality report mentions missingness or structural missingness.", warn=True)

    summary = {
        "schema": schema,
        "cohort_rows": len(cohort),
        "final_attrition": final_count,
        "data_source": manifest.get("data_source", "unknown"),
    }
    return checks, summary


def run_simple_checks(checks: list[Check], cohort: list[dict[str, str]]) -> None:
    bad_baseline = [row["participant_id"] for row in cohort if parse_date(row["baseline_visit_date"]) > parse_date(row["time_zero"])]
    bad_followup = [row["participant_id"] for row in cohort if parse_date(row["followup_visit_date"]) <= parse_date(row["time_zero"])]
    bad_age = [row["participant_id"] for row in cohort if int(row["baseline_age"]) < 65]
    dementia = [row["participant_id"] for row in cohort if row["baseline_cognitive_status"].lower() == "dementia"]
    missing_apoe = [row["participant_id"] for row in cohort if row["apoe_e4_count"] in MISSING_CODES]
    missing_outcome = [row["participant_id"] for row in cohort if row["followup_mmse"] in MISSING_CODES]
    add(checks, "baseline_before_or_at_time_zero", not bad_baseline, f"Violations: {bad_baseline}")
    add(checks, "followup_after_time_zero", not bad_followup, f"Violations: {bad_followup}")
    add(checks, "baseline_age_rule", not bad_age, f"Violations: {bad_age}")
    add(checks, "baseline_dementia_free_rule", not dementia, f"Violations: {dementia}")
    add(checks, "apoe_available_rule", not missing_apoe, f"Violations: {missing_apoe}")
    add(checks, "followup_outcome_available_rule", not missing_outcome, f"Violations: {missing_outcome}")


def run_nacc_like_checks(checks: list[Check], cohort: list[dict[str, str]]) -> None:
    bad_baseline = [row["NACCID"] for row in cohort if parse_date(row["baseline_visit_date"]) > parse_date(row["time_zero"])]
    bad_followup = [row["NACCID"] for row in cohort if parse_date(row["followup_visit_date"]) <= parse_date(row["time_zero"])]
    bad_age = [row["NACCID"] for row in cohort if int(row["baseline_NACCAGE"]) < 65]
    dementia = [row["NACCID"] for row in cohort if row["baseline_NACCUDSD"].lower() in DEMENTIA_CODES]
    missing_apoe = [row["NACCID"] for row in cohort if row["NACCNE4S"] in MISSING_CODES]
    missing_outcome = [row["NACCID"] for row in cohort if row["followup_NACCMMSE"] in MISSING_CODES]
    add(checks, "baseline_before_or_at_time_zero", not bad_baseline, f"Violations: {bad_baseline}")
    add(checks, "followup_after_time_zero", not bad_followup, f"Violations: {bad_followup}")
    add(checks, "baseline_age_rule", not bad_age, f"Violations: {bad_age}")
    add(checks, "baseline_dementia_free_rule", not dementia, f"Violations: {dementia}")
    add(checks, "apoe_available_rule", not missing_apoe, f"Violations: {missing_apoe}")
    add(checks, "followup_outcome_available_rule", not missing_outcome, f"Violations: {missing_outcome}")


def run_nacc_prediction_checks(checks: list[Check], cohort: list[dict[str, str]]) -> None:
    bad_outcome_timing = [row["NACCID"] for row in cohort if parse_date(row["outcome_visit_date"]) <= parse_date(row["index_visit_date"])]
    bad_age = [row["NACCID"] for row in cohort if int(row["baseline_NACCAGE"]) < 65]
    dementia = [row["NACCID"] for row in cohort if row["baseline_NACCUDSD"].lower() in DEMENTIA_CODES]
    missing_apoe = [row["NACCID"] for row in cohort if row["NACCNE4S"] in MISSING_CODES]
    missing_baseline = [row["NACCID"] for row in cohort if row["baseline_NACCMMSE"] in MISSING_CODES]
    missing_outcome = [row["NACCID"] for row in cohort if row["outcome_NACCMMSE"] in MISSING_CODES]
    bad_label = []
    for row in cohort:
        expected = 1 if int(row["mmse_change"]) <= -1 else 0
        if int(row["cognitive_decline_label"]) != expected:
            bad_label.append(row["NACCID"])
    add(checks, "outcome_after_index", not bad_outcome_timing, f"Violations: {bad_outcome_timing}")
    add(checks, "baseline_age_rule", not bad_age, f"Violations: {bad_age}")
    add(checks, "baseline_dementia_free_rule", not dementia, f"Violations: {dementia}")
    add(checks, "apoe_available_rule", not missing_apoe, f"Violations: {missing_apoe}")
    add(checks, "baseline_mmse_available_rule", not missing_baseline, f"Violations: {missing_baseline}")
    add(checks, "followup_outcome_available_rule", not missing_outcome, f"Violations: {missing_outcome}")
    add(checks, "cognitive_decline_label_rule", not bad_label, f"Violations: {bad_label}")


def write_report(package_dir: Path, checks: list[Check], summary: dict[str, object]) -> str:
    failures = [check for check in checks if check.result == "FAIL"]
    warnings = [check for check in checks if check.result == "WARN"]
    status = "FAIL" if failures else ("WARN" if warnings else "PASS")
    lines = [
        "# Acceptance Report",
        "",
        f"- Status: {status}",
        f"- Package: {package_dir}",
        f"- Data source: {summary['data_source']}",
        f"- Schema: {summary['schema']}",
        f"- Cohort rows: {summary['cohort_rows']}",
        f"- Final attrition count: {summary['final_attrition']}",
        "",
        "## Blocking Failures",
        "",
    ]
    lines.extend([f"- {check.name}: {check.detail}" for check in failures] or ["- None."])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {check.name}: {check.detail}" for check in warnings] or ["- None."])
    lines.extend(["", "## Checks", "", "| Check | Result | Detail |", "| --- | --- | --- |"])
    for check in checks:
        detail = check.detail.replace("|", "\\|")
        lines.append(f"| {check.name} | {check.result} | {detail} |")
    recommendation = (
        "Fix blocking failures before downstream analysis."
        if failures
        else "Package is acceptable for methodological review; freeze only after final human approval."
    )
    lines.extend(["", "## Recommendation", "", recommendation])
    report = "\n".join(lines) + "\n"
    (package_dir / "acceptance_report.md").write_text(report, encoding="utf-8")
    return status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package_dir", type=Path)
    args = parser.parse_args()
    checks, summary = run_checks(args.package_dir)
    status = write_report(args.package_dir, checks, summary)
    print(f"Acceptance status: {status}")
    return 1 if status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
