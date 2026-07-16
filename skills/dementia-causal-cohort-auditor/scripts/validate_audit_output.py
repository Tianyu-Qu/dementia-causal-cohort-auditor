#!/usr/bin/env python
"""Validate that a v0.1 design audit contains the required sections."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "Mode",
    "Study Design Restatement",
    "Draft Estimand",
    "Red Flags",
    "Must-Answer Human Confirmations",
    "Temporal Ordering Review",
    "Leakage and Bias Checks",
    "Missingness and Measurement Concerns",
    "Recommended Sensitivity Analyses",
    "Next-Step Recommendation",
]


def normalize_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().strip("#").strip())


def extract_headings(markdown: str) -> set[str]:
    headings: set[str] = set()
    for line in markdown.splitlines():
        if line.lstrip().startswith("#"):
            headings.add(normalize_heading(line))
    return headings


def validate(markdown: str) -> list[str]:
    headings = extract_headings(markdown)
    return [section for section in REQUIRED_SECTIONS if section not in headings]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("audit_markdown", type=Path)
    args = parser.parse_args()

    text = args.audit_markdown.read_text(encoding="utf-8")
    missing = validate(text)
    if missing:
        print("Missing required sections:")
        for section in missing:
            print(f"- {section}")
        return 1

    print("Audit output contains all required v0.1 sections.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
