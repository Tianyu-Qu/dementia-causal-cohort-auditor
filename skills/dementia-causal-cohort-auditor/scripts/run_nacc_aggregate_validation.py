#!/usr/bin/env python
"""Run aggregate-only validation for a proposed NACC cohort design.

This v0.13 script may read real NACC CSV/TSV data, but it only writes
aggregate summaries. It must not emit NACCID values, patient rows, or a cohort.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


MISSING_LIKE = {"", "-4", "-7", "-8", "-9", "8", "88", "888", "9", "99", "999"}
ID_FIELDS = {"NACCID"}
KEY_FIELD_CANDIDATES = {
    "participant_id": ["NACCID"],
    "visit_id": ["NACCVNUM"],
    "visit_date": ["VISITMO", "VISITDAY", "VISITYR"],
    "age_at_visit": ["NACCAGE"],
    "sex": ["SEX"],
    "education": ["EDUC"],
    "apoe": ["NACCNE4S", "NACCAPOE", "APOE", "APOE4"],
    "baseline_cognitive_status": ["NACCUDSD", "DEMENTED", "CDRGLOB"],
    "cognitive_score": ["NACCMMSE", "NACCMOCA", "MMSE", "MOCA"],
    "cdr_global": ["CDRGLOB"],
    "cdr_sum": ["CDRSUM"],
    "follow_up_context": ["NACCDIED", "NACCDAYS", "NACCFDYS", "NACCAVST", "DROPACT"],
    "form_version_context": ["PACKET", "FORMVER", "UDSVER", "NACCFORM", "NPFORMVER", "FTLDFORMVER", "LBDFORMVER"],
}


def detect_dialect(path: Path) -> csv.Dialect:
    sample = path.read_text(encoding="utf-8-sig", errors="replace")[:8192]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t")
    except csv.Error:
        return csv.excel_tab if path.suffix.lower() == ".tsv" else csv.excel


def iter_tables(input_dir: Path) -> Iterable[Path]:
    for pattern in ("*.csv", "*.tsv"):
        yield from sorted(input_dir.rglob(pattern))


def read_headers(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.reader(handle, dialect=detect_dialect(path))
        return next(reader, [])


def choose_core_file(input_dir: Path, explicit_core_file: str | None) -> Path:
    if explicit_core_file:
        core = Path(explicit_core_file)
        if not core.exists():
            raise FileNotFoundError(f"Core file does not exist: {core}")
        return core

    candidates: list[tuple[int, int, Path]] = []
    for path in iter_tables(input_dir):
        headers = {header.upper() for header in read_headers(path)}
        score = 0
        for required in ("NACCID", "NACCVNUM"):
            score += 20 if required in headers else 0
        for helpful in ("VISITYR", "VISITMO", "VISITDAY", "NACCAGE", "NACCUDSD", "NACCMMSE", "NACCMOCA"):
            score += 5 if helpful in headers else 0
        score += min(len(headers), 2500) // 100
        if score > 0:
            candidates.append((score, len(headers), path))
    if not candidates:
        raise FileNotFoundError(f"No CSV/TSV table with NACC-like headers found under {input_dir}")
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return candidates[0][2]


def upper_map(headers: list[str]) -> dict[str, str]:
    return {header.upper(): header for header in headers}


def first_present(headers: dict[str, str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate.upper() in headers:
            return headers[candidate.upper()]
    return None


def present_fields(headers: dict[str, str], candidates: list[str]) -> list[str]:
    return [headers[candidate.upper()] for candidate in candidates if candidate.upper() in headers]


def is_missing_like(value: object) -> bool:
    return str(value).strip() in MISSING_LIKE


def as_float(value: object) -> float | None:
    try:
        if is_missing_like(value):
            return None
        return float(str(value).strip())
    except ValueError:
        return None


def visit_sort_value(row: dict[str, str], visit_field: str | None, year_field: str | None) -> tuple[float, float]:
    visit = as_float(row.get(visit_field or "", "")) if visit_field else None
    year = as_float(row.get(year_field or "", "")) if year_field else None
    return (visit if visit is not None else 1_000_000.0, year if year is not None else 1_000_000.0)


def safe_counter(counter: Counter[str], limit: int = 8) -> str:
    pairs = []
    for value, count in counter.most_common(limit):
        display = "<missing-like>" if is_missing_like(value) else str(value)
        pairs.append(f"{display}:{count}")
    return "; ".join(pairs)


def summarize_numeric(values: list[float]) -> dict[str, object]:
    if not values:
        return {"count": 0, "min": None, "median": None, "max": None}
    return {
        "count": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }


def scan_core_table(path: Path) -> dict[str, object]:
    dialect = detect_dialect(path)
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        headers = reader.fieldnames or []
        header_lookup = upper_map(headers)

        selected: dict[str, list[str]] = {
            concept: present_fields(header_lookup, candidates)
            for concept, candidates in KEY_FIELD_CANDIDATES.items()
        }
        participant_field = first_present(header_lookup, KEY_FIELD_CANDIDATES["participant_id"])
        visit_field = first_present(header_lookup, KEY_FIELD_CANDIDATES["visit_id"])
        year_field = first_present(header_lookup, ["VISITYR"])
        age_field = first_present(header_lookup, KEY_FIELD_CANDIDATES["age_at_visit"])
        apoe_field = first_present(header_lookup, KEY_FIELD_CANDIDATES["apoe"])
        dementia_field = first_present(header_lookup, ["NACCUDSD", "DEMENTED", "CDRGLOB"])
        form_fields = present_fields(header_lookup, KEY_FIELD_CANDIDATES["form_version_context"])

        key_fields = sorted(
            {
                field
                for fields in selected.values()
                for field in fields
                if field.upper() not in ID_FIELDS
            }
        )
        field_stats = {
            field: {"missing_like": 0, "non_missing": 0, "distinct": set(), "top": Counter()}
            for field in key_fields
        }
        missing_by_form: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))

        row_count = 0
        participant_visit_counts: Counter[str] = Counter()
        duplicate_pair_count = 0
        seen_pairs: set[tuple[str, str]] = set()
        baseline_by_pid: dict[str, dict[str, str]] = {}
        baseline_order_by_pid: dict[str, tuple[float, float]] = {}
        numeric_age_values: list[float] = []

        for row in reader:
            row_count += 1

            for field in key_fields:
                value = row.get(field, "")
                if is_missing_like(value):
                    field_stats[field]["missing_like"] += 1  # type: ignore[index]
                else:
                    field_stats[field]["non_missing"] += 1  # type: ignore[index]
                    field_stats[field]["distinct"].add(value)  # type: ignore[index]
                    field_stats[field]["top"][str(value)] += 1  # type: ignore[index]

            if age_field:
                age = as_float(row.get(age_field, ""))
                if age is not None:
                    numeric_age_values.append(age)

            form_value = first_non_missing(row, form_fields)
            if form_value is not None:
                for field in key_fields:
                    missing_by_form[(str(form_value), field)]["rows"] += 1
                    if is_missing_like(row.get(field, "")):
                        missing_by_form[(str(form_value), field)]["missing_like"] += 1

            if participant_field:
                pid = row.get(participant_field, "")
                if not is_missing_like(pid):
                    participant_visit_counts[pid] += 1
                    order = visit_sort_value(row, visit_field, year_field)
                    if pid not in baseline_order_by_pid or order < baseline_order_by_pid[pid]:
                        baseline_order_by_pid[pid] = order
                        baseline_by_pid[pid] = {
                            "age": row.get(age_field, "") if age_field else "",
                            "apoe": row.get(apoe_field, "") if apoe_field else "",
                            "dementia": row.get(dementia_field, "") if dementia_field else "",
                        }
                    if visit_field:
                        pair = (pid, row.get(visit_field, ""))
                        if pair in seen_pairs:
                            duplicate_pair_count += 1
                        else:
                            seen_pairs.add(pair)

    participants = len(participant_visit_counts)
    visit_counts = list(participant_visit_counts.values())
    baseline_rows = list(baseline_by_pid.values())
    baseline_age_ge_65 = sum(1 for row in baseline_rows if (as_float(row.get("age", "")) or -1) >= 65)
    baseline_apoe_available = sum(1 for row in baseline_rows if not is_missing_like(row.get("apoe", "")))
    baseline_status_available = sum(1 for row in baseline_rows if not is_missing_like(row.get("dementia", "")))

    return {
        "core_file": str(path),
        "headers": headers,
        "selected_fields": selected,
        "row_count": row_count,
        "participant_count": participants,
        "participants_with_at_least_2_visits": sum(1 for count in visit_counts if count >= 2),
        "visit_count_summary": summarize_numeric([float(count) for count in visit_counts]),
        "duplicate_participant_visit_pairs": duplicate_pair_count,
        "age_summary_all_rows": summarize_numeric(numeric_age_values),
        "baseline_age_ge_65": baseline_age_ge_65,
        "baseline_apoe_available": baseline_apoe_available,
        "baseline_cognitive_status_available": baseline_status_available,
        "baseline_participant_ids": set(baseline_by_pid.keys()),
        "field_stats": field_stats,
        "missing_by_form": missing_by_form,
        "form_fields": form_fields,
        "auxiliary_evidence": [],
    }


def enrich_with_auxiliary_participant_tables(input_dir: Path, core_file: Path, scan: dict[str, object]) -> None:
    """Add aggregate evidence from participant-level side tables.

    This does not emit IDs or row-level joins. It only uses participant IDs in
    memory to count whether baseline participants have auxiliary concepts such
    as APOE, sex, or education available.
    """

    baseline_ids = scan.get("baseline_participant_ids", set())
    if not isinstance(baseline_ids, set) or not baseline_ids:
        return

    selected = scan["selected_fields"]  # type: ignore[assignment]
    field_stats = scan["field_stats"]  # type: ignore[assignment]
    auxiliary_evidence: list[str] = scan["auxiliary_evidence"]  # type: ignore[assignment]

    participant_concepts = {
        "apoe": KEY_FIELD_CANDIDATES["apoe"],
        "sex": KEY_FIELD_CANDIDATES["sex"],
        "education": KEY_FIELD_CANDIDATES["education"],
    }

    for path in iter_tables(input_dir):
        if path.resolve() == core_file.resolve():
            continue
        headers = read_headers(path)
        header_lookup = upper_map(headers)
        id_field = first_present(header_lookup, KEY_FIELD_CANDIDATES["participant_id"])
        if not id_field:
            continue
        present_concepts = {
            concept: first_present(header_lookup, candidates)
            for concept, candidates in participant_concepts.items()
        }
        present_concepts = {concept: field for concept, field in present_concepts.items() if field}
        if not present_concepts:
            continue

        dialect = detect_dialect(path)
        stats_by_concept = {
            concept: {"missing_like": 0, "non_missing": 0, "distinct": set(), "top": Counter(), "baseline_available": 0}
            for concept in present_concepts
        }
        seen_for_concept: dict[str, set[str]] = {concept: set() for concept in present_concepts}

        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            reader = csv.DictReader(handle, dialect=dialect)
            for row in reader:
                pid = row.get(id_field, "")
                if pid not in baseline_ids:
                    continue
                for concept, field in present_concepts.items():
                    value = row.get(field or "", "")
                    if is_missing_like(value):
                        stats_by_concept[concept]["missing_like"] += 1  # type: ignore[index]
                    else:
                        stats_by_concept[concept]["non_missing"] += 1  # type: ignore[index]
                        stats_by_concept[concept]["distinct"].add(value)  # type: ignore[index]
                        stats_by_concept[concept]["top"][str(value)] += 1  # type: ignore[index]
                        if pid not in seen_for_concept[concept]:
                            stats_by_concept[concept]["baseline_available"] += 1  # type: ignore[index]
                            seen_for_concept[concept].add(pid)

        for concept, field in present_concepts.items():
            qualified_field = f"{path.name}::{field}"
            if not selected.get(concept):  # type: ignore[union-attr]
                selected[concept] = [qualified_field]  # type: ignore[index]
            field_stats[qualified_field] = stats_by_concept[concept]  # type: ignore[index]
            auxiliary_evidence.append(f"{concept}: {qualified_field}")
            if concept == "apoe" and scan.get("baseline_apoe_available", 0) == 0:
                scan["baseline_apoe_available"] = stats_by_concept[concept]["baseline_available"]


def first_non_missing(row: dict[str, str], fields: list[str]) -> str | None:
    for field in fields:
        value = row.get(field, "")
        if not is_missing_like(value):
            return f"{field}={value}"
    return None


def write_field_summary(scan: dict[str, object], output_dir: Path) -> None:
    path = output_dir / "field_distribution_summary.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["concept", "field", "present", "non_missing_count", "missing_like_count", "unique_count", "top_values"],
        )
        writer.writeheader()
        selected = scan["selected_fields"]  # type: ignore[assignment]
        field_stats = scan["field_stats"]  # type: ignore[assignment]
        for concept, fields in selected.items():  # type: ignore[union-attr]
            if not fields:
                writer.writerow(
                    {
                        "concept": concept,
                        "field": "",
                        "present": "false",
                        "non_missing_count": 0,
                        "missing_like_count": 0,
                        "unique_count": 0,
                        "top_values": "",
                    }
                )
            for field in fields:
                if field.upper() in ID_FIELDS:
                    writer.writerow(
                        {
                            "concept": concept,
                            "field": field,
                            "present": "true",
                            "non_missing_count": "suppressed_identifier_field",
                            "missing_like_count": "suppressed_identifier_field",
                            "unique_count": "suppressed_identifier_field",
                            "top_values": "suppressed_identifier_field",
                        }
                    )
                    continue
                stats = field_stats.get(field, {})  # type: ignore[union-attr]
                writer.writerow(
                    {
                        "concept": concept,
                        "field": field,
                        "present": "true",
                        "non_missing_count": stats.get("non_missing", 0),
                        "missing_like_count": stats.get("missing_like", 0),
                        "unique_count": len(stats.get("distinct", set())),
                        "top_values": safe_counter(stats.get("top", Counter())),
                    }
                )


def write_missingness_by_form(scan: dict[str, object], output_dir: Path) -> None:
    path = output_dir / "missingness_by_form_version.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["form_context", "field", "rows", "missing_like_count", "missing_like_rate"])
        writer.writeheader()
        for (form_value, field), stats in sorted(scan["missing_by_form"].items()):  # type: ignore[union-attr]
            rows = stats.get("rows", 0)
            missing = stats.get("missing_like", 0)
            writer.writerow(
                {
                    "form_context": form_value,
                    "field": field,
                    "rows": rows,
                    "missing_like_count": missing,
                    "missing_like_rate": round(missing / rows, 4) if rows else "",
                }
            )


def write_visit_report(scan: dict[str, object], output_dir: Path) -> None:
    summary = scan["visit_count_summary"]  # type: ignore[assignment]
    lines = [
        "# NACC Aggregate Visit Structure Report",
        "",
        "This report is aggregate-only. It does not list NACCID values or patient rows.",
        "",
        f"- Core table: `{Path(str(scan['core_file'])).name}`",
        f"- Total rows: {scan['row_count']}",
        f"- Unique participants: {scan['participant_count']}",
        f"- Participants with >=2 visits: {scan['participants_with_at_least_2_visits']}",
        f"- Duplicate participant-visit pairs: {scan['duplicate_participant_visit_pairs']}",
        f"- Visit count min/median/max: {summary['min']} / {summary['median']} / {summary['max']}",
        "",
        "Interpretation: these counts can support design review and attrition planning, but they are not a cohort output.",
    ]
    (output_dir / "visit_structure_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def readiness(scan: dict[str, object]) -> tuple[str, list[str], list[str]]:
    selected = scan["selected_fields"]  # type: ignore[assignment]
    blockers = []
    warnings = []
    required = [
        "participant_id",
        "visit_id",
        "visit_date",
        "age_at_visit",
        "apoe",
        "baseline_cognitive_status",
        "cognitive_score",
    ]
    for concept in required:
        if not selected.get(concept):  # type: ignore[union-attr]
            blockers.append(f"Missing aggregate-validation concept: {concept}")
    if scan["participants_with_at_least_2_visits"] == 0:
        blockers.append("No participants with at least two visits were detected.")
    if scan["baseline_apoe_available"] == 0:
        blockers.append("No baseline APOE availability detected.")
    if not selected.get("form_version_context"):  # type: ignore[union-attr]
        warnings.append("No UDS/form-version context detected; structural missingness cannot be stratified.")
    if not selected.get("follow_up_context"):  # type: ignore[union-attr]
        warnings.append("No death/follow-up context detected; dropout/censoring handling remains unresolved.")
    if blockers:
        return "not_ready", blockers, warnings
    return "aggregate_supported_pending_design_approval", blockers, warnings


def write_aggregate_report(scan: dict[str, object], output_dir: Path, real_data_mode: bool) -> None:
    status, blockers, warnings = readiness(scan)
    age_summary = scan["age_summary_all_rows"]  # type: ignore[assignment]
    lines = [
        "# NACC Aggregate Validation Report",
        "",
        f"- Status: {status}",
        f"- Real data mode: {str(real_data_mode).lower()}",
        "- Patient-level output: no",
        "- Cohort construction performed: no",
        "- Ready for cohort construction: false",
        "",
        "## Aggregate Evidence",
        "",
        f"- Core table: `{Path(str(scan['core_file'])).name}`",
        f"- Total rows scanned: {scan['row_count']}",
        f"- Unique participants: {scan['participant_count']}",
        f"- Participants with >=2 visits: {scan['participants_with_at_least_2_visits']}",
        f"- Duplicate participant-visit pairs: {scan['duplicate_participant_visit_pairs']}",
        f"- All-row age min/median/max: {age_summary['min']} / {age_summary['median']} / {age_summary['max']}",
        f"- Baseline age >=65 count: {scan['baseline_age_ge_65']}",
        f"- Baseline APOE available count: {scan['baseline_apoe_available']}",
        f"- Baseline cognitive-status available count: {scan['baseline_cognitive_status_available']}",
        "",
        "## Field Evidence",
        "",
    ]
    selected = scan["selected_fields"]  # type: ignore[assignment]
    for concept, fields in selected.items():  # type: ignore[union-attr]
        value = ", ".join(fields) if fields else "missing"
        lines.append(f"- {concept}: {value}")
    if scan.get("auxiliary_evidence"):
        lines.extend(["", "## Auxiliary Participant-Level Evidence", ""])
        lines.extend(f"- {item}" for item in scan["auxiliary_evidence"])  # type: ignore[index]
    lines.extend(["", "## Blockers", ""])
    if blockers:
        lines.extend(f"- {blocker}" for blocker in blockers)
    else:
        lines.append("- No aggregate-only blockers detected for moving to design refinement/approval.")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- None from aggregate validation.")
    lines.extend(
        [
            "",
            "## Gate",
            "",
            "Aggregate validation can support human design approval, but it must not approve cohort construction by itself. Proceed only after field definitions, missing-code rules, outcome definition, time zero, and follow-up rules are approved.",
        ]
    )
    (output_dir / "aggregate_validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_privacy_report(output_dir: Path) -> None:
    leaks = []
    for path in output_dir.glob("*"):
        if path.suffix.lower() not in {".md", ".csv", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"\bN\d{3,}\b", text):
            leaks.append(path.name)
    lines = [
        "# Privacy Check Report",
        "",
        "- Patient rows emitted: no",
        "- NACCID values emitted: no" if not leaks else f"- Potential leaks: {', '.join(leaks)}",
        "- Identifier fields are summarized only as counts or suppressed in distribution tables.",
    ]
    (output_dir / "privacy_check_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manifest(scan: dict[str, object], output_dir: Path, real_data_mode: bool) -> None:
    status, blockers, warnings = readiness(scan)
    manifest = {
        "schema_version": "0.13",
        "stage": "nacc_aggregate_validation",
        "real_data_mode": real_data_mode,
        "core_file_name": Path(str(scan["core_file"])).name,
        "row_count": scan["row_count"],
        "participant_count": scan["participant_count"],
        "status": status,
        "ready_for_cohort_construction": False,
        "blockers": blockers,
        "warnings": warnings,
        "outputs": [
            "aggregate_validation_report.md",
            "field_distribution_summary.csv",
            "missingness_by_form_version.csv",
            "visit_structure_report.md",
            "privacy_check_report.md",
        ],
    }
    (output_dir / "aggregate_validation_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run(input_dir: Path, output_dir: Path, core_file: str | None, real_data_mode: bool) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_core = choose_core_file(input_dir, core_file)
    scan = scan_core_table(selected_core)
    enrich_with_auxiliary_participant_tables(input_dir, selected_core, scan)
    write_field_summary(scan, output_dir)
    write_missingness_by_form(scan, output_dir)
    write_visit_report(scan, output_dir)
    write_aggregate_report(scan, output_dir, real_data_mode)
    write_manifest(scan, output_dir, real_data_mode)
    write_privacy_report(output_dir)
    return selected_core


def main() -> int:
    parser = argparse.ArgumentParser(description="Run aggregate-only validation for NACC cohort design readiness.")
    parser.add_argument("--input-dir", required=True, help="Directory containing selected NACC CSV/TSV files.")
    parser.add_argument("--output-dir", required=True, help="Directory for aggregate-only validation outputs.")
    parser.add_argument("--core-file", help="Optional explicit core clinical/UDS CSV/TSV file.")
    parser.add_argument("--design-packet-dir", help="Optional v0.12 design packet directory; reserved for audit traceability.")
    parser.add_argument("--real-data-mode", action="store_true", help="Mark outputs as real-data aggregate validation.")
    args = parser.parse_args()

    _ = args.design_packet_dir
    core = run(Path(args.input_dir), Path(args.output_dir), args.core_file, args.real_data_mode)
    print(f"Aggregate validation complete. Core file: {core}")
    print(f"Outputs: {Path(args.output_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
