#!/usr/bin/env python3
"""Produce an automated scorecard for Future Selves predictions."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Callable, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCES = ROOT / "data" / "dev.csv"
TOKEN_RE = re.compile(r"\w+(?:['\N{RIGHT SINGLE QUOTATION MARK}]\w+)*", re.UNICODE)
PREDICTION_COLUMNS = ["id", "predicted_tst_2025"]

METRIC_INFO = {
    "normalized_exact_match_rate": (
        "Agreement",
        "higher",
        "Fraction of predictions exactly matching the reference after case and whitespace normalization.",
    ),
    "normalized_edit_similarity": (
        "Agreement",
        "higher",
        "Character-level Levenshtein similarity after case and whitespace normalization.",
    ),
    "token_jaccard_similarity": (
        "Agreement",
        "higher",
        "Macro-average Jaccard similarity over unique prediction and reference tokens.",
    ),
    "token_overlap_f1": (
        "Agreement",
        "higher",
        "Macro-average bag-of-words token overlap F1 against the reference.",
    ),
    "rouge_l_f1": (
        "Agreement",
        "higher",
        "Macro-average longest-common-subsequence token F1 against the reference.",
    ),
    "character_ngram_f1": (
        "Agreement",
        "higher",
        "Macro-average character 1- through 6-gram overlap F1 against the reference.",
    ),
    "word_count_mae": (
        "Form",
        "lower",
        "Mean absolute error in response word count.",
    ),
    "line_count_mae": (
        "Form",
        "lower",
        "Mean absolute error in nonblank response-line count.",
    ),
    "prediction_word_count_mean": (
        "Form",
        "descriptive",
        "Mean predicted response word count.",
    ),
    "reference_word_count_mean": (
        "Form",
        "descriptive",
        "Mean reference response word count.",
    ),
    "prediction_repeat_2024_rate": (
        "Change",
        "descriptive",
        "Fraction of predictions that repeat the 2024 response after normalization.",
    ),
    "observed_repeat_2024_rate": (
        "Change",
        "descriptive",
        "Fraction of reference responses that repeat the 2024 response after normalization.",
    ),
    "source_similarity_mae": (
        "Change",
        "lower",
        "Mean absolute error between predicted and observed ROUGE-L similarity to the 2024 response.",
    ),
    "prediction_source_similarity_mean": (
        "Change",
        "descriptive",
        "Mean ROUGE-L similarity between predictions and 2024 responses.",
    ),
    "observed_source_similarity_mean": (
        "Change",
        "descriptive",
        "Mean ROUGE-L similarity between follow-up and 2024 responses.",
    ),
}


class EvaluationError(ValueError):
    """Raised when scorecard inputs are invalid or incompatible."""


def normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(normalize(text))


def f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def token_overlap_f1(prediction: str, reference: str) -> float:
    predicted = Counter(tokenize(prediction))
    expected = Counter(tokenize(reference))
    if not predicted and not expected:
        return 1.0
    overlap = sum((predicted & expected).values())
    precision = overlap / sum(predicted.values()) if predicted else 0.0
    recall = overlap / sum(expected.values()) if expected else 0.0
    return f1(precision, recall)


def levenshtein_distance(left: str, right: str) -> int:
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for left_index, left_character in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_character in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1]
                    + (left_character != right_character),
                )
            )
        previous = current
    return previous[-1]


def normalized_edit_similarity(prediction: str, reference: str) -> float:
    predicted = normalize(prediction)
    expected = normalize(reference)
    denominator = max(len(predicted), len(expected))
    if denominator == 0:
        return 1.0
    return 1 - levenshtein_distance(predicted, expected) / denominator


def token_jaccard_similarity(prediction: str, reference: str) -> float:
    predicted = set(tokenize(prediction))
    expected = set(tokenize(reference))
    union = predicted | expected
    if not union:
        return 1.0
    return len(predicted & expected) / len(union)


def lcs_length(left: list[str], right: list[str]) -> int:
    if len(left) < len(right):
        left, right = right, left
    previous = [0] * (len(right) + 1)
    for left_token in left:
        current = [0]
        for index, right_token in enumerate(right, start=1):
            if left_token == right_token:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    return previous[-1]


def rouge_l_f1(prediction: str, reference: str) -> float:
    predicted = tokenize(prediction)
    expected = tokenize(reference)
    if not predicted and not expected:
        return 1.0
    if not predicted or not expected:
        return 0.0
    overlap = lcs_length(predicted, expected)
    return f1(overlap / len(predicted), overlap / len(expected))


def ngrams(text: str, order: int) -> Counter[str]:
    return Counter(text[index : index + order] for index in range(len(text) - order + 1))


def character_ngram_f1(prediction: str, reference: str, max_order: int = 6) -> float:
    predicted_text = "".join(normalize(prediction).split())
    expected_text = "".join(normalize(reference).split())
    if not predicted_text and not expected_text:
        return 1.0

    precisions: list[float] = []
    recalls: list[float] = []
    for order in range(1, max_order + 1):
        predicted = ngrams(predicted_text, order)
        expected = ngrams(expected_text, order)
        if not predicted and not expected:
            continue
        overlap = sum((predicted & expected).values())
        precisions.append(overlap / sum(predicted.values()) if predicted else 0.0)
        recalls.append(overlap / sum(expected.values()) if expected else 0.0)
    if not precisions:
        return 0.0
    return f1(sum(precisions) / len(precisions), sum(recalls) / len(recalls))


def line_count(text: str) -> int:
    return sum(bool(line.strip()) for line in text.splitlines())


def mean(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        raise EvaluationError("Cannot score an empty dataset")
    return sum(values) / len(values)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file():
        raise EvaluationError(f"File not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames is None:
            raise EvaluationError(f"CSV is empty: {path}")
        rows = []
        try:
            for row in reader:
                if None in row:
                    raise EvaluationError(
                        f"CSV record ending at line {reader.line_num} in {path} "
                        "has extra fields"
                    )
                missing = [field for field, value in row.items() if value is None]
                if missing:
                    raise EvaluationError(
                        f"CSV record ending at line {reader.line_num} in {path} "
                        f"is missing fields: {missing}"
                    )
                rows.append(row)
        except csv.Error as error:
            raise EvaluationError(f"Malformed CSV in {path}: {error}") from error
        return reader.fieldnames, rows


def index_rows(
    rows: list[dict[str, str]], source: Path
) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        case_id = row.get("id", "")
        if not case_id:
            raise EvaluationError(f"Blank or missing id in {source}")
        if case_id in indexed:
            raise EvaluationError(f"Duplicate id {case_id!r} in {source}")
        indexed[case_id] = row
    return indexed


def require_same_ids(
    expected: list[str], actual: list[str], source: Path
) -> None:
    missing = set(expected) - set(actual)
    extra = set(actual) - set(expected)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing {len(missing)} IDs")
        if extra:
            details.append(f"has {len(extra)} unexpected IDs")
        raise EvaluationError(f"{source} " + " and ".join(details))


def evaluate(
    prediction_path: Path,
    reference_path: Path,
    input_path: Path | None = None,
) -> dict[str, object]:
    prediction_columns, prediction_rows = read_csv(prediction_path)
    if prediction_columns != PREDICTION_COLUMNS:
        raise EvaluationError(
            f"Expected prediction columns {PREDICTION_COLUMNS}, found {prediction_columns}"
        )
    _, reference_rows = read_csv(reference_path)
    if not reference_rows or "tst_2025" not in reference_rows[0]:
        raise EvaluationError(f"References must contain id and tst_2025: {reference_path}")

    predictions = index_rows(prediction_rows, prediction_path)
    references = index_rows(reference_rows, reference_path)
    case_ids = [row["id"] for row in reference_rows]
    require_same_ids(case_ids, list(predictions), prediction_path)
    if any(not predictions[case_id]["predicted_tst_2025"].strip() for case_id in case_ids):
        raise EvaluationError("Predictions must be nonblank")

    if "tst_2024" in reference_rows[0]:
        inputs = references
    else:
        if input_path is None:
            raise EvaluationError(
                "References do not contain tst_2024; provide --inputs"
            )
        _, input_rows = read_csv(input_path)
        inputs = index_rows(input_rows, input_path)
        require_same_ids(case_ids, list(inputs), input_path)
        if "tst_2024" not in input_rows[0]:
            raise EvaluationError(f"Inputs must contain id and tst_2024: {input_path}")

    predicted = [predictions[case_id]["predicted_tst_2025"] for case_id in case_ids]
    expected = [references[case_id]["tst_2025"] for case_id in case_ids]
    source = [inputs[case_id]["tst_2024"] for case_id in case_ids]

    prediction_source_similarity = [
        rouge_l_f1(prediction, earlier)
        for prediction, earlier in zip(predicted, source)
    ]
    observed_source_similarity = [
        rouge_l_f1(reference, earlier)
        for reference, earlier in zip(expected, source)
    ]

    metric_functions: dict[str, Callable[[str, str], float]] = {
        "normalized_edit_similarity": normalized_edit_similarity,
        "token_jaccard_similarity": token_jaccard_similarity,
        "token_overlap_f1": token_overlap_f1,
        "rouge_l_f1": rouge_l_f1,
        "character_ngram_f1": character_ngram_f1,
    }
    metrics = {
        "normalized_exact_match_rate": mean(
            float(normalize(prediction) == normalize(reference))
            for prediction, reference in zip(predicted, expected)
        ),
        **{
            name: mean(
                function(prediction, reference)
                for prediction, reference in zip(predicted, expected)
            )
            for name, function in metric_functions.items()
        },
        "word_count_mae": mean(
            abs(len(tokenize(prediction)) - len(tokenize(reference)))
            for prediction, reference in zip(predicted, expected)
        ),
        "line_count_mae": mean(
            abs(line_count(prediction) - line_count(reference))
            for prediction, reference in zip(predicted, expected)
        ),
        "prediction_word_count_mean": mean(len(tokenize(text)) for text in predicted),
        "reference_word_count_mean": mean(len(tokenize(text)) for text in expected),
        "prediction_repeat_2024_rate": mean(
            float(normalize(prediction) == normalize(earlier))
            for prediction, earlier in zip(predicted, source)
        ),
        "observed_repeat_2024_rate": mean(
            float(normalize(reference) == normalize(earlier))
            for reference, earlier in zip(expected, source)
        ),
        "source_similarity_mae": mean(
            abs(prediction_value - observed_value)
            for prediction_value, observed_value in zip(
                prediction_source_similarity, observed_source_similarity
            )
        ),
        "prediction_source_similarity_mean": mean(prediction_source_similarity),
        "observed_source_similarity_mean": mean(observed_source_similarity),
    }

    return {
        "cases": len(case_ids),
        "predictions": str(prediction_path),
        "references": str(reference_path),
        "metrics": {
            name: {
                "value": round(value, 6),
                "group": METRIC_INFO[name][0],
                "direction": METRIC_INFO[name][1],
                "description": METRIC_INFO[name][2],
            }
            for name, value in metrics.items()
        },
    }


def print_scorecard(scorecard: dict[str, object]) -> None:
    print(f"Cases: {scorecard['cases']}")
    print("No composite score is calculated.\n")
    metrics = scorecard["metrics"]
    assert isinstance(metrics, dict)
    for group in ("Agreement", "Form", "Change"):
        print(group)
        for name, details in metrics.items():
            if details["group"] != group:
                continue
            direction = {"higher": "higher is better", "lower": "lower is better"}.get(
                details["direction"], "descriptive"
            )
            print(f"  {name}: {details['value']:.6f} ({direction})")
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", type=Path)
    parser.add_argument(
        "--references",
        type=Path,
        default=DEFAULT_REFERENCES,
        help="Labeled CSV containing id and tst_2025 (default: data/dev.csv)",
    )
    parser.add_argument(
        "--inputs",
        type=Path,
        help="CSV containing id and tst_2024 when references omit the source text",
    )
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        scorecard = evaluate(args.predictions, args.references, args.inputs)
    except (OSError, csv.Error, EvaluationError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print_scorecard(scorecard)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(scorecard, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Wrote JSON scorecard to {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
