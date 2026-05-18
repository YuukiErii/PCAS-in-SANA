# Calibrated PCAS Calibration Dataset

Reference policy: Fixed-20.
Quality constraint: `CLIPScore(s) >= CLIPScore(Fixed-20) - 0.2`.

## Minimal Sufficient Steps Distribution

| Steps | Prompts |
| ---: | ---: |
| 8 | 18 |
| 12 | 4 |
| 16 | 6 |
| 20 | 2 |

## Oracle Policy Summary

| Method | Prompts | Avg steps | Avg time no-warmup (s) | Speedup vs Fixed-20 | Avg CLIPScore | Avg CLIP delta | Constraint satisfaction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fixed_20 | 30 | 20.000 | 1.854 | 0.000% | 35.762 | 0.000 | 100.000% |
| oracle_min_sufficient | 30 | 10.933 | 1.112 | 40.015% | 36.276 | 0.513 | 100.000% |

## Notes

- The oracle policy is not a deployable predictor; it is the upper-bound scheduler that directly reads the calibration grid label for each prompt.
- The next step is to train a lightweight predictor from prompt features to the minimal sufficient steps label.
