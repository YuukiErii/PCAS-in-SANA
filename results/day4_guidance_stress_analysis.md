# Day 4 Guidance Stress-Test Analysis

The original guidance ablation only covered 3.5-6.5, where CLIPScore changes were small. This expanded analysis adds guidance 1.5 and 8.5 to separate normal-band robustness from low/high stress behavior.

| Group | CLIP@4.5 | 1.5 delta | 8.5 delta | Normal-band range | Full range | Best guidance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 35.762 | -1.057 | 0.264 | 0.130 | 1.322 | 8.5 |
| 10_words | 34.336 | -1.117 | 0.350 | 0.482 | 1.468 | 6.5 |
| 30_words | 36.614 | -0.636 | -0.176 | 0.187 | 0.714 | 3.5 |
| 50_words | 36.336 | -1.419 | 0.619 | 0.345 | 2.038 | 8.5 |

Key finding:

- On all prompts, guidance 1.5 is -1.057 CLIPScore points below guidance 4.5, so too-low guidance weakens prompt-image alignment.
- The normal 3.5-6.5 band has only 0.130 CLIPScore range on all prompts, so the original ablation was expected to look flat.
- Guidance 8.5 is 0.264 above guidance 4.5 on all prompts, but the gain is small enough that it should be reported as a high-guidance CLIPScore preference, not a proven visual-quality improvement.
- Recommended report wording: SANA-0.6B is robust to moderate guidance changes; avoid very low guidance; keep 4.5 as the default for fair comparison, or use 6.5-8.5 only as an optional higher-alignment setting with qualitative inspection.

Files:

- Stress-test table: `results\day4_guidance_stress_analysis.csv`
- Qualitative grid: `results\figures\day4_guidance_stress_qualitative_grid.png`
