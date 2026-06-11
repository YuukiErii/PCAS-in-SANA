# Day 5 LoRA Subject Consistency Summary

This follow-up evaluates subject-focused prompts that keep the headphones centered and unobstructed. It compares the original 200-step LoRA, an enhanced 500-step rank-16 LoRA, and a clean-captioned 400-step rank-16 LoRA trained on a cleaner 7-image subset with per-image captions.

| Method | Images | Ref similarity | Ref delta vs Base | Ref wins | Subject CLIP | Subject delta vs Base | Subject wins | Prompt CLIPScore |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | 8 | 83.659 | 0.000 | 0/8 | 28.487 | 0.000 | 0/8 | 31.525 |
| Original LoRA x2 | 8 | 83.839 | 0.180 | 4/8 | 29.141 | 0.654 | 7/8 | 32.620 |
| Enhanced LoRA x1.5 | 8 | 81.560 | -2.099 | 2/8 | 30.053 | 1.566 | 6/8 | 34.040 |
| Enhanced LoRA x2 | 8 | 76.666 | -6.993 | 0/8 | 27.874 | -0.613 | 3/8 | 32.855 |
| Clean-caption x1.25 | 8 | 83.281 | -0.378 | 5/8 | 28.982 | 0.495 | 5/8 | 33.084 |
| Clean-caption x1.5 | 8 | 81.778 | -1.882 | 4/8 | 28.646 | 0.159 | 4/8 | 32.752 |
| Clean-caption x1.75 | 8 | 79.343 | -4.317 | 2/8 | 28.401 | -0.086 | 5/8 | 32.887 |

Key finding:

- Best automatic subject-consistency setting: `Enhanced LoRA x1.5`.
- Best clean-captioned compromise setting: `Clean-caption x1.25`.
- The enhanced and clean-captioned LoRA variants use more explicit prompts, rank 16, and longer training than the original 200-step run.
- The clean-captioned variant removes the most ambiguous training views and gives each remaining image a specific caption, so it tests whether better data/caption quality can reduce subject instability.
- Clean-caption x1.25 is more conservative than the enhanced x1.5 setting: it does not win the automatic subject-prompt metric, but it keeps reference similarity close to Base and avoids the stronger scale collapse seen at x1.75/x2.
- This is enough for the Day 5 conclusion; extra photos would mainly improve visual polish and product-identity robustness rather than unblock the current result.
- The validation prompts avoid occlusion-heavy scenes; this better measures whether the adapter can preserve the learned headphone identity.
- CLIP-based identity metrics remain proxies, so the qualitative grid should be used together with this table.

Files:

- Detailed metrics: `results\day5_lora_subject_consistency_results.csv`
- Visual grid: `results\figures\day5_lora_subject_consistency_grid.png`
