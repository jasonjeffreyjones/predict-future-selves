from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_predictions as evaluation  # noqa: E402
import validate_submission as validation  # noqa: E402


PREDICTION_HEADER = ["id", "predicted_tst_2025"]


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


class SubmissionValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)
        self.sample = self.directory / "sample.csv"
        write_csv(
            self.sample,
            PREDICTION_HEADER,
            [["test_0001", "reference one"], ["test_0002", "reference two"]],
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def submission(self, rows: list[list[str]], header=None) -> Path:
        path = self.directory / "submission.csv"
        write_csv(path, header or PREDICTION_HEADER, rows)
        return path

    def test_accepts_valid_submission(self) -> None:
        path = self.submission(
            [["test_0001", "prediction one"], ["test_0002", "prediction two"]]
        )
        self.assertEqual(validation.validate(path, self.sample), 2)

    def test_rejects_extra_row_field(self) -> None:
        path = self.submission(
            [
                ["test_0001", "prediction", "unexpected"],
                ["test_0002", "prediction two"],
            ]
        )
        with self.assertRaisesRegex(validation.ValidationError, "extra fields"):
            validation.validate(path, self.sample)

    def test_rejects_missing_row_field(self) -> None:
        path = self.submission(
            [["test_0001"], ["test_0002", "prediction two"]]
        )
        with self.assertRaisesRegex(validation.ValidationError, "missing fields"):
            validation.validate(path, self.sample)

    def test_rejects_blank_prediction(self) -> None:
        path = self.submission(
            [["test_0001", ""], ["test_0002", "prediction two"]]
        )
        with self.assertRaisesRegex(validation.ValidationError, "Blank predictions"):
            validation.validate(path, self.sample)

    def test_rejects_duplicate_id(self) -> None:
        path = self.submission(
            [["test_0001", "one"], ["test_0001", "two"]]
        )
        with self.assertRaisesRegex(validation.ValidationError, "duplicate IDs"):
            validation.validate(path, self.sample)

    def test_rejects_duplicate_header(self) -> None:
        path = self.submission(
            [["test_0001", "one"]], header=["id", "id"]
        )
        with self.assertRaisesRegex(validation.ValidationError, "Expected columns"):
            validation.validate(path, self.sample)

    def test_rejects_malformed_quoting(self) -> None:
        path = self.directory / "submission.csv"
        path.write_text(
            'id,predicted_tst_2025\ntest_0001,"unterminated\n', encoding="utf-8"
        )
        with self.assertRaisesRegex(validation.ValidationError, "Malformed CSV"):
            validation.validate(path, self.sample)


class EvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)
        self.references = self.directory / "references.csv"
        write_csv(
            self.references,
            ["id", "tst_2024", "tst_2025"],
            [
                ["dev_0001", "I am here", "I am still here"],
                ["dev_0002", "I like tea", "I like coffee"],
            ],
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def predictions(self, rows: list[list[str]]) -> Path:
        path = self.directory / "predictions.csv"
        write_csv(path, PREDICTION_HEADER, rows)
        return path

    def test_scores_valid_predictions(self) -> None:
        path = self.predictions(
            [
                ["dev_0001", "I am still here"],
                ["dev_0002", "I like coffee"],
            ]
        )
        scorecard = evaluation.evaluate(path, self.references)
        self.assertEqual(scorecard["cases"], 2)
        metrics = scorecard["metrics"]
        self.assertEqual(metrics["normalized_exact_match_rate"]["value"], 1.0)
        self.assertEqual(metrics["rouge_l_f1"]["value"], 1.0)
        self.assertEqual(metrics["word_count_mae"]["value"], 0.0)

    def test_rejects_extra_row_field(self) -> None:
        path = self.predictions(
            [
                ["dev_0001", "prediction", "unexpected"],
                ["dev_0002", "prediction two"],
            ]
        )
        with self.assertRaisesRegex(evaluation.EvaluationError, "extra fields"):
            evaluation.evaluate(path, self.references)

    def test_rejects_missing_row_field(self) -> None:
        path = self.predictions(
            [["dev_0001"], ["dev_0002", "prediction two"]]
        )
        with self.assertRaisesRegex(evaluation.EvaluationError, "missing fields"):
            evaluation.evaluate(path, self.references)

    def test_private_style_references_require_inputs(self) -> None:
        references = self.directory / "key.csv"
        write_csv(
            references,
            ["id", "tst_2025"],
            [["dev_0001", "later one"], ["dev_0002", "later two"]],
        )
        path = self.predictions(
            [["dev_0001", "prediction one"], ["dev_0002", "prediction two"]]
        )
        with self.assertRaisesRegex(evaluation.EvaluationError, "provide --inputs"):
            evaluation.evaluate(path, references)

    def test_metric_fixtures(self) -> None:
        self.assertEqual(
            evaluation.normalized_edit_similarity("Same text", "same   text"), 1.0
        )
        self.assertAlmostEqual(
            evaluation.normalized_edit_similarity("kitten", "sitting"), 4 / 7
        )
        self.assertAlmostEqual(
            evaluation.token_jaccard_similarity("alpha beta", "beta gamma"),
            1 / 3,
        )
        self.assertEqual(evaluation.token_overlap_f1("same text", "same text"), 1.0)
        self.assertEqual(evaluation.token_overlap_f1("alpha", "beta"), 0.0)
        self.assertAlmostEqual(evaluation.rouge_l_f1("a b", "a c"), 0.5)
        self.assertEqual(
            evaluation.character_ngram_f1("Same text", "same   text"), 1.0
        )
        self.assertEqual(evaluation.line_count("one\n\n two "), 2)


if __name__ == "__main__":
    unittest.main()
