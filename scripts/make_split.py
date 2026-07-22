#!/usr/bin/env python3
"""Build the public benchmark files from private Qualtrics/Prolific exports."""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRIVATE_DATA = ROOT / "private" / "data"
DEFAULT_PUBLIC_DATA = ROOT / "data"
DEFAULT_PRIVATE_OUTPUT = ROOT / "private" / "derived"

QUALTRICS_FILE = "JJJ+Pro+WAI+All_Responses_exported_July_22_2026.csv"
PROLIFIC_2024_ORIGINAL_FILE = (
    "JJJ_Pro_WAI_2024_prolific_demographic_exported_2024.csv"
)
PROLIFIC_2024_FILE = "JJJ_Pro_WAI_2024_prolific_demographic_exported_2026.csv"
PROLIFIC_2025_FILE = (
    "JJJ_Pro_WAI_2025_Longi_prolific_demographic_exported_2026.csv"
)

TRAIN_SIZE = 150
DEV_SIZE = 50
EXPECTED_PAIRS = 281
DEFAULT_SEED = "future-selves-v1-2026-07-22"

RAW_TEXT_FIELD = "wai_text_repsonse"
INVALID_VALUES = {"", "DATA_EXPIRED", "N/A", "NA", "NULL", "NONE"}

DEMOGRAPHIC_FIELDS = {
    "Age": "age",
    "Sex": "sex",
    "Ethnicity simplified": "ethnicity_simplified",
    "Country of birth": "country_of_birth",
    "Country of residence": "country_of_residence",
    "Nationality": "nationality",
    "Language": "language",
    "Student status": "student_status",
    "Employment status": "employment_status",
}


class BuildError(RuntimeError):
    """Raised when a raw-data invariant does not hold."""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise BuildError(f"Required source file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def index_unique(
    rows: Iterable[dict[str, str]], key: str, source_name: str
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        value = row[key]
        if not value:
            raise BuildError(f"Blank {key!r} in {source_name}")
        if value in result:
            raise BuildError(f"Duplicate {key!r} in {source_name}: {value}")
        result[value] = row
    return result


def is_valid_demographic(field: str, value: str) -> bool:
    value = value.strip()
    if value.upper() in INVALID_VALUES:
        return False
    if field == "Age":
        try:
            age = int(value)
        except ValueError:
            return False
        return 18 <= age <= 120
    return True


def clean_demographic(field: str, value: str) -> str:
    value = value.strip()
    return value if is_valid_demographic(field, value) else ""


def merged_2024_demographics(
    current: dict[str, str], original: dict[str, str]
) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_name, public_name in DEMOGRAPHIC_FIELDS.items():
        chosen = current[raw_name]
        if not is_valid_demographic(raw_name, chosen):
            chosen = original[raw_name]
        values[f"{public_name}_2024"] = clean_demographic(raw_name, chosen)

    values["fluent_languages_2024"] = clean_demographic(
        "Fluent languages", original["Fluent languages"]
    )
    return values


def demographics_2025(row: dict[str, str]) -> dict[str, str]:
    return {
        f"{public_name}_2025": clean_demographic(raw_name, row[raw_name])
        for raw_name, public_name in DEMOGRAPHIC_FIELDS.items()
    }


def qualifying_response(row: dict[str, str]) -> bool:
    return (
        row["Finished"] == "True"
        and row["Progress"] == "100"
        and row["consent"] == "Consent to continue"
        and bool(row["pei_inform"].strip())
        and bool(row["public_data_inform"].strip())
        and bool(row[RAW_TEXT_FIELD].strip())
    )


def select_response(
    responses_by_session: dict[str, list[dict[str, str]]],
    submission: dict[str, str],
) -> dict[str, str] | None:
    candidates = [
        row
        for row in responses_by_session.get(submission["Submission id"], [])
        if qualifying_response(row)
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda row: (row["RecordedDate"], row["ResponseId"]))
    selected = candidates[-1]
    if selected["PROLIFIC_PID"] != submission["Participant id"]:
        raise BuildError(
            "Qualtrics PROLIFIC_PID does not match the Prolific participant "
            f"for submission {submission['Submission id']}"
        )
    return selected


def split_rank(seed: str, participant_id: str) -> bytes:
    return hashlib.sha256(f"{seed}\0{participant_id}".encode("utf-8")).digest()


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def build_rows(private_data: Path) -> list[dict[str, str]]:
    qualtrics_rows = [
        row
        for row in read_csv(private_data / QUALTRICS_FILE)
        if row.get("ResponseId", "").startswith("R_")
    ]
    responses_by_session: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in qualtrics_rows:
        if row["SESSION_ID"]:
            responses_by_session[row["SESSION_ID"]].append(row)

    original_2024 = index_unique(
        read_csv(private_data / PROLIFIC_2024_ORIGINAL_FILE),
        "Submission id",
        PROLIFIC_2024_ORIGINAL_FILE,
    )
    current_2024_by_participant = index_unique(
        read_csv(private_data / PROLIFIC_2024_FILE),
        "Participant id",
        PROLIFIC_2024_FILE,
    )
    current_2025_by_participant = index_unique(
        read_csv(private_data / PROLIFIC_2025_FILE),
        "Participant id",
        PROLIFIC_2025_FILE,
    )

    paired_ids = sorted(
        current_2024_by_participant.keys() & current_2025_by_participant.keys()
    )
    rows: list[dict[str, str]] = []
    for participant_id in paired_ids:
        prolific_2024 = current_2024_by_participant[participant_id]
        prolific_2025 = current_2025_by_participant[participant_id]
        if prolific_2024["Status"] != "APPROVED" or prolific_2025["Status"] != "APPROVED":
            continue

        response_2024 = select_response(responses_by_session, prolific_2024)
        response_2025 = select_response(responses_by_session, prolific_2025)
        if response_2024 is None or response_2025 is None:
            continue

        original = original_2024.get(prolific_2024["Submission id"])
        if original is None:
            raise BuildError(
                "Authoritative 2024 submission is absent from the original export: "
                f"{prolific_2024['Submission id']}"
            )

        row = {
            "_participant_id": participant_id,
            "tst_2024": response_2024[RAW_TEXT_FIELD].strip(),
            "tst_2025": response_2025[RAW_TEXT_FIELD].strip(),
        }
        row.update(merged_2024_demographics(prolific_2024, original))
        row.update(demographics_2025(prolific_2025))
        rows.append(row)

    if len(rows) != EXPECTED_PAIRS:
        raise BuildError(
            f"Expected {EXPECTED_PAIRS} complete approved pairs, found {len(rows)}"
        )
    return rows


def build_files(
    private_data: Path,
    public_data: Path,
    private_output: Path,
    seed: str,
) -> None:
    rows = sorted(
        build_rows(private_data),
        key=lambda row: split_rank(seed, row["_participant_id"]),
    )
    partitions = {
        "train": rows[:TRAIN_SIZE],
        "dev": rows[TRAIN_SIZE : TRAIN_SIZE + DEV_SIZE],
        "test": rows[TRAIN_SIZE + DEV_SIZE :],
    }

    for split_name, split_rows in partitions.items():
        for index, row in enumerate(split_rows, start=1):
            row["id"] = f"{split_name}_{index:04d}"

    demographics_2024 = [
        f"{name}_2024" for name in DEMOGRAPHIC_FIELDS.values()
    ] + ["fluent_languages_2024"]
    demographics_2025 = [f"{name}_2025" for name in DEMOGRAPHIC_FIELDS.values()]
    labeled_fields = [
        "id",
        "tst_2024",
        *demographics_2024,
        "tst_2025",
        *demographics_2025,
    ]
    input_fields = ["id", "tst_2024", *demographics_2024]
    key_fields = ["id", "tst_2025", *demographics_2025]

    write_csv(public_data / "train.csv", partitions["train"], labeled_fields)
    write_csv(public_data / "dev.csv", partitions["dev"], labeled_fields)
    write_csv(public_data / "test_input.csv", partitions["test"], input_fields)
    write_csv(private_output / "test_key.csv", partitions["test"], key_fields)

    sample_rows = [
        {"id": row["id"], "predicted_tst_2025": row["tst_2024"]}
        for row in partitions["test"]
    ]
    write_csv(
        public_data / "sample_submission.csv",
        sample_rows,
        ["id", "predicted_tst_2025"],
    )

    print(
        f"Wrote {len(partitions['train'])} train, {len(partitions['dev'])} dev, "
        f"and {len(partitions['test'])} test cases."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-data", type=Path, default=DEFAULT_PRIVATE_DATA)
    parser.add_argument("--public-data", type=Path, default=DEFAULT_PUBLIC_DATA)
    parser.add_argument("--private-output", type=Path, default=DEFAULT_PRIVATE_OUTPUT)
    parser.add_argument("--seed", default=DEFAULT_SEED)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_files(args.private_data, args.public_data, args.private_output, args.seed)
