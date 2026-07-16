#!/usr/bin/env python
"""Validate the required v0.2 cohort_definition.yaml surface.

This intentionally uses a conservative text-level check instead of requiring
PyYAML. It verifies the contract that matters for the skill: required fields
must be present and readiness must be explicit.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_TOP_LEVEL = [
    "schema_version",
    "metadata",
    "study_question",
    "estimand",
    "data_source",
    "population",
    "exposure",
    "comparator",
    "time_zero",
    "baseline_window",
    "follow_up",
    "outcome",
    "inclusion_criteria",
    "exclusion_criteria",
    "covariates",
    "missingness_plan",
    "leakage_checks",
    "attrition_plan",
    "sensitivity_analyses",
    "assumptions",
    "unresolved_items",
    "readiness",
]

REQUIRED_PATHS = [
    "metadata.status",
    "metadata.created_by",
    "estimand.target_population",
    "estimand.treatment_strategy",
    "estimand.comparator_strategy",
    "estimand.assignment_time",
    "estimand.follow_up_start",
    "estimand.outcome",
    "estimand.causal_contrast",
    "data_source.name",
    "data_source.adapter",
    "time_zero.definition",
    "baseline_window.start",
    "baseline_window.end",
    "follow_up.start",
    "follow_up.end",
    "outcome.definition",
    "readiness.ready_for_execution",
    "readiness.blocking_issues",
]


def strip_comment(line: str) -> str:
    return line.split("#", 1)[0].rstrip()


def top_level_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for line in text.splitlines():
        clean = strip_comment(line)
        if not clean or clean.startswith((" ", "-")):
            continue
        match = re.match(r"^([A-Za-z0-9_]+):", clean)
        if match:
            keys.add(match.group(1))
    return keys


def path_exists(text: str, dotted_path: str) -> bool:
    parent, child = dotted_path.split(".", 1)
    in_parent = False
    parent_indent = 0
    for raw_line in text.splitlines():
        line = strip_comment(raw_line)
        if not line:
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if re.match(rf"^{re.escape(parent)}:", line):
            in_parent = True
            parent_indent = indent
            continue
        if in_parent and indent <= parent_indent and not line.startswith("-"):
            in_parent = False
        if in_parent and re.match(rf"^\s+{re.escape(child)}:", raw_line):
            return True
    return False


def validate(text: str) -> list[str]:
    missing: list[str] = []
    keys = top_level_keys(text)
    for key in REQUIRED_TOP_LEVEL:
        if key not in keys:
            missing.append(key)
    for dotted_path in REQUIRED_PATHS:
        if not path_exists(text, dotted_path):
            missing.append(dotted_path)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cohort_spec", type=Path)
    args = parser.parse_args()

    text = args.cohort_spec.read_text(encoding="utf-8")
    missing = validate(text)
    if missing:
        print("Missing required cohort spec fields:")
        for item in missing:
            print(f"- {item}")
        return 1

    print("Cohort spec contains all required v0.2 fields.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
