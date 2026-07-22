#!/usr/bin/env python3
"""Predict that each 2025 TST response exactly repeats its 2024 response."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "test_input.csv"
DEFAULT_OUTPUT = ROOT / "submissions" / "repeat_2024_submission.csv"


def make_predictions(input_path: Path, output_path: Path) -> int:
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["id", "predicted_tst_2025"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(
            {
                "id": row["id"],
                "predicted_tst_2025": row["tst_2024"],
            }
            for row in rows
        )
    return len(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    count = make_predictions(args.input, args.output)
    print(f"Wrote {count} predictions to {args.output}")
