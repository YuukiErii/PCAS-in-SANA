# Day6 Calibrated-PCAS CLIPScore Summary

CLIP model: `openai/clip-vit-base-patch32`.

The reported score is cosine similarity between CLIP image and text embeddings multiplied by 100. Higher is better.

| Method | Group | Images | Avg steps | Avg time no-warmup (s) | Avg CLIPScore | Min | Max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fixed_20 | all | 30 | 20.000 | 1.537 | 35.762 | 29.935 | 39.473 |
| fixed_20 | 10_words | 10 | 20.000 | 1.599 | 34.336 | 29.935 | 38.123 |
| fixed_20 | 30_words | 10 | 20.000 | 1.580 | 36.614 | 31.917 | 39.297 |
| fixed_20 | 50_words | 10 | 20.000 | 1.438 | 36.336 | 31.894 | 39.473 |
| balanced_pcas | all | 30 | 16.000 | 1.740 | 35.772 | 30.049 | 39.889 |
| balanced_pcas | 10_words | 10 | 8.000 | 1.102 | 34.065 | 30.049 | 37.685 |
| balanced_pcas | 30_words | 10 | 16.000 | 2.027 | 36.757 | 31.895 | 39.889 |
| balanced_pcas | 50_words | 10 | 24.000 | 2.026 | 36.496 | 32.103 | 39.313 |
| deepseek_balanced_pcas | all | 30 | 18.467 | 2.023 | 35.813 | 30.049 | 39.510 |
| deepseek_balanced_pcas | 10_words | 10 | 12.000 | 0.812 | 34.414 | 30.049 | 38.304 |
| deepseek_balanced_pcas | 30_words | 10 | 21.400 | 3.645 | 36.644 | 31.952 | 39.510 |
| deepseek_balanced_pcas | 50_words | 10 | 22.000 | 1.492 | 36.381 | 31.643 | 39.246 |
| calibrated_pcas | all | 30 | 10.667 | 0.675 | 36.234 | 30.499 | 40.531 |
| calibrated_pcas | 10_words | 10 | 10.400 | 0.647 | 34.674 | 30.499 | 38.311 |
| calibrated_pcas | 30_words | 10 | 11.600 | 0.743 | 37.242 | 32.647 | 40.531 |
| calibrated_pcas | 50_words | 10 | 10.000 | 0.632 | 36.786 | 34.119 | 39.402 |
