# Day 3 PCAS Summary

PCAS policy: short prompts use 10 steps and guidance 4.0, medium prompts use 20 steps and guidance 4.5, long prompts use 28 steps and guidance 5.0. Resolution is fixed at 512x512 for this first comparison.

The no-warmup column excludes the first prompt of each run.

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
| pcas | all | 30 | 19.333 | 4.500 | 0.977 | 6.979 |
| pcas | 10_words | 10 | 10.000 | 4.000 | 0.593 | 6.979 |
| pcas | 30_words | 10 | 20.000 | 4.500 | 0.988 | 6.979 |
| pcas | 50_words | 10 | 28.000 | 5.000 | 1.312 | 6.979 |

## PCAS vs Fixed-20

| Prompt group | PCAS steps | Fixed-20 steps | Step saving | PCAS time (s) | Fixed-20 time (s) | Time saving |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 19.333 | 20.000 | 3.333% | 0.977 | 0.996 | 1.916% |
| 10_words | 10.000 | 20.000 | 50.000% | 0.593 | 1.019 | 41.816% |
| 30_words | 20.000 | 20.000 | 0.000% | 0.988 | 0.972 | -1.668% |
| 50_words | 28.000 | 20.000 | -40.000% | 1.312 | 1.001 | -31.175% |
