# LLM Prompt Baseline

This baseline asks a language model to predict the later response from the
earlier response without fine-tuning. Run it once for every row in
`data/test_input.csv`, substituting the row's `tst_2024` value.

## System message

```text
You predict how the same person will answer the Twenty Statements Test at a
later wave. Return only the predicted response, with no explanation or framing.
Do not invent names or other identifying details.
```

## User message

```text
The following is one person's response to the Twenty Statements Test in 2024.
Predict that same person's response at a follow-up collected 14 to 25 months
later. Preserve statements likely to remain stable, make only plausible changes,
and match the original level of detail and writing style.

2024 response:
<tst_2024>
```

Write the returned text to `predicted_tst_2025`. Record the provider, model,
model version, generation parameters, prompt changes, and run date in the
submission's method file. Do not send the demographic metadata unless the
method explicitly intends to use it and documents that choice.
