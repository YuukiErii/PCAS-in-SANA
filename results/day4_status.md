# Day 4 Status

Date: 2026-05-17

## Completed

- Implemented CLIPScore evaluation for Day 2 and Day 3 outputs:
  - `src/evaluate_clipscore.py`
  - `src/make_day4_figures.py`
- Evaluated 150 images across:
  - Fixed-10
  - Fixed-20
  - Fixed-28
  - Rule-PCAS 7.2
  - DeepSeek-PCAS 7.3
- Saved CLIPScore result tables:
  - `results/day4_clipscore_results.csv`
  - `results/day4_clipscore_summary.csv`
  - `results/day4_clipscore_summary.md`
- Saved high-resolution Day 4 comparison figures:
  - `results/figures/day4_speed_quality_tradeoff.png`
  - `results/figures/day4_clipscore_by_group.png`
- Ran guidance-scale ablation at 20 steps:
  - Guidance 1.5: `outputs/day4_guidance_1_5/`
  - Guidance 3.5: `outputs/day4_guidance_3_5/`
  - Guidance 4.5: reused `outputs/day2_baseline_20steps/`
  - Guidance 5.5: `outputs/day4_guidance_5_5/`
  - Guidance 6.5: `outputs/day4_guidance_6_5/`
  - Guidance 8.5: `outputs/day4_guidance_8_5/`
- Implemented guidance ablation analysis and visualization:
  - `src/evaluate_day4_guidance_ablation.py`
  - `src/make_day4_guidance_figures.py`
  - `src/make_day4_guidance_stress_assets.py`
- Saved guidance ablation result tables and figure:
  - `results/day4_guidance_ablation_results.csv`
  - `results/day4_guidance_ablation_summary.csv`
  - `results/day4_guidance_ablation_summary.md`
  - `results/day4_guidance_stress_analysis.csv`
  - `results/day4_guidance_stress_analysis.md`
  - `results/figures/day4_guidance_ablation_clipscore.png`
  - `results/figures/day4_guidance_stress_qualitative_grid.png`
- Added a hard-prompt qualitative evaluation supplement for cases where CLIPScore is not sensitive enough:
  - `src/make_day4_hard_eval_assets.py`
  - `src/make_day4_visual_difference_assets.py`
  - `results/day4_hard_prompt_clipscore_summary.csv`
  - `results/day4_hard_prompt_difference_vs_fixed20.csv`
  - `results/day4_hard_prompt_visual_tie_summary.md`
  - `results/figures/day4_hard_prompt_qualitative_grid.png`
  - `results/figures/day4_hard_prompt_difference_heatmap_vs_fixed20.png`
  - `report/day4_hard_prompt_evaluation_draft.md`

## CLIPScore Result

CLIPScore is CLIP image-text cosine similarity multiplied by 100. Higher is better.

| Method | Avg steps | Avg time no-warm-up | Avg CLIPScore |
| --- | ---: | ---: | ---: |
| Fixed-10 | 10.000 | 0.525s | 35.689 |
| Fixed-20 | 20.000 | 0.996s | 35.762 |
| Fixed-28 | 28.000 | 1.335s | 35.890 |
| Rule-PCAS 7.2 | 19.333 | 0.977s | 35.750 |
| DeepSeek-PCAS 7.3 | 23.400 | 1.303s | 35.829 |

## Guidance Ablation Result

All guidance ablation runs use 20 inference steps and the same 30 prompts. Guidance 1.5 and 8.5 are stress-test points added after the original 3.5-6.5 band looked too flat.

| Guidance | Avg time no-warm-up | Avg CLIPScore |
| ---: | ---: | ---: |
| 1.5 | 0.897s | 34.705 |
| 3.5 | 1.190s | 35.856 |
| 4.5 | 0.996s | 35.762 |
| 5.5 | 1.124s | 35.848 |
| 6.5 | 1.088s | 35.892 |
| 8.5 | 0.887s | 36.027 |

The normal 3.5-6.5 band has only 0.130 CLIPScore range on all prompts, which explains why the original ablation was not visually or numerically strong. Guidance 1.5 is 1.057 points below the default 4.5, while guidance 8.5 is 0.264 points above 4.5. This supports a robustness conclusion: moderate guidance values are similar, too-low guidance weakens prompt alignment, and high guidance can slightly improve automatic alignment without proving better visual quality.

## Hard Prompt Supplement

The hard subset uses 8 prompts that stress multi-object layout, relations, text rendering, and dense composition. It is intended for qualitative inspection and visual tie analysis, not forced manual scoring.

| Method | Images | Avg steps | Avg time no-warm-up | Avg CLIPScore |
| --- | ---: | ---: | ---: | ---: |
| Fixed-20 | 8 | 20.000 | 0.978s | 36.522 |
| Fixed-28 | 8 | 28.000 | 1.357s | 36.718 |
| Rule-PCAS 7.2 | 8 | 26.000 | 1.225s | 36.748 |
| Balanced-PCAS | 8 | 22.000 | 0.953s | 36.526 |
| DeepSeek-Balanced | 8 | 22.000 | 0.955s | 36.440 |

Because the generated images are visually very similar, the project does not use a forced human scoring table. The visual-difference supplement compares each candidate against Fixed-20 and marks where pixel-level changes occur; most visible changes are local texture, edge, and lighting changes rather than clear semantic improvements.

## Interpretation

- The CLIPScore differences across fixed-step baselines and PCAS variants are very small. The full-method range is only about 0.20 CLIPScore points, so Day 4 should not claim a statistically strong quality improvement.
- Rule-PCAS 7.2 keeps nearly the same CLIP-based text-image alignment as Fixed-20 while using slightly fewer average steps and less time overall.
- DeepSeek-PCAS 7.3 is more conservative: it allocates more prompts to high-step sampling, producing a slightly higher CLIPScore than Fixed-20 but also higher runtime.
- Fixed-28 has the highest CLIPScore among the fixed-step baselines, but the gain over Fixed-20 is small compared with the added runtime.
- Guidance scale between 3.5 and 6.5 does not show a strong monotonic CLIPScore trend because it is a stable normal band. The added 1.5 and 8.5 stress-test points make the conclusion clearer: avoid too-low guidance; high guidance slightly improves CLIPScore, especially for long prompts, but should not be claimed as a clear visual-quality gain.
- On the hard subset, CLIPScore still separates methods only weakly, so the stronger Day 4 interpretation is visual quality preservation, not manual-score superiority.
- Since many side-by-side images are nearly indistinguishable, visual similarity itself is evidence that lower-step PCAS preserves appearance.
- Report wording should be conservative: PCAS can be described as preserving CLIP-based alignment while changing compute allocation; it should not be presented as a proven quality-improving method based on CLIPScore alone.
