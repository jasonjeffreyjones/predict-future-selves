from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "baselines"))
sys.path.insert(0, str(ROOT / "scripts"))

import baseline_repeat_2024 as repeat_baseline  # noqa: E402
import evaluate_predictions as evaluation  # noqa: E402


LABELED_COLUMNS = [
    "id",
    "tst_2024",
    "age_2024",
    "sex_2024",
    "ethnicity_simplified_2024",
    "country_of_birth_2024",
    "country_of_residence_2024",
    "nationality_2024",
    "language_2024",
    "student_status_2024",
    "employment_status_2024",
    "fluent_languages_2024",
    "tst_2025",
    "age_2025",
    "sex_2025",
    "ethnicity_simplified_2025",
    "country_of_birth_2025",
    "country_of_residence_2025",
    "nationality_2025",
    "language_2025",
    "student_status_2025",
    "employment_status_2025",
]
INPUT_COLUMNS = LABELED_COLUMNS[:12]
SUBMISSION_COLUMNS = ["id", "predicted_tst_2025"]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        return reader.fieldnames or [], list(reader)


class PublicReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.train_columns, cls.train = read_csv(ROOT / "data" / "train.csv")
        cls.dev_columns, cls.dev = read_csv(ROOT / "data" / "dev.csv")
        cls.test_columns, cls.test = read_csv(ROOT / "data" / "test_input.csv")
        cls.sample_columns, cls.sample = read_csv(
            ROOT / "data" / "sample_submission.csv"
        )

    def test_counts_and_schemas(self) -> None:
        self.assertEqual(len(self.train), 150)
        self.assertEqual(len(self.dev), 50)
        self.assertEqual(len(self.test), 81)
        self.assertEqual(len(self.sample), 81)
        self.assertEqual(self.train_columns, LABELED_COLUMNS)
        self.assertEqual(self.dev_columns, LABELED_COLUMNS)
        self.assertEqual(self.test_columns, INPUT_COLUMNS)
        self.assertEqual(self.sample_columns, SUBMISSION_COLUMNS)

    def test_ids_are_unique_and_partitioned(self) -> None:
        groups = [
            {row["id"] for row in self.train},
            {row["id"] for row in self.dev},
            {row["id"] for row in self.test},
        ]
        self.assertEqual([len(group) for group in groups], [150, 50, 81])
        self.assertFalse(groups[0] & groups[1])
        self.assertFalse(groups[0] & groups[2])
        self.assertFalse(groups[1] & groups[2])

    def test_sample_is_repeat_2024_baseline(self) -> None:
        self.assertEqual(
            [row["id"] for row in self.sample], [row["id"] for row in self.test]
        )
        self.assertEqual(
            [row["predicted_tst_2025"] for row in self.sample],
            [row["tst_2024"] for row in self.test],
        )

    def test_public_values_are_normalized(self) -> None:
        all_rows = self.train + self.dev + self.test
        self.assertTrue(all(row["tst_2024"].strip() for row in all_rows))
        self.assertTrue(all(row["tst_2025"].strip() for row in self.train + self.dev))
        self.assertFalse(
            any(
                value.upper() in {"DATA_EXPIRED", "N/A", "NA", "NULL", "NONE"}
                for row in all_rows
                for value in row.values()
            )
        )

    def test_repeat_baseline_scorecard_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            predictions = Path(temporary_directory) / "dev_predictions.csv"
            repeat_baseline.make_predictions(ROOT / "data" / "dev.csv", predictions)
            scorecard = evaluation.evaluate(predictions, ROOT / "data" / "dev.csv")
        metrics = scorecard["metrics"]
        expected = {
            "normalized_exact_match_rate": 0.0,
            "normalized_edit_similarity": 0.291966,
            "token_jaccard_similarity": 0.14193,
            "token_overlap_f1": 0.312202,
            "rouge_l_f1": 0.225683,
            "character_ngram_f1": 0.296534,
            "word_count_mae": 56.68,
            "line_count_mae": 6.8,
            "prediction_word_count_mean": 108.04,
            "reference_word_count_mean": 94.76,
            "prediction_repeat_2024_rate": 1.0,
            "observed_repeat_2024_rate": 0.0,
            "source_similarity_mae": 0.774317,
            "prediction_source_similarity_mean": 1.0,
            "observed_source_similarity_mean": 0.225683,
        }
        self.assertEqual(
            {name: details["value"] for name, details in metrics.items()}, expected
        )


if __name__ == "__main__":
    unittest.main()
