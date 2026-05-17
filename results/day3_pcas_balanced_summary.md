# Balanced-PCAS Speed Summary

Balanced-PCAS is introduced to solve the small overall speed gain of the original Rule-PCAS. It uses a fixed average-step budget below Fixed-20: short prompts use 8 steps, medium prompts use 16 steps, and long prompts use 24 steps.

| Method | Group | Prompts | Avg steps | Avg guidance | Avg time no-warmup (s) | Avg peak VRAM (GB) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| fixed_20 | all | 30 | 20.000 | 4.500 | 0.996 | 6.979 |
| fixed_20 | 10_words | 10 | 20.000 | 4.500 | 1.019 | 6.979 |
| fixed_20 | 30_words | 10 | 20.000 | 4.500 | 0.972 | 6.979 |
| fixed_20 | 50_words | 10 | 20.000 | 4.500 | 1.001 | 6.979 |
| rule_pcas_7_2 | all | 30 | 19.333 | 4.500 | 0.977 | 6.979 |
| rule_pcas_7_2 | 10_words | 10 | 10.000 | 4.000 | 0.593 | 6.979 |
| rule_pcas_7_2 | 30_words | 10 | 20.000 | 4.500 | 0.988 | 6.979 |
| rule_pcas_7_2 | 50_words | 10 | 28.000 | 5.000 | 1.312 | 6.979 |
| balanced_pcas | all | 30 | 16.000 | 4.400 | 0.751 | 6.979 |
| balanced_pcas | 10_words | 10 | 8.000 | 4.000 | 0.465 | 6.979 |
| balanced_pcas | 30_words | 10 | 16.000 | 4.400 | 0.737 | 6.979 |
| balanced_pcas | 50_words | 10 | 24.000 | 4.800 | 1.023 | 6.979 |

## Compared With Fixed-20

| Method | Group | Avg steps | Step saving | Avg time (s) | Time saving |
| --- | --- | ---: | ---: | ---: | ---: |
| rule_pcas_7_2 | all | 19.333 | 3.333% | 0.977 | 1.916% |
| rule_pcas_7_2 | 10_words | 10.000 | 50.000% | 0.593 | 41.816% |
| rule_pcas_7_2 | 30_words | 20.000 | 0.000% | 0.988 | -1.668% |
| rule_pcas_7_2 | 50_words | 28.000 | -40.000% | 1.312 | -31.175% |
| balanced_pcas | all | 16.000 | 20.000% | 0.751 | 24.588% |
| balanced_pcas | 10_words | 8.000 | 60.000% | 0.465 | 54.321% |
| balanced_pcas | 30_words | 16.000 | 20.000% | 0.737 | 24.153% |
| balanced_pcas | 50_words | 24.000 | -20.000% | 1.023 | -2.241% |

## Interpretation

- The original Rule-PCAS mainly reallocates compute: it saves time on short prompts but spends extra time on long prompts, so the balanced 10/30/50 benchmark has only a small overall speed gain.
- Balanced-PCAS constrains every group below Fixed-20, so its overall speed gain is much larger and easier to report as an efficiency-oriented PCAS variant.
- The trade-off is that long prompts now receive 24 rather than 28 steps, so this variant should be framed as efficiency-first. A follow-up quality check is needed before replacing the original PCAS in the main quality discussion.
