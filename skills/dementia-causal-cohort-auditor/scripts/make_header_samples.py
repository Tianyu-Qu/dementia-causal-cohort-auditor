#!/usr/bin/env python
"""Create safe header-only or small sample copies from CSV/TSV files."""

from __future__ import annotations

import argparse
from pathlib import Path


def copy_sample(source: Path, destination: Path, rows: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    limit = rows + 1
    with source.open("r", encoding="utf-8-sig", errors="replace", newline="") as src, destination.open(
        "w", encoding="utf-8", newline=""
    ) as dst:
        for index, line in enumerate(src):
            if index >= limit:
                break
            dst.write(line)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--rows", type=int, default=0, help="Rows after the header to include. Defaults to 0.")
    args = parser.parse_args()

    if args.rows < 0:
        raise SystemExit("--rows must be non-negative")

    files = sorted([path for path in args.input_dir.iterdir() if path.suffix.lower() in {".csv", ".tsv"}])
    if not files:
        raise SystemExit(f"No CSV/TSV files found in {args.input_dir}")
    for source in files:
        copy_sample(source, args.output_dir / source.name, args.rows)
    print(f"Wrote header/sample files to {args.output_dir} with rows={args.rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
