#!/usr/bin/env python
"""Guarded real-NACC prediction/cognitive-decline pilot.

This v0.15.1 pilot is intentionally narrow:
- one core file: investigator_ftldlbd_nacc70.csv
- one task: 65+, baseline dementia-free, APOE available, post-index MMSE follow-up
- local patient-level output only after explicit flags

Do not commit real outputs produced by this script.
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


CORE_FILE_NAME = "investigator_ftldlbd_nacc70.csv"
MISSING_CODES = {"", "-4", "-7", "-8", "-9", "8", "88", "888", "9", "99", "999"}
DEMENTIA_CODES = {"4"}
REQUIRED_COLUMNS = [
    "NACCID",
    "NACCVNUM",
    "VISITMO",
    "VISITDAY",
    "VISITYR",
    "NACCAGE",
    "NACCUDSD",
    "NACCNE4S",
    "NACCMMSE",
]
OPTIONAL_COLUMNS = ["SEX", "EDUC", "CDRGLOB", "CDRSUM", "PACKET", "FORMVER", "NACCDIED", "NACCAVST", "NACCFDYS"]


@dataclass(frozen=True)
class Stage:
    stage: str
    n: int
    excluded_at_stage: int


def detect_dialect(path: Path) -> csv.Dialect:
    sample = path.read_text(encoding="utf-8-sig", errors="replace")[:8192]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t")
    except csv.Error:
        return csv.excel_tab if path.suffix.lower() == ".tsv" else csv.excel


def has_value(value: object) -> bool:
    return str(value).strip() not in MISSING_CODES


def as_int(value: object) -> int | None:
    if not has_value(value):
        return None
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return None


def visit_date(row: dict[str, str]) -> date | None:
    month = as_int(row.get("VISITMO", ""))
    day = as_int(row.get("VISITDAY", ""))
    year = as_int(row.get("VISITYR", ""))
    if month is None or day is None or year is None:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_blocker(output_dir: Path, blockers: list[str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Real NACC Guarded Pilot Blocker Report",
        "",
        "No cohort construction was performed.",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {blocker}" for blocker in blockers)
    (output_dir / "pilot_blocker_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "0.15.1",
        "stage": "real_nacc_guarded_prediction_pilot",
        "cohort_construction_performed": False,
        "blockers": blockers,
    }
    (output_dir / "pilot_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def preflight(core_file: Path, allow_real_data: bool, approved_pilot_rules: bool) -> list[str]:
    blockers = []
    if not allow_real_data:
        blockers.append("Missing --allow-real-data; refusing patient-level real NACC execution.")
    if not approved_pilot_rules:
        blockers.append("Missing --approved-pilot-rules; user has not approved the conservative pilot rules.")
    if core_file.name != CORE_FILE_NAME:
        blockers.append(f"Core file must be exactly {CORE_FILE_NAME}; got {core_file.name}.")
    if not core_file.exists():
        blockers.append(f"Core file does not exist: {core_file}")
        return blockers
    with core_file.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.reader(handle, dialect=detect_dialect(core_file))
        headers = next(reader, [])
    header_set = {header.upper() for header in headers}
    missing = [column for column in REQUIRED_COLUMNS if column not in header_set]
    if missing:
        blockers.append(f"Missing required columns: {missing}")
    return blockers


def load_selected_rows(core_file: Path) -> tuple[dict[str, list[dict[str, str]]], dict[str, int]]:
    selected = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
    rows_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    stats = {"rows_read": 0, "rows_with_missing_id": 0}
    with core_file.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle, dialect=detect_dialect(core_file))
        for row in reader:
            stats["rows_read"] += 1
            naccid = row.get("NACCID", "")
            if not has_value(naccid):
                stats["rows_with_missing_id"] += 1
                continue
            kept = {field: row.get(field, "") for field in selected}
            rows_by_id[naccid].append(kept)
    return rows_by_id, stats


def choose_index_visit(visits: list[dict[str, str]]) -> dict[str, str] | None:
    dated = [(visit_date(row), as_int(row.get("NACCVNUM", "")), row) for row in visits]
    dated = [(dt, visit_num, row) for dt, visit_num, row in dated if dt is not None and visit_num is not None]
    if not dated:
        return None
    return min(dated, key=lambda item: (item[0], item[1]))[2]


def post_index_outcome(visits: list[dict[str, str]], index: dict[str, str]) -> dict[str, str] | None:
    index_date = visit_date(index)
    if index_date is None:
        return None
    candidates = []
    for row in visits:
        dt = visit_date(row)
        if dt is not None and dt > index_date and has_value(row.get("NACCMMSE", "")):
            candidates.append((dt, as_int(row.get("NACCVNUM", "")) or 999999, row))
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


def run(core_file: Path, output_dir: Path, allow_real_data: bool, approved_pilot_rules: bool) -> int:
    blockers = preflight(core_file, allow_real_data, approved_pilot_rules)
    if blockers:
        write_blocker(output_dir, blockers)
        print("Blocked real NACC pilot. See pilot_blocker_report.md.")
        return 2

    rows_by_id, load_stats = load_selected_rows(core_file)
    candidate_ids = set(rows_by_id)
    attrition: list[Stage] = [Stage("all_unique_participants", len(candidate_ids), 0)]

    def apply(stage: str, ids: set[str], predicate) -> set[str]:
        kept = {pid for pid in ids if predicate(pid)}
        attrition.append(Stage(stage, len(kept), len(ids) - len(kept)))
        return kept

    index_by_id = {pid: choose_index_visit(visits) for pid, visits in rows_by_id.items()}
    ids = apply("has_valid_index_visit", candidate_ids, lambda pid: index_by_id[pid] is not None)
    ids = apply("baseline_age_eligible", ids, lambda pid: (as_int(index_by_id[pid].get("NACCAGE", "")) or -1) >= 65)  # type: ignore[union-attr]
    ids = apply("baseline_cognitive_status_available", ids, lambda pid: has_value(index_by_id[pid].get("NACCUDSD", "")))  # type: ignore[union-attr]
    ids = apply("baseline_dementia_free", ids, lambda pid: str(index_by_id[pid].get("NACCUDSD", "")).strip() not in DEMENTIA_CODES)  # type: ignore[union-attr]
    ids = apply("apoe_available", ids, lambda pid: has_value(index_by_id[pid].get("NACCNE4S", "")))  # type: ignore[union-attr]
    ids = apply("baseline_mmse_available", ids, lambda pid: has_value(index_by_id[pid].get("NACCMMSE", "")))  # type: ignore[union-attr]
    outcome_by_id = {pid: post_index_outcome(rows_by_id[pid], index_by_id[pid]) for pid in ids}  # type: ignore[arg-type]
    ids = apply("has_post_index_mmse_outcome", ids, lambda pid: outcome_by_id[pid] is not None)

    cohort_index = []
    feature_rows = []
    outcome_rows = []
    cohort_rows = []
    for pid in sorted(ids):
        index = index_by_id[pid]
        outcome = outcome_by_id[pid]
        assert index is not None and outcome is not None
        index_date = visit_date(index)
        outcome_date = visit_date(outcome)
        assert index_date is not None and outcome_date is not None
        baseline_mmse = as_int(index["NACCMMSE"])
        outcome_mmse = as_int(outcome["NACCMMSE"])
        assert baseline_mmse is not None and outcome_mmse is not None
        mmse_change = outcome_mmse - baseline_mmse
        decline_label = 1 if mmse_change <= -1 else 0
        cohort_index.append(
            {
                "NACCID": pid,
                "index_NACCVNUM": index["NACCVNUM"],
                "index_visit_date": index_date.isoformat(),
                "outcome_NACCVNUM": outcome["NACCVNUM"],
                "outcome_visit_date": outcome_date.isoformat(),
            }
        )
        feature_rows.append(
            {
                "NACCID": pid,
                "index_visit_date": index_date.isoformat(),
                "baseline_NACCAGE": index["NACCAGE"],
                "SEX": index.get("SEX", ""),
                "EDUC": index.get("EDUC", ""),
                "NACCNE4S": index.get("NACCNE4S", ""),
                "baseline_NACCUDSD": index["NACCUDSD"],
                "baseline_CDRGLOB": index.get("CDRGLOB", ""),
                "baseline_CDRSUM": index.get("CDRSUM", ""),
                "baseline_NACCMMSE": index["NACCMMSE"],
                "baseline_UDSVER": index.get("FORMVER", "") or index.get("PACKET", ""),
            }
        )
        outcome_rows.append(
            {
                "NACCID": pid,
                "index_visit_date": index_date.isoformat(),
                "outcome_visit_date": outcome_date.isoformat(),
                "outcome_NACCMMSE": outcome["NACCMMSE"],
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
    write_reports(output_dir, core_file, rows_by_id, load_stats, cohort_rows)
    subprocess.run([sys.executable, str(Path(__file__).with_name("run_acceptance_checks.py")), str(output_dir)], capture_output=True, text=True, check=False)
    write_privacy_notice(output_dir)
    print(f"Real NACC guarded prediction pilot wrote local outputs to {output_dir}")
    print("Do not commit this output directory.")
    return 0


def write_reports(
    output_dir: Path,
    core_file: Path,
    rows_by_id: dict[str, list[dict[str, str]]],
    load_stats: dict[str, int],
    cohort_rows: list[dict[str, object]],
) -> None:
    all_visits = [row for rows in rows_by_id.values() for row in rows]
    duplicate_pairs = sum(1 for count in Counter((row["NACCID"], row["NACCVNUM"]) for row in all_visits).values() if count > 1)
    missing_apoe_baseline = sum(1 for rows in rows_by_id.values() if (idx := choose_index_visit(rows)) is not None and not has_value(idx.get("NACCNE4S", "")))
    missing_mmse_rows = sum(1 for row in all_visits if not has_value(row.get("NACCMMSE", "")))
    baseline_versions = Counter(str(row.get("baseline_UDSVER", "")) for row in cohort_rows)
    label_counts = Counter(str(row.get("cognitive_decline_label", "")) for row in cohort_rows)
    dq = [
        "# Real NACC Guarded Prediction Pilot Data Quality Report",
        "",
        f"- Core file: `{core_file.name}`",
        f"- Rows read: {load_stats['rows_read']}",
        f"- Unique participants loaded: {len(rows_by_id)}",
        f"- Included participants: {len(cohort_rows)}",
        f"- Duplicate participant-visit pairs in selected core fields: {duplicate_pairs}",
        f"- Baseline visits with missing APOE e4 count among loaded participants: {missing_apoe_baseline}",
        f"- Visit rows with missing-like MMSE: {missing_mmse_rows}",
        f"- Baseline form/version context counts in included cohort: {dict(baseline_versions)}",
        f"- Cognitive decline label counts: {dict(label_counts)}",
    ]
    (output_dir / "data_quality_report.md").write_text("\n".join(dq) + "\n", encoding="utf-8")
    leakage = [
        "# Real NACC Guarded Prediction Pilot Leakage Report",
        "",
        "## Deterministic Temporal Checks",
        "",
        "- Outcome visit is required to occur after index visit.",
        "- Feature table uses index-visit or time-invariant fields only.",
        "",
        "## Design Warnings",
        "",
        "- This pilot uses a conservative rule: baseline dementia-free is NACCUDSD not equal to dementia code 4.",
        "- Missing-code and field semantics still require local NACC dictionary confirmation before freezing a scientific cohort.",
        "- APOE availability restriction may induce selection bias.",
        "- Requiring post-index MMSE follow-up conditions on future observation and should be described as outcome ascertainment.",
    ]
    (output_dir / "leakage_report.md").write_text("\n".join(leakage) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "0.15.1",
        "created_by": "dementia-causal-cohort-auditor",
        "data_source": "real_nacc_guarded_prediction",
        "cohort_task": "prediction_cognitive_decline",
        "core_file_name": core_file.name,
        "patient_level_output": True,
        "git_commit_allowed_for_outputs": False,
        "rules": {
            "time_zero": "first valid visit in the core NACC table",
            "baseline_window": "index visit only",
            "age_rule": "baseline NACCAGE >= 65",
            "baseline_dementia_rule": "baseline NACCUDSD not equal to 4",
            "apoe_rule": "baseline NACCNE4S not in missing-like codes",
            "outcome_rule": "last post-index visit with non-missing NACCMMSE; decline label is MMSE change <= -1",
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
            "privacy_notice.md",
        ],
    }
    (output_dir / "reproducibility_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def write_privacy_notice(output_dir: Path) -> None:
    notice = [
        "# Privacy Notice",
        "",
        "This directory contains real NACC-derived patient-level cohort files.",
        "",
        "- Do not commit this directory.",
        "- Do not paste patient rows or NACCID values into chat.",
        "- Summarize only aggregate counts and acceptance status.",
    ]
    (output_dir / "privacy_notice.md").write_text("\n".join(notice) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run guarded real NACC prediction/cognitive-decline pilot.")
    parser.add_argument("--core-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--allow-real-data", action="store_true")
    parser.add_argument("--approved-pilot-rules", action="store_true")
    args = parser.parse_args()
    return run(args.core_file, args.output_dir, args.allow_real_data, args.approved_pilot_rules)


if __name__ == "__main__":
    raise SystemExit(main())
