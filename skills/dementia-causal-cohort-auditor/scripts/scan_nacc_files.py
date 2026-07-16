#!/usr/bin/env python
"""Read-only NACC folder/header/sample dry-run scanner.

The scanner intentionally writes aggregate and metadata-only outputs. When
sample rows are provided, it summarizes missingness and value distributions but
does not emit row-level participant records.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


MISSING_CODES = {"", "-4", "8", "88", "9", "99"}
SENSITIVE_IDENTIFIER_FIELDS = {"NACCID"}

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
    {
        "id": "medication_records",
        "label": "Medication or ADRD treatment records (not causal-ready exposure)",
        "required": False,
        "candidates": ["DRUGNAME", "DRUGID", "MEDICATION", "CURRENT_USE", "A4", "A4A"],
    },
    {
        "id": "medication_temporality_support",
        "label": "Medication timing fields for constructing exposure windows",
        "required": False,
        "candidates": ["DRUG_STARTMO", "DRUG_STARTYR", "STARTDATE", "STOPDATE", "CURRENT_USE"],
    },
    {"id": "death_dropout", "label": "Death/dropout/follow-up", "required": False, "candidates": ["DECEASED", "DROPOUT", "LAST_CONTACT_YR", "DEATH"]},
    {"id": "uds_version", "label": "UDS version", "required": True, "candidates": ["UDSVER", "NACCUDSV"]},
]

TASK_PROFILES = {
    "dementia_classification": {
        "label": "Dementia or cognitive-status classification",
        "required": ["participant_id", "visit_id", "age_at_visit", "sex", "cognitive_status"],
        "recommended": ["education", "apoe", "cdr_global", "cdr_sum", "cognitive_score", "uds_version"],
        "note": "Best first real-data task because it mainly needs UDS visit records and diagnosis/status variables.",
    },
    "cognitive_decline_prediction": {
        "label": "Cognitive decline prediction",
        "required": ["participant_id", "visit_id", "visit_date", "age_at_visit", "cognitive_score", "cognitive_status"],
        "recommended": ["sex", "education", "apoe", "cdr_global", "cdr_sum", "death_dropout", "uds_version"],
        "note": "Needs longitudinal ordering and follow-up outcomes; two visits in a five-row sample prove structure, not adequacy.",
    },
    "trajectory_modeling": {
        "label": "Longitudinal trajectory modeling",
        "required": ["participant_id", "visit_id", "visit_date", "age_at_visit", "cognitive_score"],
        "recommended": ["cognitive_status", "cdr_global", "cdr_sum", "death_dropout", "uds_version"],
        "note": "Treat visit spacing, UDS version changes, and informative dropout as first-class design issues.",
    },
    "representation_learning": {
        "label": "Representation learning / feature pretraining",
        "required": ["participant_id", "visit_id"],
        "recommended": ["age_at_visit", "sex", "education", "cognitive_status", "cognitive_score", "cdr_global", "cdr_sum", "apoe"],
        "note": "Medication data is optional unless the representation is intended to support treatment-effect questions.",
    },
    "treatment_effect_estimation": {
        "label": "Treatment effect estimation",
        "required": [
            "participant_id",
            "visit_id",
            "visit_date",
            "age_at_visit",
            "cognitive_status",
            "cognitive_score",
            "medication_records",
            "medication_temporality_support",
        ],
        "recommended": ["sex", "education", "apoe", "cdr_global", "cdr_sum", "death_dropout", "uds_version"],
        "note": "NACC medication records are not automatically treatment exposure; new-user, comparator, washout, lag, and grace windows need human confirmation.",
    },
    "survival_progression": {
        "label": "Survival / progression analysis",
        "required": ["participant_id", "visit_id", "visit_date", "cognitive_status"],
        "recommended": ["death_dropout", "age_at_visit", "sex", "education", "apoe", "cdr_global", "cdr_sum", "uds_version"],
        "note": "Clarify whether death/dropout is a competing event, censoring process, or missing outcome mechanism.",
    },
}

GLOSSARY = {
    "NACCID": "Participant identifier. Treat as protected row-level information; reports should summarize it, not list values.",
    "NACCADC": "ADRC/center identifier. Useful for center effects, harmonization checks, and clustered validation.",
    "NACCVNUM": "Visit number/order. Useful for longitudinal ordering, but still verify date fields when time windows matter.",
    "VISITMO/VISITDAY/VISITYR": "Visit date components. Needed for baseline, index date, follow-up windows, and lag checks.",
    "NACCAGE": "Age at visit. Often the safest age anchor for visit-level cohort definitions.",
    "SEX": "Sex variable. Verify coding in the local dictionary before modeling.",
    "EDUC": "Years of education or education code. Common confounder/prognostic feature.",
    "NACCNE4S": "APOE e4 count/status candidate. Availability may be selective; do not silently restrict without attrition reporting.",
    "NACCUDSD": "Cognitive status / UDS diagnosis candidate. Confirm coding before defining dementia-free baseline.",
    "CDRGLOB": "Global Clinical Dementia Rating. Useful baseline severity/outcome feature.",
    "CDRSUM": "CDR sum of boxes. Useful severity/outcome feature.",
    "NACCMMSE": "MMSE-like cognitive score candidate. Check UDS version, language, missing codes, and comparability.",
    "UDSVER/NACCUDSV": "UDS version indicator. Important because structural missingness and form content change across versions.",
    "Medication records": "NACC may contain medication/treatment records, but these are not automatically causal exposure definitions.",
}


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
    for field in [
        "NACCID",
        "NACCVNUM",
        "VISITYR",
        "NACCAGE",
        "SEX",
        "UDSVER",
        "NACCUDSD",
        "NACCNE4S",
        "CDRGLOB",
        "CDRSUM",
        "NACCMMSE",
        "CURRENT_USE",
    ]:
        if field in upper_headers:
            original = upper_headers[field]
            values = [row.get(original, "") for row in samples]
            missing_counts[field] = sum(1 for value in values if value in MISSING_CODES)
            distinct_counts[field] = len(set(values))
            if field in SENSITIVE_IDENTIFIER_FIELDS:
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


def readiness(coverage: list[dict[str, object]], real_data_mode: bool) -> tuple[str, dict[str, str], list[str], list[str]]:
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
    phases = {
        "ready_for_design_audit": "yes" if not missing_required else "partial",
        "ready_for_cohort_spec": "partial" if not missing_required else "no",
        "ready_for_execution": "no",
    }
    if real_data_mode:
        blockers.append("Real-data mode is enabled; dry-run evidence alone must not authorize execution.")
    return status, phases, blockers, questions


def yaml_list(values: list[str], indent: int = 0) -> list[str]:
    prefix = " " * indent
    return [f"{prefix}- {value}" for value in values] if values else [f"{prefix}[]"]


def write_outputs(scans: list[dict[str, object]], coverage: list[dict[str, object]], output_dir: Path, real_data_mode: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    status, phases, blockers, questions = readiness(coverage, real_data_mode)
    write_inventory_csv(scans, output_dir / "nacc_file_inventory.csv")
    write_inventory_md(scans, output_dir / "nacc_file_inventory.md")
    write_coverage_yaml(coverage, output_dir / "nacc_concept_coverage.yaml")
    write_mapping_candidates_yaml(coverage, output_dir / "nacc_variable_mapping_candidates.yaml")
    write_readiness_report(status, phases, blockers, coverage, real_data_mode, output_dir / "nacc_readiness_report.md")
    write_questions(questions, blockers, output_dir / "unresolved_human_questions.md")
    write_human_confirmation_worksheet(questions, blockers, output_dir / "human_confirmation_worksheet.md")
    write_beginner_report(scans, coverage, status, blockers, real_data_mode, output_dir / "nacc_beginner_report.md")
    write_feature_readiness_report(coverage, output_dir / "feature_readiness_report.md")
    write_next_action_plan(coverage, blockers, real_data_mode, output_dir / "next_action_plan.md")
    write_glossary(output_dir / "nacc_glossary.md")


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
    lines = [
        "# NACC File Inventory",
        "",
        "This inventory summarizes file structure and small-sample distributions only. It does not print participant-level rows.",
        "",
        "| File | Rows | Columns | Inferred grain | Key sample summaries |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for scan in scans:
        summaries = []
        distributions = scan["distributions_sample"]  # type: ignore[assignment]
        for field, dist in distributions.items():  # type: ignore[union-attr]
            summaries.append(f"{field}: {dist}")
        lines.append(f"| {scan['name']} | {scan['row_count']} | {scan['column_count']} | {scan['grain']} | {'; '.join(summaries) or 'none'} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_coverage_yaml(coverage: list[dict[str, object]], path: Path) -> None:
    lines = ['schema_version: "0.8"', "concept_coverage:"]
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
    lines = ['schema_version: "0.8"', "adapter: nacc", "mapping_candidates:"]
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


def write_readiness_report(
    status: str,
    phases: dict[str, str],
    blockers: list[str],
    coverage: list[dict[str, object]],
    real_data_mode: bool,
    path: Path,
) -> None:
    missing = [str(item["concept_id"]) for item in coverage if item["status"] == "missing"]
    lines = [
        "# NACC Dry-Run Readiness Report",
        "",
        f"- Status: {status}",
        f"- Real data mode: {str(real_data_mode).lower()}",
        f"- Missing concepts: {', '.join(missing) if missing else 'none'}",
        f"- Ready for design audit: {phases['ready_for_design_audit']}",
        f"- Ready for cohort spec: {phases['ready_for_cohort_spec']}",
        f"- Ready for execution: {phases['ready_for_execution']}",
        "",
        "## Blockers / Gates",
        "",
        *(f"- {blocker}" for blocker in blockers),
        "",
        "## Recommendation",
        "",
        "Do not run cohort construction on real NACC data until required concepts, missing-code rules, UDS versions, and cohort spec readiness are confirmed. For treatment-effect studies, also confirm that medication records can actually support the intended exposure, comparator, washout, grace-period, and lag definitions.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_questions(questions: list[str], blockers: list[str], path: Path) -> None:
    lines = ["# Unresolved Human Questions", "", "## Blocking Gates", ""]
    lines.extend(f"- {blocker}" for blocker in blockers)
    lines.extend(["", "## Questions", ""])
    lines.extend(f"- {question}" for question in questions)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_human_confirmation_worksheet(questions: list[str], blockers: list[str], path: Path) -> None:
    lines = [
        "# Human Confirmation Worksheet",
        "",
        "Use this worksheet before cohort construction or effect estimation.",
        "",
        "## Required Sign-Off",
        "",
        "- [ ] NACC release, UDS versions, and modules are documented.",
        "- [ ] Missing-value and structural-missingness rules are documented.",
        "- [ ] Time zero and baseline window are confirmed.",
        "- [ ] Dementia-free baseline definition is confirmed.",
        "- [ ] Cognitive outcome variable and follow-up window are confirmed.",
        "- [ ] Medication records are treated as records first, not causal-ready exposure; exposure construction limits are documented.",
        "- [ ] APOE availability rule is justified.",
        "- [ ] Follow-up availability is treated as outcome ascertainment unless explicitly justified as eligibility.",
        "",
        "## Blockers / Gates",
        "",
    ]
    lines.extend(f"- {blocker}" for blocker in blockers)
    lines.extend(["", "## Questions for Human Review", ""])
    lines.extend(f"- [ ] {question}" for question in questions)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def coverage_status_map(coverage: list[dict[str, object]]) -> dict[str, str]:
    return {str(item["concept_id"]): str(item["status"]) for item in coverage}


def present_concepts(coverage: list[dict[str, object]]) -> list[str]:
    return [str(item["concept_id"]) for item in coverage if item["status"] != "missing"]


def missing_concepts(coverage: list[dict[str, object]]) -> list[str]:
    return [str(item["concept_id"]) for item in coverage if item["status"] == "missing"]


def write_beginner_report(
    scans: list[dict[str, object]],
    coverage: list[dict[str, object]],
    status: str,
    blockers: list[str],
    real_data_mode: bool,
    path: Path,
) -> None:
    sample_rows = sum(int(scan["row_count"]) for scan in scans)
    files_by_grain = Counter(str(scan["grain"]) for scan in scans)
    present = present_concepts(coverage)
    missing = missing_concepts(coverage)
    medication_present = "medication_records" in present
    medication_timing_present = "medication_temporality_support" in present
    lines = [
        "# Beginner NACC Navigation Report",
        "",
        "## Plain-English status",
        "",
        f"- Scanned files: {len(scans)}",
        f"- Rows visible to this dry run: {sample_rows}",
        f"- Real-data safety mode: {str(real_data_mode).lower()}",
        f"- Overall readiness: {status}",
        f"- Inferred grains: {dict(files_by_grain)}",
        "",
        "This report is meant for users who know modeling/code but do not yet know NACC well. It translates file headers and tiny samples into practical next steps.",
        "",
        "## What this sample appears to contain",
        "",
    ]
    if present:
        lines.extend(f"- {concept}" for concept in present)
    else:
        lines.append("- No target concepts were detected.")
    lines.extend(["", "## What is missing or unresolved", ""])
    if missing:
        lines.extend(f"- {concept}" for concept in missing)
    else:
        lines.append("- No tracked concept is completely missing from headers, but human confirmation is still required.")
    lines.extend(
        [
            "",
            "## Medication warning",
            "",
            "- NACC medication/treatment fields, when present, should be interpreted as medication records, not causal-ready exposure.",
            "- They are not automatically a treatment exposure variable.",
            f"- Medication records detected: {'yes' if medication_present else 'no'}",
            f"- Medication timing support detected: {'yes' if medication_timing_present else 'no'}",
            "- For treatment-effect estimation, the user must still define active comparator, new-user status, washout, grace period, lag period, and exposure persistence.",
            "",
            "## Blockers / gates",
            "",
        ]
    )
    lines.extend(f"- {blocker}" for blocker in blockers)
    lines.extend(
        [
            "",
            "## Suggested first real-data experiment",
            "",
            "Use a five-row sample only to verify that the skill can understand the local NACC release structure. Do not estimate effects or train a final model from five rows.",
            "",
            "Recommended command pattern:",
            "",
            "```powershell",
            "python skills/dementia-causal-cohort-auditor/scripts/make_header_samples.py --input-dir <REAL_NACC_DIR> --output-dir <SAFE_SAMPLE_DIR> --rows 5",
            "python skills/dementia-causal-cohort-auditor/scripts/scan_nacc_files.py --input-dir <SAFE_SAMPLE_DIR> --output-dir <DRY_RUN_OUTPUT_DIR> --sample-rows 5 --real-data-mode",
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_feature_readiness_report(coverage: list[dict[str, object]], path: Path) -> None:
    status_map = coverage_status_map(coverage)
    lines = [
        "# Feature and Task Readiness Report",
        "",
        "| Task | Required concept coverage | Recommended concept gaps | Interpretation |",
        "| --- | --- | --- | --- |",
    ]
    for profile in TASK_PROFILES.values():
        missing_required = [concept for concept in profile["required"] if status_map.get(concept) == "missing"]
        missing_recommended = [concept for concept in profile["recommended"] if status_map.get(concept) == "missing"]
        if missing_required:
            required_status = "blocked: " + ", ".join(missing_required)
        else:
            required_status = "surface-ready; needs human confirmation"
        recommended_status = ", ".join(missing_recommended) if missing_recommended else "none"
        lines.append(f"| {profile['label']} | {required_status} | {recommended_status} | {profile['note']} |")
    lines.extend(
        [
            "",
            "## How to read this",
            "",
            "- `surface-ready` means headers/sample values contain plausible candidates. It does not mean the cohort is methodologically valid.",
            "- Treatment-effect estimation has a higher bar than prediction or representation learning because medication records must be converted into a valid exposure design.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_next_action_plan(coverage: list[dict[str, object]], blockers: list[str], real_data_mode: bool, path: Path) -> None:
    status_map = coverage_status_map(coverage)
    lines = [
        "# Next Action Plan",
        "",
        "## Immediate next steps",
        "",
        "1. Confirm the NACC release, UDS versions, and module list against the official local data dictionary.",
        "2. Review `nacc_variable_mapping_candidates.yaml` and select fields only when their meanings match the study objective.",
        "3. Decide the first task profile: classification/prediction/trajectory/representation learning/treatment-effect/survival.",
        "4. Treat five-row samples as structural smoke tests only; use aggregate full-data checks before final cohort construction.",
        "",
        "## If your goal is treatment-effect estimation",
        "",
        "1. Verify whether the NACC extract includes A4/A4a or other medication/treatment modules.",
        "2. Decide whether medication records can define incident treatment, prevalent use, active comparator, or only descriptive covariates.",
        "3. Specify washout, grace period, lag window, exposure persistence, and outcome start before code generation.",
        "",
        "## Current blockers from dry run",
        "",
    ]
    lines.extend(f"- {blocker}" for blocker in blockers)
    if status_map.get("death_dropout") == "missing":
        lines.append("- Death/dropout/follow-up information is not detected; progression or survival designs need additional files or rules.")
    if real_data_mode:
        lines.append("- Real-data mode was used; keep outputs metadata-only until the user explicitly authorizes aggregate or row-level cohort generation.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_glossary(path: Path) -> None:
    lines = ["# NACC Beginner Glossary", "", "| Term | Practical meaning |", "| --- | --- |"]
    for term, meaning in GLOSSARY.items():
        lines.append(f"| {term} | {meaning} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sample-rows", type=int, default=25)
    parser.add_argument("--real-data-mode", action="store_true", help="Mark outputs as real-data dry run; never execution-ready.")
    args = parser.parse_args()

    files = sorted([path for path in args.input_dir.rglob("*") if path.is_file() and path.suffix.lower() in {".csv", ".tsv"}])
    if not files:
        raise SystemExit(f"No CSV/TSV files found in {args.input_dir}")
    scans = [scan_file(path, args.sample_rows) for path in files]
    coverage = concept_coverage(scans)
    write_outputs(scans, coverage, args.output_dir, args.real_data_mode)
    print(f"Wrote NACC dry-run outputs to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
