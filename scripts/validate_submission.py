#!/usr/bin/env python3
"""Validate the schema and case coverage of a Future Selves submission."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SAMPLE = ROOT / "data" / "sample_submission.csv"
EXPECTED_COLUMNS = ["id", "predicted_tst_2025"]


class ValidationError(ValueError):
    """Raised when a submission does not match the required format."""


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise ValidationError(f"File not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames is None:
            raise ValidationError("The submission is empty")
        rows = []
        try:
            for row in reader:
                if None in row:
                    raise ValidationError(
                        f"CSV record ending at line {reader.line_num} has extra fields"
                    )
                missing = [field for field, value in row.items() if value is None]
                if missing:
                    raise ValidationError(
                        f"CSV record ending at line {reader.line_num} is missing "
                        f"fields: {missing}"
                    )
                rows.append(row)
        except csv.Error as error:
            raise ValidationError(f"Malformed CSV: {error}") from error
        return reader.fieldnames, rows


def validate(submission: Path, sample: Path) -> int:
    sample_columns, sample_rows = read_rows(sample)
    if sample_columns != EXPECTED_COLUMNS:
        raise ValidationError(
            f"Reference sample has unexpected columns: {sample_columns}"
        )

    columns, rows = read_rows(submission)
    if columns != EXPECTED_COLUMNS:
        raise ValidationError(
            f"Expected columns {EXPECTED_COLUMNS}, found {columns}"
        )

    expected_ids = [row["id"] for row in sample_rows]
    actual_ids = [row["id"] for row in rows]
    if len(actual_ids) != len(set(actual_ids)):
        raise ValidationError("Submission contains duplicate IDs")

    missing_ids = sorted(set(expected_ids) - set(actual_ids))
    extra_ids = sorted(set(actual_ids) - set(expected_ids))
    if missing_ids or extra_ids:
        details = []
        if missing_ids:
            details.append(f"missing {len(missing_ids)} expected IDs")
        if extra_ids:
            details.append(f"contains {len(extra_ids)} unexpected IDs")
        raise ValidationError("Submission " + " and ".join(details))

    if actual_ids != expected_ids:
        raise ValidationError("Submission IDs are not in the required order")

    blank_ids = [row["id"] for row in rows if not row["predicted_tst_2025"].strip()]
    if blank_ids:
        raise ValidationError(f"Blank predictions found for {len(blank_ids)} IDs")

    return len(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    parser.add_argument(
        "--sample",
        type=Path,
        default=DEFAULT_SAMPLE,
        help="Reference sample submission (default: data/sample_submission.csv)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        row_count = validate(args.submission, args.sample)
    except (OSError, csv.Error, ValidationError) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 1
    print(f"VALID: {row_count} predictions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
