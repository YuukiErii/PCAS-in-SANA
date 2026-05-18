# Calibrated-PCAS Predictor Summary

The predictor is a small rule-based decision tree trained on prompt features and minimal sufficient step labels.

## Learned Rules

- if llm_relation_count <= 6.500 and llm_relation_count <= 3.500 and llm_object_count <= 7.500 and content_word_count <= 9.500 and llm_style_constraint_count <= 0.500 -> 8 steps (n=3, labels=8:3)
- if llm_relation_count <= 6.500 and llm_relation_count <= 3.500 and llm_object_count <= 7.500 and content_word_count <= 9.500 and llm_style_constraint_count > 0.500 -> 16 steps (n=5, labels=16:4, 8:1)
- if llm_relation_count <= 6.500 and llm_relation_count <= 3.500 and llm_object_count <= 7.500 and content_word_count > 9.500 -> 8 steps (n=5, labels=8:5)
- if llm_relation_count <= 6.500 and llm_relation_count <= 3.500 and llm_object_count > 7.500 -> 12 steps (n=1, labels=12:1)
- if llm_relation_count <= 6.500 and llm_relation_count > 3.500 and llm_object_count <= 7.500 and content_word_count <= 21.500 and llm_relation_count <= 4.500 -> 8 steps (n=1, labels=8:1)
- if llm_relation_count <= 6.500 and llm_relation_count > 3.500 and llm_object_count <= 7.500 and content_word_count <= 21.500 and llm_relation_count > 4.500 -> 12 steps (n=1, labels=12:1)
- if llm_relation_count <= 6.500 and llm_relation_count > 3.500 and llm_object_count <= 7.500 and content_word_count > 21.500 -> 12 steps (n=2, labels=12:2)
- if llm_relation_count <= 6.500 and llm_relation_count > 3.500 and llm_object_count > 7.500 and content_word_count <= 37.500 and content_word_count <= 35.500 -> 20 steps (n=3, labels=16:1, 20:2)
- if llm_relation_count <= 6.500 and llm_relation_count > 3.500 and llm_object_count > 7.500 and content_word_count <= 37.500 and content_word_count > 35.500 -> 16 steps (n=1, labels=16:1)
- if llm_relation_count <= 6.500 and llm_relation_count > 3.500 and llm_object_count > 7.500 and content_word_count > 37.500 -> 8 steps (n=1, labels=8:1)
- if llm_relation_count > 6.500 -> 8 steps (n=7, labels=8:7)

## Leave-One-Out Diagnostics

- Exact label accuracy: 43.3%
- Under-budget rate: 30.0%
- Over-budget rate: 26.7%
- Mean step error: -0.267

## Method Comparison

| Method | Prompts | Avg steps | Avg time no-warmup (s) | Speedup vs Fixed-20 | Avg CLIPScore | Avg CLIP delta | Constraint satisfaction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fixed_20 | 30 | 20.000 | 1.537 | 0.000% | 35.762 | 0.000 | 100.0% |
| balanced_pcas | 30 | 16.000 | 1.740 | -13.188% | 35.772 | 0.010 | 73.3% |
| deepseek_balanced_pcas | 30 | 18.467 | 2.023 | -31.642% | 35.813 | 0.051 | 73.3% |
| oracle_min_sufficient | 30 | 10.933 | 1.112 | 27.629% | 36.276 | 0.513 | 100.0% |
| calibrated_pcas | 30 | 10.667 | 0.675 | 56.099% | 36.234 | 0.472 | 96.7% |
| calibrated_pcas_llm_features | 30 | 11.333 | 1.093 | 28.854% | 36.230 | 0.467 | 96.7% |

## Constraint Misses

| Prompt | True steps | Predicted steps | CLIP delta | Tree path |
| --- | ---: | ---: | ---: | --- |
| blue sports car parked on empty road at bright noon | 8 | 16 | -0.429 | llm_relation_count <= 6.500 / llm_relation_count <= 3.500 / llm_object_count <= 7.500 / content_word_count <= 9.500 / llm_style_constraint_count > 0.500 / predict 16 steps |
