# You Can Predict Future Selves with AI (or Without AI)

Can we predict how people will describe themselves one year in the future?

This repository contains a small longitudinal prediction task. Each case contains a person's 2024 response to the Twenty Statements Test. The challenge is to predict that same person's 2025 response.

You may use AI. You may use simple rules. You may use statistics, language models, social science theory, vibes, or careful reading. The point is to compare approaches to predicting continuity and change in self-description.

## The task

Given:

- `tst_2024`: a person's Twenty Statements Test response from 2024

Predict:

- `predicted_tst_2025`: your best guess for that same person's Twenty Statements Test response in 2025

## Data files

- `data/train.csv`: 150 examples with 2024 and 2025 text
- `data/dev.csv`: 50 examples with 2024 and 2025 text
- `data/test_input.csv`: 100 examples with 2024 text only
- `data/sample_submission.csv`: expected submission format

## How to participate

1. Fork this repository.
2. Inspect the training and dev data.
3. Create predictions for `data/test_input.csv`.
4. Save your predictions as `submissions/YOUR_NAME_submission.csv`.
5. Describe your method in `submissions/YOUR_NAME_method.md`.
6. Open a pull request.

## Submission format

Your CSV should contain exactly two columns:

```csv
id,predicted_ts_2025
test_0001,"I am..."

## Who? What? Why?

I am [Dr. Jason Jeffrey Jones](https://jasonjones.ninja/).  I study human identity using computational social science.

Since I first read about [Google T5 in 2020](https://research.google/blog/exploring-transfer-learning-with-t5-the-text-to-text-transfer-transformer/), I have wanted to do 'machine translation' of past selves into future selves.

I have not found the time to do anything more than [chip away](https://jasonjones.ninja/papers/Rogers-Jones-2025-Trends-in-Identity-Transition-Using-Social-Media-Bios.pdf) [small](https://jasonjones.ninja/misc/slides-Jones-Predicting-the-Self.pdf) [flakes](https://jasonjones.ninja/papers/Tosolini-and-Jones-2026-From-Tumblr-to-Twitter.pdf) from that tempting slab of marble, however.

I still don't have time, so it's your turn.

The reason to attempt this is to approach a BIG, hard-to-define question: Do human lives follow predictable courses? through a SMALL, completely-defined task.

*You can Predict Future Selves with AI (or Without AI).*
