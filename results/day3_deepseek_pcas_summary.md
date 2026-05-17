# Day 3 DeepSeek-PCAS Summary

This extends Section 7.2 rule-based PCAS with a Section 7.3 DeepSeek-assisted semantic prompt analyzer.

| Method | Prompt group | Prompts | Avg steps | Avg guidance | Avg time no-warmup (s) | Avg peak VRAM (GB) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| fixed_10 | all | 30 | 10.000 | 4.500 | 0.525 | 6.979 |
| fixed_10 | 10_words | 10 | 10.000 | 4.500 | 0.527 | 6.979 |
| fixed_10 | 30_words | 10 | 10.000 | 4.500 | 0.525 | 6.979 |
| fixed_10 | 50_words | 10 | 10.000 | 4.500 | 0.523 | 6.979 |
| fixed_20 | all | 30 | 20.000 | 4.500 | 0.996 | 6.979 |
| fixed_20 | 10_words | 10 | 20.000 | 4.500 | 1.019 | 6.979 |
| fixed_20 | 30_words | 10 | 20.000 | 4.500 | 0.972 | 6.979 |
| fixed_20 | 50_words | 10 | 20.000 | 4.500 | 1.001 | 6.979 |
| fixed_28 | all | 30 | 28.000 | 4.500 | 1.335 | 6.979 |
| fixed_28 | 10_words | 10 | 28.000 | 4.500 | 1.304 | 6.979 |
| fixed_28 | 30_words | 10 | 28.000 | 4.500 | 1.365 | 6.979 |
| fixed_28 | 50_words | 10 | 28.000 | 4.500 | 1.333 | 6.979 |
| rule_pcas_7_2 | all | 30 | 19.333 | 4.500 | 0.977 | 6.979 |
| rule_pcas_7_2 | 10_words | 10 | 10.000 | 4.000 | 0.593 | 6.979 |
| rule_pcas_7_2 | 30_words | 10 | 20.000 | 4.500 | 0.988 | 6.979 |
| rule_pcas_7_2 | 50_words | 10 | 28.000 | 5.000 | 1.312 | 6.979 |
| deepseek_pcas_7_3 | all | 30 | 23.400 | 4.733 | 1.303 | 6.979 |
| deepseek_pcas_7_3 | 10_words | 10 | 15.000 | 4.250 | 0.940 | 6.979 |
| deepseek_pcas_7_3 | 30_words | 10 | 27.200 | 4.950 | 1.420 | 6.979 |
| deepseek_pcas_7_3 | 50_words | 10 | 28.000 | 5.000 | 1.514 | 6.979 |

## PCAS Methods vs Fixed-20

| Method | Group | Avg steps | Fixed-20 steps | Step saving | Avg time (s) | Fixed-20 time (s) | Time saving |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| rule_pcas_7_2 | all | 19.333 | 20.000 | 3.333% | 0.977 | 0.996 | 1.916% |
| rule_pcas_7_2 | 10_words | 10.000 | 20.000 | 50.000% | 0.593 | 1.019 | 41.816% |
| rule_pcas_7_2 | 30_words | 20.000 | 20.000 | 0.000% | 0.988 | 0.972 | -1.668% |
| rule_pcas_7_2 | 50_words | 28.000 | 20.000 | -40.000% | 1.312 | 1.001 | -31.175% |
| deepseek_pcas_7_3 | all | 23.400 | 20.000 | -17.000% | 1.303 | 0.996 | -30.823% |
| deepseek_pcas_7_3 | 10_words | 15.000 | 20.000 | 25.000% | 0.940 | 1.019 | 7.748% |
| deepseek_pcas_7_3 | 30_words | 27.200 | 20.000 | -36.000% | 1.420 | 0.972 | -46.073% |
| deepseek_pcas_7_3 | 50_words | 28.000 | 20.000 | -40.000% | 1.514 | 1.001 | -51.365% |
