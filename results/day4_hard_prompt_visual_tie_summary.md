# Day 4 Hard Prompt Visual Similarity Summary

This supplement addresses the problem that many generated images look nearly the same by measuring each candidate method against Fixed-20.

| Candidate | Pairs | Avg mean abs diff | Avg pixels changed >8 | Dominant bucket |
| --- | ---: | ---: | ---: | --- |
| Fixed-28 | 8 | 4.178 | 19.85% | noticeable_local_change |
| Rule-PCAS | 8 | 5.529 | 26.21% | clear_visual_change |
| Balanced-PCAS | 8 | 5.505 | 26.73% | noticeable_local_change |
| DeepSeek-Balanced | 8 | 5.605 | 26.01% | clear_visual_change |

Recommended interpretation:

- Do not force manual scores when the visual difference is largely imperceptible.
- Treat the hard-prompt side-by-side comparison as a qualitative sanity check.
- Public interpretation: Day 4 is evidence that PCAS preserves visual appearance under lower compute, not strong evidence of quality improvement.

Files:

- Difference metrics: `results\day4_hard_prompt_difference_vs_fixed20.csv`
- Difference heatmap: `results\figures\day4_hard_prompt_difference_heatmap_vs_fixed20.png`
