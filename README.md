# You Can Predict Future Selves with AI (or Without AI)

Can we predict how people will describe themselves at a later longitudinal
follow-up?

This repository contains a small longitudinal prediction benchmark. Each case
contains a person's 2024 response to the
[Twenty Statements Test](https://soci101.org/applications/twenty.html). The
task is to predict that same person's response at the longitudinal follow-up
wave, collected beginning in 2025.

You may use AI, simple rules, statistics, social-science theory, careful
reading, or combinations of these approaches. The point is to compare methods
for predicting continuity and change in self-description.

## Task

Given:

- `tst_2024`: a person's Twenty Statements Test response from 2024
- demographic metadata measured in 2024

Predict:

- `predicted_tst_2025`: that person's Twenty Statements Test response at the
  follow-up wave

The frozen benchmark contains 281 people with approved, complete responses in
both waves. No Prolific participant IDs, submission IDs, Qualtrics response
IDs, IP addresses, or other administrative identifiers appear in the public
data.

## Data files

- `data/train.csv`: 150 examples with 2024 and follow-up text and demographics
- `data/dev.csv`: 50 examples with 2024 and follow-up text and demographics
- `data/test_input.csv`: 81 examples with 2024 text and demographics only
- `data/sample_submission.csv`: valid test IDs and the required submission
  format, populated with the repeat-2024 baseline

Train and development files contain the available demographic fields from both
waves. Follow-up demographics for test cases are withheld with the test text so
that the held-out task remains prospective. Missing, expired, or invalid
demographic values are represented by empty fields.

See [the data statement](docs/data_statement.md) for provenance, columns,
missingness, cross-wave consistency, and limitations.

## Try the baseline

The simplest prediction is that the person's response will not change:

```bash
python3 baselines/baseline_repeat_2024.py
python3 scripts/validate_submission.py submissions/repeat_2024_submission.csv
```

The language-model prompt baseline is documented in
[`baselines/baseline_llm_prompt.md`](baselines/baseline_llm_prompt.md).

## Evaluation

Methods are compared using an automated multi-metric scorecard. There is no
composite score, metric weighting, ranking, or overall winner. The scorecard
reports agreement with the observed follow-up, response-form error, and how
well a method predicts the amount of continuity or change from 2024.

Others may use the data and evaluator to benchmark models or harnesses, but
maintaining those benchmarks or rankings is not the purpose or responsibility
of this project.

Evaluate development predictions with:

```bash
python3 scripts/evaluate_predictions.py path/to/dev_predictions.csv
```

See [docs/evaluation.md](docs/evaluation.md) for metric definitions,
interpretation, baseline results, and the private test procedure.

## Participate

1. Fork this repository.
2. Inspect the training and development data.
3. Create predictions for every row in `data/test_input.csv`.
4. Save predictions as `submissions/YOUR_NAME_submission.csv`.
5. Describe the method in `submissions/YOUR_NAME_method.md`.
6. Validate the CSV with `scripts/validate_submission.py`.
7. Open a pull request.

Full instructions are in [docs/participation.md](docs/participation.md).

## Licensing

The public benchmark CSV files in `data/` are licensed under the
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
License](DATA_LICENSE.md) (CC BY-NC-SA 4.0).

Source code, documentation, prompts, and other non-data repository materials
are licensed under the [MIT License](LICENSE).

## Submission format

The CSV must contain exactly these two columns and all 81 test IDs in the order
provided by `data/sample_submission.csv`:

```csv
id,predicted_tst_2025
test_0001,"I am..."
```

## Why this benchmark?

I am [Dr. Jason Jeffrey Jones](https://jasonjones.ninja/), and I study human
identity using computational social science.

Since reading about
[Google T5 in 2020](https://research.google/blog/exploring-transfer-learning-with-t5-the-text-to-text-transfer-transformer/),
I have wanted to try "machine translation" of past selves into future selves.
This benchmark approaches a large, hard-to-define question, "Do human lives
follow predictable courses?", through a small, completely defined task.

*You can Predict Future Selves with AI (or Without AI).*
