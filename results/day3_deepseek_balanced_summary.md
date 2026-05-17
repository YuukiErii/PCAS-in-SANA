# DeepSeek-Balanced PCAS Summary

DeepSeek-Balanced PCAS keeps the same cached DeepSeek semantic complexity labels, but applies a budget-constrained policy: low=8 steps, medium=16 steps, high=22 steps. This addresses the original DeepSeek-PCAS being too conservative and slower than Fixed-20.

## DeepSeek Label Counts

| Method | Low | Medium | High |
| --- | ---: | ---: | ---: |
| deepseek_pcas_7_3 | 5 | 6 | 19 |
| deepseek_balanced_pcas | 5 | 6 | 19 |

## Speed Summary

| Method | Group | Prompts | Avg steps | Avg guidance | Avg time no-warmup (s) | Avg peak VRAM (GB) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| fixed_20 | all | 30 | 20.000 | 4.500 | 0.996 | 6.979 |
| fixed_20 | 10_words | 10 | 20.000 | 4.500 | 1.019 | 6.979 |
| fixed_20 | 30_words | 10 | 20.000 | 4.500 | 0.972 | 6.979 |
| fixed_20 | 50_words | 10 | 20.000 | 4.500 | 1.001 | 6.979 |
| deepseek_pcas_7_3 | all | 30 | 23.400 | 4.733 | 1.303 | 6.979 |
| deepseek_pcas_7_3 | 10_words | 10 | 15.000 | 4.250 | 0.940 | 6.979 |
| deepseek_pcas_7_3 | 30_words | 10 | 27.200 | 4.950 | 1.420 | 6.979 |
| deepseek_pcas_7_3 | 50_words | 10 | 28.000 | 5.000 | 1.514 | 6.979 |
| deepseek_balanced_pcas | all | 30 | 18.467 | 4.587 | 0.844 | 6.979 |
| deepseek_balanced_pcas | 10_words | 10 | 12.000 | 4.200 | 0.614 | 6.979 |
| deepseek_balanced_pcas | 30_words | 10 | 21.400 | 4.760 | 0.928 | 6.979 |
| deepseek_balanced_pcas | 50_words | 10 | 22.000 | 4.800 | 0.966 | 6.979 |

## Compared With Fixed-20

| Method | Group | Avg steps | Step saving | Avg time (s) | Time saving |
| --- | --- | ---: | ---: | ---: | ---: |
| deepseek_pcas_7_3 | all | 23.400 | -17.000% | 1.303 | -30.823% |
| deepseek_pcas_7_3 | 10_words | 15.000 | 25.000% | 0.940 | 7.748% |
| deepseek_pcas_7_3 | 30_words | 27.200 | -36.000% | 1.420 | -46.073% |
| deepseek_pcas_7_3 | 50_words | 28.000 | -40.000% | 1.514 | -51.365% |
| deepseek_balanced_pcas | all | 18.467 | 7.667% | 0.844 | 15.298% |
| deepseek_balanced_pcas | 10_words | 12.000 | 40.000% | 0.614 | 39.715% |
| deepseek_balanced_pcas | 30_words | 21.400 | -7.000% | 0.928 | 4.495% |
| deepseek_balanced_pcas | 50_words | 22.000 | -10.000% | 0.966 | 3.410% |

## Interpretation

- The original DeepSeek-PCAS is semantically useful but too conservative: because 19 of 30 prompts are labeled high, its 28-step high policy makes it slower than Fixed-20.
- DeepSeek-Balanced keeps the same semantic labels but lowers the action taken for each label, especially high prompts.
- This turns DeepSeek from a quality-conservative strategy into a budget-constrained semantic scheduler.
