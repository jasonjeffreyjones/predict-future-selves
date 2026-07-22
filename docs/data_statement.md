# Data Statement

## Summary

The Future Selves benchmark contains paired responses from 281 people who
completed the Twenty Statements Test in a 2024 study and again in its
longitudinal follow-up wave. Participants were recruited through Prolific and
responded through Qualtrics. They gave informed consent, including notice that
their response data would be made publicly available under a Creative Commons
license. The public benchmark CSVs are released under the
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
License](../DATA_LICENSE.md) (CC BY-NC-SA 4.0).

Detailed methods are available in the manuscript
[*Building the Ipseome: Large, Free, Open, Human Identity Data*](https://arxiv.org/html/2607.02488).

The benchmark was frozen on July 22, 2026. Follow-up collection began in 2025
and continued into 2026; `2025` in public column names denotes the study wave,
not necessarily the response's calendar year. Across the frozen cohort, the
elapsed time between responses ranges from 424 to 750 days, with a median of
433 days. Of the 281 follow-up responses, 248 were recorded in 2025 and 33 in
2026. Exact follow-up timing is not included as a public input feature.

## Inclusion and exclusions

A case is included only when all of the following hold:

- The participant appears in the 2024 Prolific study and its longitudinal
  follow-up study.
- Both Prolific submissions have status `APPROVED`.
- Both submissions link to a finished, consented Qualtrics response.
- Both Qualtrics responses contain nonblank Twenty Statements Test text and the
  public-data notice was displayed.

The independent 2025 cross-sectional cohort and a 10-person pilot are not part
of this benchmark. These rules yield 281 complete longitudinal pairs.

## Source processing

The July 22, 2026 cumulative Qualtrics export is authoritative. The same survey
was reused for all studies and waves, so responses are assigned to waves by
joining Qualtrics `SESSION_ID` to Prolific `Submission id`, not by date.
Participants are linked across waves using private Prolific participant IDs.

When a Prolific submission maps to multiple Qualtrics rows, processing keeps
rows that are finished, consented, and contain nonblank response text. If more
than one qualifying row remains, the latest `RecordedDate` is selected. Two
included 2024 submissions had repeated session IDs, but each had only one
qualifying response.

The later Prolific export is authoritative for 2024 demographics. If one of its
demographic values is blank, `DATA_EXPIRED`, or invalid, processing falls back
to the same field in the original 2024 export. No value is imputed from another
wave. Invalid or unavailable values remaining after this step become empty CSV
fields.

Public IDs are newly assigned within each split. Direct and administrative
identifiers from the source platforms are omitted.

## Splits

The 281 eligible participant IDs are ordered by a fixed SHA-256 hash using the
seed `future-selves-v1-2026-07-22`, then divided into:

| Split | Cases | Public data |
| --- | ---: | --- |
| Train | 150 | 2024 and follow-up text and demographics |
| Development | 50 | 2024 and follow-up text and demographics |
| Test | 81 | 2024 text and demographics |

The test response and follow-up demographic fields remain in a private answer
key. The split is deterministic and is not stratified by demographic fields.

## Public columns

All public benchmark files begin with `id`. Text columns are `tst_2024` and,
for labeled splits, `tst_2025`.

The 2024 demographic columns are:

- `age_2024`
- `sex_2024`
- `ethnicity_simplified_2024`
- `country_of_birth_2024`
- `country_of_residence_2024`
- `nationality_2024`
- `language_2024`
- `student_status_2024`
- `employment_status_2024`
- `fluent_languages_2024`

The follow-up demographic columns use the same base names with a `_2025`
suffix, except that Prolific did not provide `fluent_languages` in the later
export.

## Demographic completeness

Missing counts below are calculated over all 281 frozen cases after 2024
fallback and invalid-value normalization.

| Field | Missing in 2024 | Missing in follow-up |
| --- | ---: | ---: |
| Age | 0 | 0 |
| Sex | 0 | 0 |
| Ethnicity simplified | 0 | 0 |
| Country of birth | 0 | 0 |
| Country of residence | 0 | 0 |
| Nationality | 0 | 0 |
| Language | 1 | 2 |
| Student status | 54 | 152 |
| Employment status | 55 | 152 |
| Fluent languages | 0 | Not collected |

Most missing student and employment values were marked `DATA_EXPIRED` in the
Prolific exports.

## Cross-wave consistency

The following audit compares trimmed, case-normalized values. `Missing either`
means at least one wave lacks a usable value. Differences are left in the
released labeled data rather than silently reconciled.

| Field | Same | Different | Missing either |
| --- | ---: | ---: | ---: |
| Sex | 281 | 0 | 0 |
| Ethnicity simplified | 278 | 3 | 0 |
| Country of birth | 280 | 1 | 0 |
| Country of residence | 281 | 0 | 0 |
| Nationality | 281 | 0 | 0 |
| Language | 279 | 0 | 2 |
| Student status | 112 | 7 | 162 |
| Employment status | 87 | 32 | 162 |

Age is expected to change between waves and is audited separately: 196 cases
increase by one year, 84 increase by two years, and one decreases by 36 years.
The anomalous age pair is retained so the public data reflect the source
records transparently.

Differences may represent real changes, platform-profile updates, response
error, or expired Prolific demographic data. The benchmark does not attempt to
adjudicate those causes.

## Privacy and limitations

The released files contain no source-platform IDs, response IDs, IP addresses,
contact fields, or submission timestamps. The free-text responses and
demographic combinations may nevertheless be sensitive and should not be used
to reidentify participants.

Response length and formatting vary substantially. Under the shared evaluator's
tokenization, included responses range from 3 to 478 words and from 1 to 29
nonblank lines. Some responses are brief or use prose rather than a line-based
list; these source differences are retained rather than filtered or reformatted.

This is a small, selected sample of Prolific participants who completed both
waves and whose submissions were approved. Attrition and platform recruitment
limit generalization. The task measures prediction of self-description text,
not prediction of a person's life course as a whole.
