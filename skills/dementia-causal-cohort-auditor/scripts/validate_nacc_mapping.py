#!/usr/bin/env python
"""Validate that a v0.3 NACC mapping represents required concepts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_TOP_LEVEL = [
    "schema_version",
    "adapter",
    "mapping_metadata",
    "source_dictionary",
    "core_concepts",
    "unresolved_items",
    "temporal_warnings",
    "missingness_warnings",
    "readiness",
]

REQUIRED_CONCEPTS = [
    "participant_id",
    "visit_id",
    "visit_date",
    "age_at_visit",
    "sex",
    "apoe",
    "cognitive_status",
    "dementia_status",
    "cognitive_score",
    "medication_records",
]

CONCEPT_ALIASES = {
    "medication_records": {"medication_exposure"},
}


def top_level_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for line in text.splitlines():
        if not line or line.startswith((" ", "-")):
            continue
        match = re.match(r"^([A-Za-z0-9_]+):", line)
        if match:
            keys.add(match.group(1))
    return keys


def concept_ids(text: str) -> set[str]:
    return set(re.findall(r"concept_id:\s*([A-Za-z0-9_]+)", text))


def validate(text: str) -> list[str]:
    missing: list[str] = []
    keys = top_level_keys(text)
    concepts = concept_ids(text)
    for key in REQUIRED_TOP_LEVEL:
        if key not in keys:
            missing.append(key)
    for concept in REQUIRED_CONCEPTS:
        aliases = CONCEPT_ALIASES.get(concept, set())
        if concept not in concepts and concepts.isdisjoint(aliases):
            missing.append(f"concept:{concept}")
    if "ready_for_cohort_spec:" not in text:
        missing.append("readiness.ready_for_cohort_spec")
    return missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mapping_yaml", type=Path)
    args = parser.parse_args()

    text = args.mapping_yaml.read_text(encoding="utf-8")
    missing = validate(text)
    if missing:
        print("Missing required NACC mapping fields:")
        for item in missing:
            print(f"- {item}")
        return 1

    print("NACC mapping contains all required v0.3 concepts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
