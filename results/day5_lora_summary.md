# Day 5 LoRA Personalization Summary

## Setup

- Subject: user's black over-ear headphones, named `zzmearphone`.
- Training images: 9 original photos in `ZZM Earphone/`.
- Prepared DreamBooth images: 9 square 768x768 images in `data/dreambooth/zzmearphone/`.
- Instance prompt: `a photo of zzmearphone headphones`.
- Base model: `Efficient-Large-Model/Sana_600M_512px_diffusers`.
- LoRA training: rank 8, alpha 8, 200 max steps, 512 resolution, bf16 mixed precision, CPU offload enabled.
- LoRA output: `outputs/day5_lora_zzmearphone/pytorch_lora_weights.safetensors`.

## Validation Runs

Six validation prompts were generated with the same seeds for the base model and LoRA model. The LoRA branch was tested at adapter scale 1.0 and 2.0.

| Method | Images | Avg time no-warmup | Avg peak VRAM | Avg reference CLIP similarity | Avg prompt CLIPScore |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base SANA | 6 | 0.884s | 6.979GB | 80.680 | 32.681 |
| LoRA scale 1.0 | 6 | 1.218s | 6.985GB | 79.724 | 32.779 |
| LoRA scale 2.0 | 6 | 1.230s | 6.985GB | 78.423 | 32.472 |

Reference CLIP similarity is computed between each generated image and the mean CLIP image embedding of the 9 prepared training photos. This is only a proxy for subject similarity and should not be treated as a definitive identity metric.

## Interpretation

- The LoRA adapter loads correctly and produces valid SANA images.
- At scale 1.0, the visual difference from the base model is small.
- At scale 2.0, several outputs shift toward darker black headphones and stronger over-ear product traits, especially the studio, macro, desk, and product-render prompts.
- The automatic reference-similarity score does not improve overall. One likely reason is that CLIP image embeddings are coarse for product identity; another is that the backpack prompt hides the headphone subject and strongly hurts the LoRA score.
- The Day 5 LoRA experiment should be presented as an optional personalization reproduction and qualitative case study, not as a strong quantitative improvement.

## Subject-Focused Follow-Up

To separate adapter strength from prompt occlusion, a second validation set uses 8 prompts that keep the headphones centered, unobstructed, and explicitly described as black over-ear headphones. This follow-up compares Base SANA, the original 200-step LoRA at scale 2.0, an enhanced LoRA trained with rank 16 / alpha 16 / 500 steps, and a clean-captioned LoRA trained for 400 steps on a cleaner 7-image subset with per-image captions.

| Method | Images | Ref similarity | Ref delta vs Base | Ref wins | Subject CLIP | Subject delta vs Base | Subject wins | Prompt CLIPScore |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | 8 | 83.659 | 0.000 | 0/8 | 28.487 | 0.000 | 0/8 | 31.525 |
| Original LoRA x2 | 8 | 83.839 | 0.180 | 4/8 | 29.141 | 0.654 | 7/8 | 32.620 |
| Enhanced LoRA x1.5 | 8 | 81.560 | -2.099 | 2/8 | 30.053 | 1.566 | 6/8 | 34.040 |
| Enhanced LoRA x2 | 8 | 76.666 | -6.993 | 0/8 | 27.874 | -0.613 | 3/8 | 32.855 |
| Clean-caption x1.25 | 8 | 83.281 | -0.378 | 5/8 | 28.982 | 0.495 | 5/8 | 33.084 |
| Clean-caption x1.5 | 8 | 81.778 | -1.882 | 4/8 | 28.646 | 0.159 | 4/8 | 32.752 |
| Clean-caption x1.75 | 8 | 79.343 | -4.317 | 2/8 | 28.401 | -0.086 | 5/8 | 32.887 |

The enhanced LoRA at scale 1.5 is the best working point on subject-prompt CLIP and prompt CLIPScore, but its reference-centroid similarity is lower than Base and some images still need qualitative checking. The clean-captioned LoRA at scale 1.25 is a more conservative compromise: it keeps reference similarity close to Base, wins 5/8 prompts on reference similarity, and visually avoids the stronger scale collapse seen at clean-caption x1.75 and enhanced x2. This means new photos are not required to finish the course-report conclusion, although additional clean product photos would still help if the goal is a stronger personalization demo.

## Figure References

- Scale 1.0 visual grid: `results/figures/day5_lora_base_vs_lora_scale1_grid.png`
- Scale 2.0 visual grid: `results/figures/day5_lora_base_vs_lora_scale2_grid.png`
- Scale 1.0 metric chart: `results/figures/day5_lora_validation_scale1_metrics.png`
- Scale 2.0 metric chart: `results/figures/day5_lora_validation_scale2_metrics.png`
- Subject-focused consistency grid: `results/figures/day5_lora_subject_consistency_grid.png`
- Subject-focused consistency summary: `results/day5_lora_subject_consistency_summary.md`
