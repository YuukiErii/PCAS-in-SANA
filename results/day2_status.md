# Day 2 Status

Date: 2026-05-17

## Completed

- Removed the previous Day 2 prompt/config/output/result files and rebuilt the benchmark.
- Built a controlled 30-prompt benchmark with explicit prompt lengths:
  - `prompts/day2_10word_prompts.txt`: 10 prompts, exactly 10 words each.
  - `prompts/day2_30word_prompts.txt`: 10 prompts, exactly 30 words each.
  - `prompts/day2_50word_prompts.txt`: 10 prompts, exactly 50 words each.
  - `prompts/day2_benchmark_prompts.txt`: combined 30-prompt file.
- Recreated fixed-step baseline configs for 10, 20, and 28 denoising steps:
  - `configs/day2_baseline_10steps.yaml`
  - `configs/day2_baseline_20steps.yaml`
  - `configs/day2_baseline_28steps.yaml`
- Ran all fixed-step baselines with `Efficient-Large-Model/Sana_600M_512px_diffusers` at 512x512.
- Generated 90 baseline images:
  - `outputs/day2_baseline_10steps/`
  - `outputs/day2_baseline_20steps/`
  - `outputs/day2_baseline_28steps/`
- Rebuilt the summary scripts:
  - `src/summarize_day2_results.py`
  - `src/make_day2_summary_figures.py`
- Exported speed tables:
  - `results/day2_speed_results.csv`
  - `results/day2_speed_summary.csv`
  - `results/day2_speed_summary.md`
- Exported high-resolution summary figures with full prompts:
  - `results/figures/day2_baseline_grid_full_prompts.png`
  - `results/figures/day2_baseline_grid_10_words_full_prompts.png`
  - `results/figures/day2_baseline_grid_30_words_full_prompts.png`
  - `results/figures/day2_baseline_grid_50_words_full_prompts.png`
  - `results/figures/day2_speed_summary_chart.png`

## Fixed-Step Speed Summary

Model: `Efficient-Large-Model/Sana_600M_512px_diffusers`

Resolution: 512x512

Guidance scale: 4.5

| Method | Avg time, all prompts | Avg time, no warm-up | Max time | Avg peak VRAM |
| --- | ---: | ---: | ---: | ---: |
| Fixed-10 | 0.580s | 0.525s | 2.167s | 6.979GB |
| Fixed-20 | 1.057s | 0.996s | 2.820s | 6.979GB |
| Fixed-28 | 1.389s | 1.335s | 2.950s | 6.979GB |

## Prompt-Length Group Summary

| Method | 10 words | 30 words | 50 words |
| --- | ---: | ---: | ---: |
| Fixed-10 no-warm-up | 0.527s | 0.525s | 0.523s |
| Fixed-20 no-warm-up | 1.019s | 0.972s | 1.001s |
| Fixed-28 no-warm-up | 1.304s | 1.365s | 1.333s |

## Notes

- Prompt length is now controlled exactly, which makes the benchmark cleaner for PCAS and reporting.
- The high-resolution grid figures show every prompt in full, with no ellipsis or truncation.
- Peak VRAM is still identical across fixed-step runs because the model and 512x512 activation footprint dominate memory, while step count mostly changes runtime.
- The next step is to implement rule-based PCAS using the same 10/30/50-word benchmark.
