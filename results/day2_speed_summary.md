# Day 2 Fixed-Step Baseline Speed Summary

Model: `Efficient-Large-Model/Sana_600M_512px_diffusers` at 512x512.

Prompt benchmark: 10 prompts with 10 words, 10 prompts with 30 words, and 10 prompts with 50 words.

The no-warmup column excludes the first prompt of each fixed-step run, because it includes extra CUDA/runtime warm-up noise.

| Method | Prompt group | Prompts | Avg words | Avg time (s) | Avg time no-warmup (s) | Max time (s) | Avg peak VRAM (GB) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fixed_10 | all | 30 | 30.000 | 0.580 | 0.525 | 2.167 | 6.979 |
| fixed_10 | 10_words | 10 | 10.000 | 0.691 | 0.527 | 2.167 | 6.979 |
| fixed_10 | 30_words | 10 | 30.000 | 0.525 | 0.525 | 0.530 | 6.979 |
| fixed_10 | 50_words | 10 | 50.000 | 0.523 | 0.523 | 0.533 | 6.979 |
| fixed_20 | all | 30 | 30.000 | 1.057 | 0.996 | 2.820 | 6.979 |
| fixed_20 | 10_words | 10 | 10.000 | 1.199 | 1.019 | 2.820 | 6.979 |
| fixed_20 | 30_words | 10 | 30.000 | 0.972 | 0.972 | 1.016 | 6.979 |
| fixed_20 | 50_words | 10 | 50.000 | 1.001 | 1.001 | 1.022 | 6.979 |
| fixed_28 | all | 30 | 30.000 | 1.389 | 1.335 | 2.950 | 6.979 |
| fixed_28 | 10_words | 10 | 10.000 | 1.468 | 1.304 | 2.950 | 6.979 |
| fixed_28 | 30_words | 10 | 30.000 | 1.365 | 1.365 | 1.462 | 6.979 |
| fixed_28 | 50_words | 10 | 50.000 | 1.333 | 1.333 | 1.407 | 6.979 |
