# Calibrated-PCAS Predictor Summary

The predictor is a small rule-based decision tree trained on prompt features and minimal sufficient step labels.

## Learned Rules

- if relation_count <= 3.500 and attribute_count <= 3.500 and content_word_count <= 9.500 and scene_density_score <= 0.292 and content_word_count <= 8.500 -> 8 steps (n=3, labels=8:3)
- if relation_count <= 3.500 and attribute_count <= 3.500 and content_word_count <= 9.500 and scene_density_score <= 0.292 and content_word_count > 8.500 -> 8 steps (n=2, labels=16:1, 8:1)
- if relation_count <= 3.500 and attribute_count <= 3.500 and content_word_count <= 9.500 and scene_density_score > 0.292 -> 16 steps (n=3, labels=16:3)
- if relation_count <= 3.500 and attribute_count <= 3.500 and content_word_count > 9.500 -> 8 steps (n=3, labels=8:3)
- if relation_count <= 3.500 and attribute_count > 3.500 and rare_concept_score <= 0.062 and word_count <= 40.000 and relation_count <= 1.500 -> 16 steps (n=1, labels=16:1)
- if relation_count <= 3.500 and attribute_count > 3.500 and rare_concept_score <= 0.062 and word_count <= 40.000 and relation_count > 1.500 -> 12 steps (n=4, labels=12:4)
- if relation_count <= 3.500 and attribute_count > 3.500 and rare_concept_score <= 0.062 and word_count > 40.000 -> 20 steps (n=1, labels=20:1)
- if relation_count <= 3.500 and attribute_count > 3.500 and rare_concept_score > 0.062 and content_word_count <= 22.500 -> 8 steps (n=2, labels=8:2)
- if relation_count <= 3.500 and attribute_count > 3.500 and rare_concept_score > 0.062 and content_word_count > 22.500 -> 20 steps (n=1, labels=20:1)
- if relation_count > 3.500 and comma_count <= 6.500 -> 8 steps (n=9, labels=8:9)
- if relation_count > 3.500 and comma_count > 6.500 -> 16 steps (n=1, labels=16:1)

## Leave-One-Out Diagnostics

- Exact label accuracy: 40.0%
- Under-budget rate: 30.0%
- Over-budget rate: 30.0%
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
| red sneakers placed on concrete floor beside gym lockers neatly | 16 | 8 | -1.421 | relation_count <= 3.500 / attribute_count <= 3.500 / content_word_count <= 9.500 / scene_density_score <= 0.292 / content_word_count > 8.500 / predict 8 steps |
