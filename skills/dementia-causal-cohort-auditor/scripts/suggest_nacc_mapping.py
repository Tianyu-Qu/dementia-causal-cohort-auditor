#!/usr/bin/env python
"""Suggest v0.3 NACC concept mappings from a CSV dictionary or header file."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


CONCEPTS = [
    {
        "concept_id": "participant_id",
        "label": "Participant identifier",
        "required": True,
        "grain": "participant",
        "candidates": ["NACCID"],
        "timing": "time invariant identifier",
    },
    {
        "concept_id": "visit_id",
        "label": "Visit identifier or visit order",
        "required": True,
        "grain": "visit",
        "candidates": ["NACCVNUM", "VISITNUM", "VISITNO"],
        "timing": "visit level",
    },
    {
        "concept_id": "visit_date",
        "label": "Visit date or date components",
        "required": True,
        "grain": "visit",
        "candidates": ["VISITDATE", "VISITMO", "VISITDAY", "VISITYR"],
        "timing": "visit level",
    },
    {
        "concept_id": "age_at_visit",
        "label": "Age at visit",
        "required": True,
        "grain": "visit",
        "candidates": ["NACCAGE", "AGE"],
        "timing": "at visit",
    },
    {
        "concept_id": "sex",
        "label": "Sex",
        "required": True,
        "grain": "participant",
        "candidates": ["SEX"],
        "timing": "baseline or participant level",
    },
    {
        "concept_id": "education",
        "label": "Years of education",
        "required": False,
        "grain": "participant",
        "candidates": ["EDUC", "EDUCATION"],
        "timing": "baseline or participant level",
    },
    {
        "concept_id": "apoe",
        "label": "APOE genotype or e4 count/status",
        "required": True,
        "grain": "participant",
        "candidates": ["NACCNE4S", "APOE", "APOE4", "NACCAPOE"],
        "timing": "genetic but availability timing must be audited",
    },
    {
        "concept_id": "cognitive_status",
        "label": "Cognitive status",
        "required": True,
        "grain": "visit",
        "candidates": ["NACCUDSD", "COGSTAT", "COGSTATUS"],
        "timing": "visit level",
    },
    {
        "concept_id": "dementia_status",
        "label": "Dementia status",
        "required": True,
        "grain": "visit",
        "candidates": ["NACCUDSD", "DEMENTED", "DEMENTIA"],
        "timing": "before or at time zero for baseline exclusion",
    },
    {
        "concept_id": "mci_status",
        "label": "MCI status",
        "required": False,
        "grain": "visit",
        "candidates": ["NACCUDSD", "MCI"],
        "timing": "visit level",
    },
    {
        "concept_id": "cdr_global",
        "label": "Global CDR",
        "required": False,
        "grain": "visit",
        "candidates": ["CDRGLOB"],
        "timing": "visit level",
    },
    {
        "concept_id": "cdr_sum",
        "label": "CDR sum of boxes",
        "required": False,
        "grain": "visit",
        "candidates": ["CDRSUM"],
        "timing": "visit level",
    },
    {
        "concept_id": "cognitive_score",
        "label": "Cognitive score",
        "required": True,
        "grain": "visit",
        "candidates": ["NACCMMSE", "MMSE", "NACCMOCA", "MOCA"],
        "timing": "outcome or baseline depending on role",
    },
    {
        "concept_id": "medication_exposure",
        "label": "Medication or treatment exposure",
        "required": True,
        "grain": "visit",
        "candidates": ["DRUGID", "DRUGNAME", "MEDICATION", "NACCA4", "A4", "A4A"],
        "timing": "must support exposure start, washout, grace, and lag rules",
    },
    {
        "concept_id": "death_status",
        "label": "Death status or date",
        "required": False,
        "grain": "participant",
        "candidates": ["DECEASED", "DEATH", "DOD"],
        "timing": "censoring or competing event",
    },
]


def read_dictionary(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        if "," not in sample and "\t" not in sample:
            return {line.strip().upper(): "" for line in handle if line.strip()}
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
        reader = csv.DictReader(handle, dialect=dialect)
        if not reader.fieldnames:
            return {}
        variable_col = choose_column(reader.fieldnames, ["variable", "var", "field", "name", "column"])
        desc_col = choose_column(reader.fieldnames, ["description", "label", "definition", "question", "text"])
        rows: dict[str, str] = {}
        for row in reader:
            variable = (row.get(variable_col, "") if variable_col else "").strip()
            if not variable:
                continue
            description = (row.get(desc_col, "") if desc_col else "").strip()
            rows[variable.upper()] = description
        return rows


def choose_column(fieldnames: list[str], candidates: list[str]) -> str | None:
    lowered = {name.lower().strip(): name for name in fieldnames}
    for candidate in candidates:
        for lowered_name, original in lowered.items():
            if candidate == lowered_name or candidate in lowered_name:
                return original
    return fieldnames[0] if candidates[0] in {"variable", "var", "field", "name", "column"} else None


def yaml_escape(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def emit_mapping(dictionary: dict[str, str], source: Path) -> str:
    lines = [
        'schema_version: "0.3"',
        "adapter: nacc",
        "mapping_metadata:",
        "  status: draft",
        "  created_by: dementia-causal-cohort-auditor",
        "  release_or_extract_date: unresolved",
        "  uds_versions: []",
        "  notes: Candidate mapping generated from a supplied dictionary/header file; confirm before execution.",
        "",
        "source_dictionary:",
        f"  files_reviewed:",
        f"    - {yaml_escape(str(source))}",
        "  dictionary_format: csv_or_header_list",
        "  missing_code_rules_reviewed: false",
        "",
        "core_concepts:",
    ]
    unresolved: list[str] = []
    for concept in CONCEPTS:
        matches = [candidate for candidate in concept["candidates"] if candidate.upper() in dictionary]
        status = "candidate" if matches else "unresolved"
        if concept["required"] and not matches:
            unresolved.append(str(concept["concept_id"]))
        lines.extend(
            [
                f"  - concept_id: {concept['concept_id']}",
                f"    label: {yaml_escape(str(concept['label']))}",
                f"    required: {str(concept['required']).lower()}",
                f"    status: {status}",
                f"    grain: {concept['grain']}",
                "    candidate_fields:",
            ]
        )
        if matches:
            for match in matches:
                evidence = dictionary.get(match.upper(), "")
                lines.extend(
                    [
                        f"      - field: {match}",
                        f"        evidence: {yaml_escape(evidence or 'name match in supplied dictionary/header file')}",
                    ]
                )
        else:
            lines.append("      []")
        lines.extend(
            [
                "    selected_field: unresolved",
                f"    timing_rule: {yaml_escape(str(concept['timing']))}",
                "    notes: Confirm against local NACC release and study design.",
            ]
        )
    lines.extend(
        [
            "",
            "unresolved_items:",
        ]
    )
    if unresolved:
        for concept_id in unresolved:
            lines.extend(
                [
                    f"  - id: unresolved_{concept_id}",
                    "    severity: blocking",
                    f"    concept_id: {concept_id}",
                    "    question: Which NACC variable or module supports this concept?",
                ]
            )
    else:
        lines.append("  []")
    lines.extend(
        [
            "",
            "temporal_warnings:",
            "  - Confirm visit ordering and date components before defining time zero.",
            "  - Confirm treatment variables support new-user, washout, grace-period, and lag-period definitions.",
            "",
            "missingness_warnings:",
            "  - Review NACC missing value codes and structural missingness across UDS versions.",
            "  - Audit APOE and cognitive outcome missingness before restricting the cohort.",
            "",
            "readiness:",
            "  ready_for_cohort_spec: false",
            "  blocking_issues:",
        ]
    )
    if unresolved:
        for concept_id in unresolved:
            lines.append(f"    - unresolved_{concept_id}")
    else:
        lines.append("    - human_confirmation_required")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dictionary_csv", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    dictionary = read_dictionary(args.dictionary_csv)
    if not dictionary:
        print("No variables found in dictionary/header file.", file=sys.stderr)
        return 1

    output = emit_mapping(dictionary, args.dictionary_csv)
    if args.output:
        args.output.write_text(output, encoding="utf-8", newline="\n")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
