#!/usr/bin/env python3
"""
Read-only comparison of historical PDFBox experiment summaries.

Niloofar: This utility audits existing artifacts only. It does not regenerate,
overwrite, or modify any experiment result.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, Optional


# Niloofar: Keep the metric names explicit; "unique profiles" and
# "generated tests" are related in the experiment narrative but are not
# silently treated as identical by this audit utility.
METRIC_COLUMNS = {
    "invocations": ("invocations",),
    "collected_profiles": ("collected-profiles",),
    "unique_profiles": ("unique-profiles",),
    "generated_tests": ("generated-tests", "generated_tests"),
    "executed_tests": ("executed-tests", "executed_tests"),
    "passing_tests": ("passing-tests", "passing_tests"),
    "failing_tests": ("failing-tests", "failing_tests"),
}


def read_csv_total(path: Path) -> Dict[str, Optional[int]]:
    """Read the TOTAL row from a historical CSV without changing the file."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path}: CSV header is missing")

        for row in reader:
            method = (row.get("method") or "").strip().upper()
            if method == "TOTAL":
                result: Dict[str, Optional[int]] = {}
                for metric, possible_columns in METRIC_COLUMNS.items():
                    raw = next(
                        (row.get(column) for column in possible_columns
                         if row.get(column) not in (None, "")),
                        None,
                    )
                    try:
                        result[metric] = int(raw) if raw is not None else None
                    except ValueError:
                        result[metric] = None
                return result

    raise ValueError(f"{path}: no TOTAL row found")


def read_readme_summary(path: Path) -> Dict[str, Optional[int]]:
    """Extract the generated/executed/pass/fail counts from the PDFBox README."""
    text = path.read_text(encoding="utf-8")
    patterns = {
        "generated_tests": r"total:\s*([\d,]+)",
        "executed_tests": r"executed:\s*([\d,]+)",
        "passing_tests": r"passing:\s*([\d,]+)",
        "failing_tests": r"failing:\s*([\d,]+)",
    }
    result: Dict[str, Optional[int]] = {key: None for key in METRIC_COLUMNS}
    for metric, pattern in patterns.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            result[metric] = int(match.group(1).replace(",", ""))
    return result


def print_summary(name: str, values: Dict[str, Optional[int]]) -> None:
    print(f"\n{name}")
    for metric in METRIC_COLUMNS:
        value = values.get(metric)
        if value is not None:
            print(f"  {metric:20s} {value:,}")


def compare_summaries(summaries: Dict[str, Dict[str, Optional[int]]]) -> None:
    print("\nCross-artifact comparison")
    metrics = (
        "unique_profiles",
        "generated_tests",
        "executed_tests",
        "passing_tests",
        "failing_tests",
    )
    for metric in metrics:
        observed = [
            (name, values.get(metric))
            for name, values in summaries.items()
            if values.get(metric) is not None
        ]
        if len(observed) < 2:
            continue
        distinct = {value for _, value in observed}
        status = "MATCH" if len(distinct) == 1 else "DIFFERS"
        print(f"  {metric}: {status}")
        for name, value in observed:
            print(f"    {name}: {value:,}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare historical PDFBox report totals (read-only)."
    )
    parser.add_argument("--report", required=True, type=Path,
                        help="Path to execution/report.csv")
    parser.add_argument("--sizes", required=True, type=Path,
                        help="Path to data/report-file-sizes.csv")
    parser.add_argument("--readme", type=Path,
                        help="Optional path to the PDFBox README.md")
    args = parser.parse_args()

    try:
        summaries = {
            "execution/report.csv": read_csv_total(args.report),
            "data/report-file-sizes.csv": read_csv_total(args.sizes),
        }
        if args.readme:
            summaries["pdfbox/README.md"] = read_readme_summary(args.readme)

        for name, values in summaries.items():
            print_summary(name, values)
        compare_summaries(summaries)

        print("\nNiloofar: Audit completed. Input files were read only.")
        return 0
    except (OSError, ValueError, csv.Error) as error:
        print(f"Audit error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
