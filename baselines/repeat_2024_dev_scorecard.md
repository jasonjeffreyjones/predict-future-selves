# Repeat-2024 Development Scorecard

The repeat-2024 baseline predicts each person's 2024 response verbatim. These
results cover all 50 cases in `data/dev.csv` and were produced by
`scripts/evaluate_predictions.py`.

There is no composite score.

## Agreement

| Metric | Value |
| --- | ---: |
| Normalized exact-match rate | 0.000000 |
| Normalized edit similarity | 0.291966 |
| Token Jaccard similarity | 0.141930 |
| Token-overlap F1 | 0.312202 |
| ROUGE-L F1 | 0.225683 |
| Character n-gram F1 | 0.296534 |

## Form

| Metric | Value |
| --- | ---: |
| Word-count MAE | 56.680000 |
| Line-count MAE | 6.800000 |
| Mean predicted word count | 108.040000 |
| Mean reference word count | 94.760000 |

## Change

| Metric | Value |
| --- | ---: |
| Prediction repeat-2024 rate | 1.000000 |
| Observed repeat-2024 rate | 0.000000 |
| Source-similarity MAE | 0.774317 |
| Mean prediction-to-source similarity | 1.000000 |
| Mean observed follow-up-to-source similarity | 0.225683 |

Reproduce the scorecard with:

```bash
python3 baselines/baseline_repeat_2024.py \
  --input data/dev.csv \
  --output /tmp/repeat_2024_dev.csv
python3 scripts/evaluate_predictions.py /tmp/repeat_2024_dev.csv
```
