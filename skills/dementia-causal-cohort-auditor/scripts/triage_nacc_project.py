#!/usr/bin/env python
"""Triage a messy local project folder before NACC scanning.

This script reads file names, CSV/TSV headers, and ZIP member names only. It
does not read or emit participant-level data rows.
"""

from __future__ import annotations

import argparse
import csv
import re
import zipfile
from pathlib import Path


DATA_SUFFIXES = {".csv", ".tsv"}
ARCHIVE_SUFFIXES = {".zip"}
SKIP_DIRS = {".git", ".agents", "__pycache__"}
CORE_FIELDS = {"NACCID", "NACCVNUM", "VISITMO", "VISITDAY", "VISITYR"}


def read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        line = handle.readline().strip()
    if not line:
        return []
    delimiter = "\t" if "\t" in line and "," not in line else ","
    return [part.strip() for part in line.split(delimiter)]


def read_zip_csv_header(zip_path: Path, member: str) -> list[str]:
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(member) as handle:
            line = handle.readline().decode("utf-8-sig", errors="replace").strip()
    if not line:
        return []
    delimiter = "\t" if "\t" in line and "," not in line else ","
    return [part.strip() for part in line.split(delimiter)]


def category_for(name: str, headers: list[str]) -> tuple[str, str, int]:
    upper_name = name.upper()
    upper_headers = {header.upper() for header in headers}
    score = 0
    reasons: list[str] = []

    if "NACCID" in upper_headers:
        score += 2
        reasons.append("has NACCID")
    if "NACCVNUM" in upper_headers:
        score += 2
        reasons.append("has visit number")
    if {"VISITMO", "VISITDAY", "VISITYR"}.issubset(upper_headers):
        score += 2
        reasons.append("has visit date components")
    if {"PACKET", "FORMVER"}.intersection(upper_headers):
        score += 1
        reasons.append("has packet/form version")
    if len(headers) >= 500:
        score += 2
        reasons.append("wide clinical-style table")

    if CORE_FIELDS.issubset(upper_headers) or (score >= 7 and "SCAN" not in upper_name):
        return "core_clinical_candidate", "; ".join(reasons), score
    if "MRI" in upper_name or any("MRI" in header.upper() or header.upper().endswith("_VOLUME") for header in headers):
        return "mri_imaging", "; ".join(reasons + ["MRI-like file name/fields"]), score
    if "PET" in upper_name or any("SUVR" in header.upper() or "CENTILOID" in header.upper() for header in headers):
        return "pet_imaging", "; ".join(reasons + ["PET/SUVR-like file name/fields"]), score
    if "CSF" in upper_name or any(header.upper().startswith("CSF") for header in headers):
        return "csf_biomarker", "; ".join(reasons + ["CSF-like fields"]), score
    if "NACCID" in upper_headers:
        return "nacc_auxiliary_table", "; ".join(reasons), score
    return "non_nacc_or_irrelevant", "no NACCID/core visit header detected", score


def role_for(category: str) -> str:
    if category == "core_clinical_candidate":
        return "start_here_for_uds_cohort_smoke_test"
    if category in {"csf_biomarker", "mri_imaging", "pet_imaging", "nacc_auxiliary_table"}:
        return "optional_later_module_after_core_mapping"
    return "ignore_for_initial_nacc_smoke_test"


def iter_files(root: Path, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    files = [path for path in root.glob(pattern) if path.is_file()]
    return sorted(path for path in files if not any(part in SKIP_DIRS for part in path.parts))


def scan_project(root: Path, recursive: bool, include_zip_headers: bool) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in iter_files(root, recursive):
        suffix = path.suffix.lower()
        relative = path.relative_to(root)
        if suffix in DATA_SUFFIXES:
            headers = read_header(path)
            category, reason, score = category_for(path.name, headers)
            rows.append(
                {
                    "path": str(relative),
                    "container": "",
                    "kind": suffix.lstrip("."),
                    "category": category,
                    "recommended_role": role_for(category),
                    "score": score,
                    "size_bytes": path.stat().st_size,
                    "column_count": len(headers),
                    "key_fields": "|".join([h for h in headers[:40]]),
                    "reason": reason,
                }
            )
        elif suffix in ARCHIVE_SUFFIXES:
            rows.append(
                {
                    "path": str(relative),
                    "container": "",
                    "kind": "zip",
                    "category": "archive",
                    "recommended_role": "inspect_or_extract_selectively_if_needed",
                    "score": 0,
                    "size_bytes": path.stat().st_size,
                    "column_count": "",
                    "key_fields": "",
                    "reason": "ZIP archive; member names listed separately when possible",
                }
            )
            if include_zip_headers:
                rows.extend(scan_zip_members(root, path))
        else:
            rows.append(
                {
                    "path": str(relative),
                    "container": "",
                    "kind": suffix.lstrip(".") or "file",
                    "category": "non_nacc_or_irrelevant",
                    "recommended_role": "ignore_for_initial_nacc_smoke_test",
                    "score": 0,
                    "size_bytes": path.stat().st_size,
                    "column_count": "",
                    "key_fields": "",
                    "reason": "unsupported file suffix for NACC table triage",
                }
            )
    return rows


def scan_zip_members(root: Path, zip_path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    try:
        with zipfile.ZipFile(zip_path) as archive:
            members = [info for info in archive.infolist() if not info.is_dir()]
            for info in members[:200]:
                member_suffix = Path(info.filename).suffix.lower()
                headers: list[str] = []
                category = "archive_member"
                reason = "ZIP member listed; header not read"
                score = 0
                if member_suffix in DATA_SUFFIXES:
                    try:
                        headers = read_zip_csv_header(zip_path, info.filename)
                        category, reason, score = category_for(Path(info.filename).name, headers)
                    except Exception as exc:  # pragma: no cover - defensive for unusual archives
                        reason = f"could not read member header: {exc}"
                rows.append(
                    {
                        "path": info.filename,
                        "container": str(zip_path.relative_to(root)),
                        "kind": member_suffix.lstrip(".") or "zip_member",
                        "category": category,
                        "recommended_role": role_for(category) if category != "archive_member" else "inspect_or_extract_selectively_if_needed",
                        "score": score,
                        "size_bytes": info.file_size,
                        "column_count": len(headers) if headers else "",
                        "key_fields": "|".join(headers[:40]) if headers else "",
                        "reason": reason,
                    }
                )
    except zipfile.BadZipFile:
        rows.append(
            {
                "path": str(zip_path.relative_to(root)),
                "container": "",
                "kind": "zip",
                "category": "unreadable_archive",
                "recommended_role": "manual_review",
                "score": 0,
                "size_bytes": zip_path.stat().st_size,
                "column_count": "",
                "key_fields": "",
                "reason": "bad ZIP file",
            }
        )
    return rows


def write_inventory(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "path",
        "container",
        "kind",
        "category",
        "recommended_role",
        "score",
        "size_bytes",
        "column_count",
        "key_fields",
        "reason",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict[str, object]], output_dir: Path) -> None:
    candidates = dedupe_rows(
        sorted(
            [row for row in rows if row["recommended_role"] == "start_here_for_uds_cohort_smoke_test"],
            key=lambda row: (bool(row["container"]), -int(row["score"]), -int(row["size_bytes"])),
        )
    )
    optional = dedupe_rows([row for row in rows if row["recommended_role"] == "optional_later_module_after_core_mapping"])
    ignored = [row for row in rows if row["recommended_role"] == "ignore_for_initial_nacc_smoke_test"]
    archives = dedupe_rows([row for row in rows if row["kind"] == "zip"])
    lines = [
        "# NACC Project Triage Report",
        "",
        "This report is metadata/header-only. It does not contain participant-level rows.",
        "",
        "## Recommended starting files",
        "",
    ]
    if candidates:
        lines.extend(
            f"- `{display_path(row)}` ({row['column_count']} columns): {row['reason']}" for row in candidates[:10]
        )
    else:
        lines.append("- No clear UDS/core clinical candidate found. Ask the user for the NACC clinical/UDS CSV or data dictionary.")
    lines.extend(
        [
            "",
            "## Optional later modules",
            "",
        ]
    )
    if optional:
        lines.extend(f"- `{display_path(row)}`: {row['category']}" for row in optional[:20])
    else:
        lines.append("- None detected.")
    lines.extend(
        [
            "",
            "## Archives",
            "",
        ]
    )
    if archives:
        lines.extend(f"- `{display_path(row)}` ({row['size_bytes']} bytes)" for row in archives[:20])
    else:
        lines.append("- None detected.")
    lines.extend(
        [
            "",
            "## Ignored for initial smoke test",
            "",
            f"- {len(ignored)} files look irrelevant to the initial NACC cohort smoke test.",
            "",
            "## Agent guidance",
            "",
            "1. Start with the highest-scoring core clinical candidate, not every file in the project folder.",
            "2. Use imaging, CSF, PET, MRI, and other modules only after the core UDS mapping is understood.",
            "3. Do not treat ZIP archives as inputs unless the selected table is only available inside the archive.",
            "4. If the directory contains papers, code, bibliography files, or unrelated registries, ignore them for NACC preflight.",
            "5. After selecting candidate files, create a safe five-row sample and run `scan_nacc_files.py --real-data-mode` on that selected sample folder.",
        ]
    )
    (output_dir / "nacc_project_triage_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    selected = [str(row["path"]) for row in candidates[:5] if not str(row["container"])]
    (output_dir / "recommended_core_files.txt").write_text("\n".join(selected) + ("\n" if selected else ""), encoding="utf-8")


def display_path(row: dict[str, object]) -> str:
    container = str(row["container"])
    path = str(row["path"])
    return f"{container}::{path}" if container else path


def dedupe_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, object]] = []
    for row in rows:
        key = (str(row["container"]), str(row["path"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--include-zip-headers", action="store_true")
    args = parser.parse_args()

    if not args.input_dir.exists():
        raise SystemExit(f"Input directory does not exist: {args.input_dir}")
    rows = scan_project(args.input_dir, args.recursive, args.include_zip_headers)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_inventory(rows, args.output_dir / "nacc_project_triage_inventory.csv")
    write_report(rows, args.output_dir)
    print(f"Wrote NACC project triage outputs to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
