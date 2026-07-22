# Evaluation

## Policy

Future Selves is an open methods demonstration project. Predictions are
compared with an automated scorecard containing multiple metrics. The project
does not calculate a composite score, assign metric weights, rank submissions,
or declare an overall winner.

People may use the released data and evaluator to benchmark models or software
harnesses. The Future Selves project does not maintain those benchmarks,
certify comparisons, or take responsibility for rankings produced elsewhere.

Each person has only one observed follow-up response, even though many future
self-descriptions could have been plausible. Reference-based metrics therefore
describe agreement with the observed response; they do not establish that one
prediction was the only reasonable future or measure prediction quality in its
entirety.

The initial scorecard is dependency-free and deterministic. It does not use a
hosted API or a pretrained semantic model. Methods may report additional
automated evaluations, but they should distinguish those results from the
shared scorecard and document all models, versions, parameters, and data used.

## Shared scorecard

Metrics are calculated separately for each case and macro-averaged unless the
description says otherwise.

| Group | Metric | Direction | Meaning |
| --- | --- | --- | --- |
| Agreement | `normalized_exact_match_rate` | Higher | Fraction exactly matching the observed follow-up after case and whitespace normalization |
| Agreement | `normalized_edit_similarity` | Higher | One minus character-level Levenshtein distance divided by the longer normalized string length |
| Agreement | `token_jaccard_similarity` | Higher | Intersection divided by union for the unique token sets in the prediction and observed follow-up |
| Agreement | `token_overlap_f1` | Higher | Bag-of-words token overlap F1 with the observed follow-up |
| Agreement | `rouge_l_f1` | Higher | Longest-common-subsequence token F1 with the observed follow-up |
| Agreement | `character_ngram_f1` | Higher | Character 1- through 6-gram overlap F1 with the observed follow-up |
| Form | `word_count_mae` | Lower | Mean absolute error in word count |
| Form | `line_count_mae` | Lower | Mean absolute error in nonblank line count |
| Form | `prediction_word_count_mean` | Descriptive | Mean predicted word count |
| Form | `reference_word_count_mean` | Descriptive | Mean observed follow-up word count |
| Change | `prediction_repeat_2024_rate` | Descriptive | Fraction of predictions that repeat the 2024 response |
| Change | `observed_repeat_2024_rate` | Descriptive | Fraction of observed follow-ups that repeat the 2024 response |
| Change | `source_similarity_mae` | Lower | Error in predicting how similar the follow-up will be to the 2024 response |
| Change | `prediction_source_similarity_mean` | Descriptive | Mean ROUGE-L similarity between predictions and 2024 responses |
| Change | `observed_source_similarity_mean` | Descriptive | Mean ROUGE-L similarity between observed follow-ups and 2024 responses |

All agreement metrics range from 0 to 1. Normalized edit similarity respects
character order and measures the fraction of character edits avoided relative
to the longer text. Token Jaccard ignores order and repetition: each distinct
token appears at most once in the intersection and union. By contrast,
`token_overlap_f1` counts repeated tokens, while `rouge_l_f1` rewards token
order through a longest common subsequence.

`source_similarity_mae` is the mean absolute difference between a prediction's
ROUGE-L similarity to the 2024 response and the observed follow-up's ROUGE-L
similarity to that response. It measures whether a method predicts roughly the
observed amount of textual continuity or change; it does not evaluate whether
the specific changes are correct.

No metric should be treated as a substitute for the others. Descriptive
measures have no preferred direction.

## Text processing

- Exact-match comparison applies Unicode case folding and collapses whitespace.
- Normalized edit similarity applies Levenshtein distance to that normalized
  character sequence and divides by the longer sequence length.
- Token metrics use case-folded Unicode word tokens and retain internal
  apostrophes.
- Token Jaccard uses unique token sets; token-overlap F1 uses token frequencies.
- Character n-gram comparison removes whitespace after normalization.
- Line counts include nonblank lines only.
- Empty predictions are invalid and are never scored.

The implementation in `scripts/evaluate_predictions.py` is authoritative for
the shared scorecard.

## Evaluate development predictions

Prepare a CSV with the same two-column format as a test submission, using the
50 development IDs. Then run:

```bash
python3 scripts/evaluate_predictions.py path/to/dev_predictions.csv
```

Write a machine-readable copy with:

```bash
python3 scripts/evaluate_predictions.py path/to/dev_predictions.csv \
  --json-output path/to/scorecard.json
```

The repeat-2024 development results are recorded in
[`baselines/repeat_2024_dev_scorecard.md`](../baselines/repeat_2024_dev_scorecard.md).

## Evaluate test predictions

Test references and follow-up demographics are private. The organizer runs:

```bash
python3 scripts/evaluate_predictions.py submissions/NAME_submission.csv \
  --references private/derived/test_key.csv \
  --inputs data/test_input.csv \
  --json-output private/scorecards/NAME.json
```

Every submitted method receives the same complete scorecard. Test references
must not be used for model selection, prompt revision, or repeated tuning.
