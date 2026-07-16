#!/usr/bin/env python
"""Read-only NACC folder/header dry-run scanner."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


MISSING_CODES = {"", "-4", "8", "88", "9", "99"}

CONCEPTS = [
    {"id": "participant_id", "label": "Participant identifier", "required": True, "candidates": ["NACCID"]},
    {"id": "center_id", "label": "Center identifier", "required": False, "candidates": ["NACCADC"]},
    {"id": "visit_id", "label": "Visit order/number", "required": True, "candidates": ["NACCVNUM"]},
    {"id": "visit_date", "label": "Visit date components", "required": True, "candidates": ["VISITMO", "VISITDAY", "VISITYR"]},
    {"id": "age_at_visit", "label": "Age at visit", "required": True, "candidates": ["NACCAGE"]},
    {"id": "sex", "label": "Sex", "required": True, "candidates": ["SEX"]},
    {"id": "education", "label": "Education", "required": False, "candidates": ["EDUC"]},
    {"id": "apoe", "label": "APOE genotype/e4 count", "required": True, "candidates": ["NACCNE4S", "APOE", "APOE4", "NACCAPOE"]},
    {"id": "cognitive_status", "label": "Cognitive status", "required": True, "candidates": ["NACCUDSD"]},
    {"id": "cdr_global", "label": "Global CDR", "required": False, "candidates": ["CDRGLOB"]},
    {"id": "cdr_sum", "label": "CDR sum of boxes", "required": False, "candidates": ["CDRSUM"]},
    {"id": "cognitive_score", "label": "Cognitive score", "required": True, "candidates": ["NACCMMSE", "MMSE", "NACCMOCA", "MOCA"]},
    {"id": "medication_exposure", "label": "Medication/exposure", "required": True, "candidates": ["DRUGNAME", "DRUGID", "MEDICATION", "CURRENT_USE"]},
    {"id": "medication_timing", "label": "Medication timing", "required": True, "candidates": ["DRUG_STARTMO", "DRUG_STARTYR", "STARTDATE"]},
    {"id": "death_dropout", "label": "Death/dropout/follow-up", "required": False, "candidates": ["DECEASED", "DROPOUT", "LAST_CONTACT_YR", "DEATH"]},
    {"id": "uds_version", "label": "UDS version", "required": True, "candidates": ["UDSVER", "NACCUDSV"]},
]


def detect_dialect(path: Path) -> csv.Dialect:
    sample = path.read_text(encoding="utf-8-sig", errors="replace")[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t")
    except csv.Error:
        return csv.excel_tab if path.suffix.lower() == ".tsv" else csv.excel


def read_rows(path: Path, sample_limit: int) -> tuple[list[str], list[dict[str, str]], int]:
    dialect = detect_dialect(path)
    row_count = 0
    samples: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        headers = reader.fieldnames or []
        for row in reader:
            row_count += 1
            if len(samples) < sample_limit:
                samples.append(row)
    return headers, samples, row_count


def scan_file(path: Path, sample_limit: int) -> dict[str, object]:
    headers, samples, row_count = read_rows(path, sample_limit)
    upper_headers = {header.upper(): header for header in headers}
    missing_counts: dict[str, int] = {}
    distinct_counts: dict[str, int] = {}
    distributions: dict[str, dict[str, int]] = {}
    for field in ["NACCID", "NACCVNUM", "UDSVER", "NACCUDSD", "NACCNE4S"]:
        if field in upper_headers:
            original = upper_headers[field]
            values = [row.get(original, "") for row in samples]
            missing_counts[field] = sum(1 for value in values if value in MISSING_CODES)
            distinct_counts[field] = len(set(values))
            if field == "NACCID":
                distributions[field] = {"unique_in_sample": distinct_counts[field], "missing_in_sample": missing_counts[field]}
            else:
                distributions[field] = dict(Counter(values).most_common(10))
    grain = infer_grain(upper_headers)
    return {
        "path": path,
        "name": path.name,
        "row_count": row_count,
        "column_count": len(headers),
        "headers": headers,
        "grain": grain,
        "missing_counts_sample": missing_counts,
        "distinct_counts_sample": distinct_counts,
        "distributions_sample": distributions,
    }


def infer_grain(headers: dict[str, str]) -> str:
    if "NACCID" in headers and "NACCVNUM" in headers:
        return "visit_or_longitudinal"
    if "NACCID" in headers:
        return "participant_or_module"
    return "unknown"


def concept_coverage(scans: list[dict[str, object]]) -> list[dict[str, object]]:
    field_locations: dict[str, list[str]] = defaultdict(list)
    for scan in scans:
        for header in scan["headers"]:  # type: ignore[index]
            field_locations[str(header).upper()].append(str(scan["name"]))
    coverage = []
    for concept in CONCEPTS:
        matches = []
        for candidate in concept["candidates"]:  # type: ignore[index]
            if candidate.upper() in field_locations:
                matches.append({"field": candidate.upper(), "files": sorted(set(field_locations[candidate.upper()]))})
        coverage.append(
            {
                "concept_id": concept["id"],
                "label": concept["label"],
                "required": concept["required"],
                "status": "candidate" if matches else "missing",
                "candidate_fields": matches,
            }
        )
    return coverage


def readiness(coverage: list[dict[str, object]]) -> tuple[str, list[str], list[str]]:
    missing_required = [str(item["concept_id"]) for item in coverage if item["required"] and item["status"] == "missing"]
    questions = [
        "Which NACC release, UDS versions, and modules are represented?",
        "Which cognitive status variable should define dementia-free baseline?",
        "Can medication fields support new-user design, washout, grace period, and lag windows?",
        "Which missing-value codes are structural versus ordinary missingness?",
        "Should follow-up availability be eligibility or outcome ascertainment?",
    ]
    if missing_required:
        status = "not_ready"
        blockers = [f"Missing required concept: {concept}" for concept in missing_required]
    else:
        status = "needs_human_confirmation"
        blockers = ["All required surface concepts are present, but human confirmation is required before execution."]
    return status, blockers, questions


def yaml_list(values: list[str], indent: int = 0) -> list[str]:
    prefix = " " * indent
    return [f"{prefix}- {value}" for value in values] if values else [f"{prefix}[]"]


def write_outputs(scans: list[dict[str, object]], coverage: list[dict[str, object]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    status, blockers, questions = readiness(coverage)
    write_inventory_csv(scans, output_dir / "nacc_file_inventory.csv")
    write_inventory_md(scans, output_dir / "nacc_file_inventory.md")
    write_coverage_yaml(coverage, output_dir / "nacc_concept_coverage.yaml")
    write_mapping_candidates_yaml(coverage, output_dir / "nacc_variable_mapping_candidates.yaml")
    write_readiness_report(status, blockers, coverage, output_dir / "nacc_readiness_report.md")
    write_questions(questions, blockers, output_dir / "unresolved_human_questions.md")


def write_inventory_csv(scans: list[dict[str, object]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        fields = ["file", "row_count", "column_count", "grain", "headers"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for scan in scans:
            writer.writerow(
                {
                    "file": scan["name"],
                    "row_count": scan["row_count"],
                    "column_count": scan["column_count"],
                    "grain": scan["grain"],
                    "headers": ";".join(scan["headers"]),  # type: ignore[arg-type]
                }
            )


def write_inventory_md(scans: list[dict[str, object]], path: Path) -> None:
    lines = ["# NACC File Inventory", "", "| File | Rows | Columns | Inferred grain | Key sample summaries |", "| --- | ---: | ---: | --- | --- |"]
    for scan in scans:
        summaries = []
        distributions = scan["distributions_sample"]  # type: ignore[assignment]
        for field, dist in distributions.items():  # type: ignore[union-attr]
            summaries.append(f"{field}: {dist}")
        lines.append(f"| {scan['name']} | {scan['row_count']} | {scan['column_count']} | {scan['grain']} | {'; '.join(summaries) or 'none'} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_coverage_yaml(coverage: list[dict[str, object]], path: Path) -> None:
    lines = ['schema_version: "0.6"', "concept_coverage:"]
    for item in coverage:
        lines.extend(
            [
                f"  - concept_id: {item['concept_id']}",
                f"    label: \"{item['label']}\"",
                f"    required: {str(item['required']).lower()}",
                f"    status: {item['status']}",
                "    candidate_fields:",
            ]
        )
        candidates = item["candidate_fields"]  # type: ignore[assignment]
        if candidates:
            for candidate in candidates:  # type: ignore[union-attr]
                lines.append(f"      - field: {candidate['field']}")
                lines.append("        files:")
                lines.extend(yaml_list(candidate["files"], 10))
        else:
            lines.append("      []")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_mapping_candidates_yaml(coverage: list[dict[str, object]], path: Path) -> None:
    lines = ['schema_version: "0.6"', "adapter: nacc", "mapping_candidates:"]
    for item in coverage:
        lines.extend(
            [
                f"  - concept_id: {item['concept_id']}",
                f"    required: {str(item['required']).lower()}",
                f"    status: {item['status']}",
                "    candidates:",
            ]
        )
        candidates = item["candidate_fields"]  # type: ignore[assignment]
        if candidates:
            for candidate in candidates:  # type: ignore[union-attr]
                lines.append(f"      - field: {candidate['field']}")
                lines.append("        evidence: header match in scanned files")
        else:
            lines.append("      []")
        lines.append("    selected_field: unresolved")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readiness_report(status: str, blockers: list[str], coverage: list[dict[str, object]], path: Path) -> None:
    missing = [str(item["concept_id"]) for item in coverage if item["status"] == "missing"]
    lines = [
        "# NACC Dry-Run Readiness Report",
        "",
        f"- Status: {status}",
        f"- Missing concepts: {', '.join(missing) if missing else 'none'}",
        "",
        "## Blockers / Gates",
        "",
        *(f"- {blocker}" for blocker in blockers),
        "",
        "## Recommendation",
        "",
        "Do not run cohort construction on real NACC data until required concepts, missing-code rules, UDS versions, medication timing, and cohort spec readiness are confirmed.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_questions(questions: list[str], blockers: list[str], path: Path) -> None:
    lines = ["# Unresolved Human Questions", "", "## Blocking Gates", ""]
    lines.extend(f"- {blocker}" for blocker in blockers)
    lines.extend(["", "## Questions", ""])
    lines.extend(f"- {question}" for question in questions)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample-rows", type=int, default=25)
    args = parser.parse_args()

    files = sorted([path for path in args.input_dir.iterdir() if path.suffix.lower() in {".csv", ".tsv"}])
    if not files:
        raise SystemExit(f"No CSV/TSV files found in {args.input_dir}")
    scans = [scan_file(path, args.sample_rows) for path in files]
    coverage = concept_coverage(scans)
    write_outputs(scans, coverage, args.output_dir)
    print(f"Wrote NACC dry-run outputs to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
