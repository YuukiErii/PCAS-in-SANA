# Day 4 CLIPScore Summary

CLIP model: `openai/clip-vit-base-patch32`.

The reported score is cosine similarity between CLIP image and text embeddings multiplied by 100. Higher is better.

| Method | Group | Images | Avg steps | Avg time no-warmup (s) | Avg CLIPScore | Min | Max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fixed_10 | all | 30 | 10.000 | 0.525 | 35.689 | 29.979 | 40.062 |
| fixed_10 | 10_words | 10 | 10.000 | 0.527 | 34.525 | 29.979 | 38.809 |
| fixed_10 | 30_words | 10 | 10.000 | 0.525 | 35.911 | 31.660 | 40.062 |
| fixed_10 | 50_words | 10 | 10.000 | 0.523 | 36.631 | 33.408 | 38.755 |
| fixed_20 | all | 30 | 20.000 | 0.996 | 35.762 | 29.935 | 39.473 |
| fixed_20 | 10_words | 10 | 20.000 | 1.019 | 34.336 | 29.935 | 38.123 |
| fixed_20 | 30_words | 10 | 20.000 | 0.972 | 36.614 | 31.917 | 39.297 |
| fixed_20 | 50_words | 10 | 20.000 | 1.001 | 36.336 | 31.894 | 39.473 |
| fixed_28 | all | 30 | 28.000 | 1.335 | 35.890 | 30.043 | 39.412 |
| fixed_28 | 10_words | 10 | 28.000 | 1.304 | 34.444 | 30.043 | 38.464 |
| fixed_28 | 30_words | 10 | 28.000 | 1.365 | 36.666 | 32.079 | 39.124 |
| fixed_28 | 50_words | 10 | 28.000 | 1.333 | 36.561 | 32.254 | 39.412 |
| rule_pcas_7_2 | all | 30 | 19.333 | 0.977 | 35.750 | 29.523 | 39.325 |
| rule_pcas_7_2 | 10_words | 10 | 10.000 | 0.593 | 34.154 | 29.523 | 37.433 |
| rule_pcas_7_2 | 30_words | 10 | 20.000 | 0.988 | 36.614 | 31.917 | 39.297 |
| rule_pcas_7_2 | 50_words | 10 | 28.000 | 1.312 | 36.481 | 31.268 | 39.325 |
| deepseek_pcas_7_3 | all | 30 | 23.400 | 1.303 | 35.829 | 29.523 | 39.325 |
| deepseek_pcas_7_3 | 10_words | 10 | 15.000 | 0.940 | 34.359 | 29.523 | 38.123 |
| deepseek_pcas_7_3 | 30_words | 10 | 27.200 | 1.420 | 36.646 | 31.933 | 39.318 |
| deepseek_pcas_7_3 | 50_words | 10 | 28.000 | 1.514 | 36.481 | 31.268 | 39.325 |
