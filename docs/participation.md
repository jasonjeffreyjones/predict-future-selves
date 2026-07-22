# Participation Guide

## Goal

For every case in `data/test_input.csv`, predict the same person's Twenty
Statements Test response at the longitudinal follow-up wave. The core input is
the 2024 response in `tst_2024`; 2024 demographic metadata is also available.

## Prepare a submission

Create a UTF-8 CSV with exactly two columns:

```csv
id,predicted_tst_2025
test_0001,"I am..."
```

Requirements:

- Include each of the 81 IDs from `data/sample_submission.csv` exactly once.
- Keep IDs in the same order as the sample submission.
- Supply a nonblank prediction for every case.
- Quote or escape commas, quotation marks, and line breaks according to normal
  CSV rules. Python's standard `csv` module or another CSV library is strongly
  recommended.

Validate the result before opening a pull request:

```bash
python3 scripts/validate_submission.py submissions/YOUR_NAME_submission.csv
```

Validation checks format and coverage only; it does not score predictions.

## Evaluate on development data

Development predictions use the same two-column schema with development IDs.
Generate the complete automated scorecard with:

```bash
python3 scripts/evaluate_predictions.py path/to/dev_predictions.csv
```

Future Selves is an open methods demonstration project. The scorecard reports
multiple metrics without combining them, weighting them, ranking methods, or
declaring an overall winner. Report the complete scorecard rather than
selecting only favorable metrics. Metric definitions and interpretation are in
[`docs/evaluation.md`](evaluation.md).

## Document the method

Add `submissions/YOUR_NAME_method.md` describing enough detail to reproduce the
submission. Include, as applicable:

- The prediction approach and any training or retrieval data.
- Whether and how 2024 demographics were used.
- Model provider, exact model/version, and access date.
- Prompt text and generation parameters.
- Random seeds, software versions, and post-processing.
- Any manual review or editing.
- The full shared development scorecard and any additional automated metrics.

Do not include API keys, credentials, private participant data, or hidden test
information.

## Baselines

Generate the repeat-2024 baseline with:

```bash
python3 baselines/baseline_repeat_2024.py
```

This writes `submissions/repeat_2024_submission.csv`. A zero-shot prompt
template is available in `baselines/baseline_llm_prompt.md`.

## Submit

1. Fork the repository and create a branch.
2. Add only the prediction CSV and method Markdown file under `submissions/`.
3. Run the submission validator.
4. Open a pull request summarizing the method.

The organizer returns the complete automated test scorecard for accepted
submissions. The held-out responses are not in the repository. Do not attempt
to identify participants, recover private platform records, or solicit their
follow-up answers.
