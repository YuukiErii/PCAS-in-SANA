# Results Summary

This repository reports automatic alignment and speed measurements for a controlled 30-prompt benchmark. Each prompt group contains 10 prompts: short, medium, and long.

## Main Efficiency Result

Balanced-PCAS is the main reportable efficiency result. It changes the manual Rule-PCAS policy from 10/20/28 steps to a budget-aware 8/16/24-step policy.

| Method | Avg steps | Avg time no-warmup | Speedup vs Fixed-20 | Avg CLIPScore |
| --- | ---: | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 0.0% | 35.762 |
| Rule-PCAS | 19.333 | 0.977s | 1.9% | 35.750 |
| Balanced-PCAS | 16.000 | 0.751s | 24.6% | 35.772 |
| DeepSeek-PCAS | 23.400 | 1.303s | -30.8% | 35.829 |
| DeepSeek-Balanced | 18.467 | 0.844s | 15.3% | 35.813 |

Interpretation:

- Prompt-aware allocation alone is not enough; it must also be budget-aware.
- Balanced-PCAS reduces average steps from 20 to 16 while keeping CLIPScore very close to Fixed-20.
- DeepSeek semantic labels are useful, but the action policy must be calibrated because raw high-difficulty labels can become too conservative.

## Quality and Guidance Analysis

The Day 4 CLIPScore evaluation found that Fixed-10, Fixed-20, Fixed-28, Rule-PCAS, and DeepSeek-PCAS are close in automatic alignment. Hard-prompt visual comparisons also show many near-ties.

The conservative conclusion is:

- PCAS should be framed as an efficiency-quality tradeoff strategy.
- The project does not claim a statistically proven image-quality improvement.
- Guidance scale is relatively flat in the normal 3.5 to 6.5 range; extreme low guidance is weak, while higher guidance is not treated as a robust visual-quality gain.

## Calibrated-PCAS Extension

Calibrated-PCAS builds a six-step calibration grid with steps 8, 12, 16, 20, 24, and 28. A prompt-level label is defined as the smallest step count whose CLIPScore is within 0.2 of Fixed-20.

Minimal sufficient step distribution:

| Steps | Prompts |
| ---: | ---: |
| 8 | 18 |
| 12 | 4 |
| 16 | 6 |
| 20 | 2 |

Final Day 6 comparison:

| Method | Avg steps | Avg time no-warmup | Speedup vs Fixed-20 | Avg CLIPScore | Constraint satisfaction |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 1.537s | 0.0% | 35.762 | 100.0% |
| Balanced-PCAS | 16.000 | 1.740s | -13.2% | 35.772 | 73.3% |
| DeepSeek-Balanced | 18.467 | 2.023s | -31.6% | 35.813 | 73.3% |
| Oracle minimum | 10.933 | 1.112s | 27.6% | 36.276 | 100.0% |
| Calibrated-PCAS | 10.667 | 0.675s | 56.1% | 36.234 | 96.7% |
| LLM-feature Calibrated-PCAS | 11.333 | 1.093s | 28.9% | 36.230 | 96.7% |

Caveats:

- The calibration set has only 30 prompts.
- CLIPScore is not monotonic in sampling steps and is not a complete visual-quality metric.
- Day 6 timing comes from a later rerun, so average steps and constraint satisfaction are more stable evidence than wall-clock latency alone.
- Calibrated-PCAS is best read as a proof of concept for data-calibrated adaptive inference.

## LoRA Extension

The LoRA experiment validates that SANA can be adapted with a small DreamBooth-style subject dataset. The image data and trained weights are not published in this repository. The result should be treated as an exploratory personalization supplement, not the main contribution.
