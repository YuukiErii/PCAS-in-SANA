# Day 3 Status

Date: 2026-05-17

## Completed

- Implemented rule-based Prompt-Complexity Adaptive Sampling:
  - `src/prompt_complexity.py`
  - `src/run_sana_pcas.py`
  - `configs/day3_pcas.yaml`
- Exported prompt complexity analysis:
  - `results/day3_prompt_complexity.csv`
- Ran PCAS on the same 30-prompt benchmark from Day 2:
  - Output directory: `outputs/day3_pcas/`
  - Generated images: 30
  - Summary: `outputs/day3_pcas/summary.json`
- Implemented Day 3 result aggregation and visualization:
  - `src/summarize_day3_results.py`
  - `src/make_day3_figures.py`
- Exported PCAS result tables:
  - `results/day3_pcas_results.csv`
  - `results/day3_pcas_summary.csv`
  - `results/day3_pcas_summary.md`
  - `results/day3_pcas_vs_fixed20.csv`
- Exported high-resolution figures:
  - `results/figures/day3_pcas_vs_fixed20_chart.png`
  - `results/figures/day3_pcas_vs_fixed20_full_prompts.png`
- Implemented Section 7.3 DeepSeek-assisted semantic prompt analysis:
  - `src/prompt_complexity_deepseek.py`
  - `src/run_sana_pcas_deepseek.py`
  - `configs/day3_pcas_deepseek.yaml`
- Added `API_DEEPSEEK.txt` to `.gitignore`; the API key is read locally and is not written to result files.
- Exported DeepSeek complexity results and cache:
  - `results/day3_deepseek_prompt_complexity.csv`
  - `results/day3_deepseek_complexity_cache.json`
- Ran DeepSeek-PCAS on the same 30-prompt benchmark:
  - Output directory: `outputs/day3_pcas_deepseek/`
  - Generated images: 30
  - Summary: `outputs/day3_pcas_deepseek/summary.json`
- Exported 7.2 vs 7.3 comparison tables and figures:
  - `results/day3_deepseek_pcas_summary.md`
  - `results/day3_7_2_7_3_summary.csv`
  - `results/day3_7_2_7_3_vs_fixed20.csv`
  - `results/figures/day3_7_2_vs_7_3_time_steps_chart.png`
  - `results/figures/day3_7_2_vs_7_3_full_prompts.png`

## PCAS Policy

| Prompt group | Word count | Label | Steps | Guidance scale | Resolution |
| --- | ---: | --- | ---: | ---: | --- |
| 10-word prompts | 10 | short | 10 | 4.0 | 512x512 |
| 30-word prompts | 30 | medium | 20 | 4.5 | 512x512 |
| 50-word prompts | 50 | long | 28 | 5.0 | 512x512 |

## Main Result

| Method | Avg steps | Avg time no-warm-up | Avg peak VRAM |
| --- | ---: | ---: | ---: |
| Fixed-10 | 10.000 | 0.525s | 6.979GB |
| Fixed-20 | 20.000 | 0.996s | 6.979GB |
| Fixed-28 | 28.000 | 1.335s | 6.979GB |
| PCAS | 19.333 | 0.977s | 6.979GB |

## PCAS vs Fixed-20

| Prompt group | PCAS steps | Fixed-20 steps | Step saving | PCAS time | Fixed-20 time | Time saving |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| All | 19.333 | 20.000 | 3.3% | 0.977s | 0.996s | 1.9% |
| 10 words | 10.000 | 20.000 | 50.0% | 0.593s | 1.019s | 41.8% |
| 30 words | 20.000 | 20.000 | 0.0% | 0.988s | 0.972s | -1.7% |
| 50 words | 28.000 | 20.000 | -40.0% | 1.312s | 1.001s | -31.2% |

## Interpretation

- PCAS clearly reduces compute for short prompts: 10-word prompts use half the steps of Fixed-20 and are about 41.8% faster.
- PCAS keeps medium prompts aligned with the Fixed-20 baseline.
- PCAS intentionally spends extra compute on long prompts, using 28 steps instead of 20, so long prompts are slower but receive a higher sampling budget.
- On the balanced 10/30/50 benchmark, the overall runtime is close to Fixed-20 while the compute allocation is more prompt-aware.
- This is a first inference-policy result. Day 4 should evaluate whether the additional long-prompt compute improves text-image alignment or visual quality.

## Section 7.3 DeepSeek-PCAS Result

DeepSeek classified the 30 prompts as:

| DeepSeek label | Count |
| --- | ---: |
| low | 5 |
| medium | 6 |
| high | 19 |

Compared with the 7.2 length-based policy, DeepSeek-PCAS is more conservative:

| Method | Avg steps | Avg time no-warm-up | Avg peak VRAM |
| --- | ---: | ---: | ---: |
| Rule-PCAS 7.2 | 19.333 | 0.977s | 6.979GB |
| DeepSeek-PCAS 7.3 | 23.400 | 1.303s | 6.979GB |

DeepSeek-PCAS assigns higher steps to many prompts because it considers semantic object counts, relations, style constraints, and text-rendering requirements rather than word count alone. This makes it slower than Fixed-20 overall, but it is better aligned with the 7.3 goal: semantic prompt-complexity estimation.

## Balanced-PCAS Follow-up

To address the small overall speed gain of the original Rule-PCAS, an efficiency-oriented Balanced-PCAS variant was added.

| Prompt group | Balanced-PCAS steps | Balanced-PCAS guidance |
| --- | ---: | ---: |
| 10 words | 8 | 4.0 |
| 30 words | 16 | 4.4 |
| 50 words | 24 | 4.8 |

| Method | Avg steps | Avg time no-warmup | Avg CLIPScore |
| --- | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 35.762 |
| Rule-PCAS 7.2 | 19.333 | 0.977s | 35.750 |
| Balanced-PCAS | 16.000 | 0.751s | 35.772 |

Balanced-PCAS improves the overall no-warmup time saving vs Fixed-20 from 1.9% to 24.6%, while keeping CLIPScore essentially unchanged on this benchmark. It should be framed as the efficiency-first PCAS variant, while the original Rule-PCAS remains useful for explaining compute reallocation by prompt complexity.

Files:

- Config: `configs/day3_pcas_balanced.yaml`
- Outputs: `outputs/day3_pcas_balanced/`
- Speed summary: `results/day3_pcas_balanced_summary.md`
- CLIPScore summary: `results/day3_pcas_balanced_clipscore_summary.md`
- Figures: `results/figures/day3_pcas_balanced_speed_chart.png`, `results/figures/day3_pcas_balanced_speed_quality_tradeoff.png`

## DeepSeek-Balanced Follow-up

To address the original DeepSeek-PCAS being too conservative and slower than Fixed-20, a budget-constrained DeepSeek-Balanced variant was added. It reuses the same cached DeepSeek labels:

| DeepSeek label | Count | Original steps | Balanced steps |
| --- | ---: | ---: | ---: |
| low | 5 | 10 | 8 |
| medium | 6 | 20 | 16 |
| high | 19 | 28 | 22 |

| Method | Avg steps | Avg time no-warmup | Avg CLIPScore |
| --- | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 35.762 |
| DeepSeek-PCAS 7.3 | 23.400 | 1.303s | 35.829 |
| DeepSeek-Balanced | 18.467 | 0.844s | 35.813 |
| Balanced-PCAS | 16.000 | 0.751s | 35.772 |

DeepSeek-Balanced fixes the speed problem: the original DeepSeek-PCAS is 30.8% slower than Fixed-20, while DeepSeek-Balanced is 15.3% faster than Fixed-20. Its CLIPScore remains close to the original DeepSeek-PCAS. This version should be described as a budget-constrained semantic scheduler.

Files:

- Config: `configs/day3_pcas_deepseek_balanced.yaml`
- Outputs: `outputs/day3_pcas_deepseek_balanced/`
- Speed summary: `results/day3_deepseek_balanced_summary.md`
- CLIPScore summary: `results/day3_pcas_all_balanced_clipscore_summary.md`
- Figures: `results/figures/day3_deepseek_balanced_speed_chart.png`, `results/figures/day3_deepseek_balanced_speed_quality_tradeoff.png`
