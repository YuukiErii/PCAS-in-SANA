# Day 5 Status

Date: 2026-05-17

## Completed

- Organized the headphone DreamBooth dataset:
  - Source photos: `ZZM Earphone/`
  - Prepared square images: `data/dreambooth/zzmearphone/`
  - Dataset manifest: `results/day5_lora_dataset_manifest.json`
- Verified and used the SANA DreamBooth LoRA training script:
  - `src/external/train_dreambooth_lora_sana.py`
- Completed lightweight LoRA training:
  - Output directory: `outputs/day5_lora_zzmearphone/`
  - Final weights: `outputs/day5_lora_zzmearphone/pytorch_lora_weights.safetensors`
  - Checkpoints: `checkpoint-100/` and `checkpoint-200/`
  - Training setting: rank 8, alpha 8, 200 steps, bf16, 512 resolution, CPU offload enabled
- Completed enhanced LoRA training:
  - Output directory: `outputs/day5_lora_zzmearphone_enhanced/`
  - Final weights: `outputs/day5_lora_zzmearphone_enhanced/pytorch_lora_weights.safetensors`
  - Checkpoints: `checkpoint-250/` and `checkpoint-500/`
  - Training setting: rank 16, alpha 16, 500 steps, bf16, 512 resolution, CPU offload enabled
  - Instance prompt: `a photo of zzmearphone black over-ear headphones with large oval ear cups and a padded headband`
- Completed clean-captioned LoRA training:
  - Training data: `data/dreambooth/zzmearphone_clean_captioned/`
  - Clean subset: 7 images, excluding the most ambiguous/partial views from the original 9-image set
  - Per-image captions: sidecar `.txt` files beside each training image
  - Output directory: `outputs/day5_lora_zzmearphone_clean_captioned_400/`
  - Final weights: `outputs/day5_lora_zzmearphone_clean_captioned_400/pytorch_lora_weights.safetensors`
  - Checkpoints: `checkpoint-200/` and `checkpoint-400/`
  - Training setting: rank 16, alpha 16, 400 steps, bf16, 512 resolution, CPU offload enabled
- Implemented and ran LoRA validation generation:
  - `src/run_sana_lora_validation.py`
  - `configs/day5_lora_validation.yaml`
  - `configs/day5_lora_validation_scale2.yaml`
  - Base outputs: `outputs/day5_lora_validation_base/`
  - LoRA scale 1.0 outputs: `outputs/day5_lora_validation_lora/`
  - LoRA scale 2.0 outputs: `outputs/day5_lora_validation_lora_scale2/`
- Implemented Day 5 evaluation and visualization:
  - `src/evaluate_day5_lora_subject_similarity.py`
  - `src/make_day5_lora_figures.py`
  - `results/day5_lora_validation_scale1_*.csv`
  - `results/day5_lora_validation_scale2_*.csv`
  - `results/figures/day5_lora_base_vs_lora_scale1_grid.png`
  - `results/figures/day5_lora_base_vs_lora_scale2_grid.png`
  - `results/figures/day5_lora_validation_scale1_metrics.png`
  - `results/figures/day5_lora_validation_scale2_metrics.png`
- Wrote the Day 5 summary:
  - `results/day5_lora_summary.md`
  - `report/day5_lora_evaluation_draft.md`
- Implemented and ran subject-focused consistency evaluation:
  - Prompts: `prompts/day5_lora_subject_consistency_prompts.txt`
  - Configs: `configs/day5_lora_subject_original_scale2.yaml`, `configs/day5_lora_subject_enhanced_scale1_5.yaml`, `configs/day5_lora_subject_enhanced_scale2.yaml`
  - Clean-caption configs: `configs/day5_lora_subject_clean_captioned_scale1_25.yaml`, `configs/day5_lora_subject_clean_captioned_scale1_5.yaml`, `configs/day5_lora_subject_clean_captioned_scale1_75.yaml`
  - Outputs: `outputs/day5_lora_subject_validation_*`
  - Evaluation script: `src/evaluate_day5_lora_subject_consistency.py`
  - Summary: `results/day5_lora_subject_consistency_summary.md`
  - Visual grid: `results/figures/day5_lora_subject_consistency_grid.png`

## Main Result

| Method | Images | Avg time no-warmup | Avg peak VRAM | Avg reference CLIP similarity | Avg prompt CLIPScore |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base SANA | 6 | 0.884s | 6.979GB | 80.680 | 32.681 |
| LoRA scale 1.0 | 6 | 1.218s | 6.985GB | 79.724 | 32.779 |
| LoRA scale 2.0 | 6 | 1.230s | 6.985GB | 78.423 | 32.472 |

## Interpretation

- LoRA training and loading succeeded.
- Scale 1.0 is visually subtle.
- Scale 2.0 produces a stronger subject-style shift toward black over-ear headphones in several prompts.
- The automatic reference CLIP similarity does not improve overall, so the LoRA result should be framed as a qualitative personalization reproduction with clear limitations.
- The strongest report use is a visual comparison plus a candid limitation discussion, not a claim of quantitative identity improvement.

## Subject-Focused Follow-Up

| Method | Images | Ref similarity | Ref delta vs Base | Ref wins | Subject CLIP | Subject delta vs Base | Subject wins | Prompt CLIPScore |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | 8 | 83.659 | 0.000 | 0/8 | 28.487 | 0.000 | 0/8 | 31.525 |
| Original LoRA x2 | 8 | 83.839 | 0.180 | 4/8 | 29.141 | 0.654 | 7/8 | 32.620 |
| Enhanced LoRA x1.5 | 8 | 81.560 | -2.099 | 2/8 | 30.053 | 1.566 | 6/8 | 34.040 |
| Enhanced LoRA x2 | 8 | 76.666 | -6.993 | 0/8 | 27.874 | -0.613 | 3/8 | 32.855 |
| Clean-caption x1.25 | 8 | 83.281 | -0.378 | 5/8 | 28.982 | 0.495 | 5/8 | 33.084 |
| Clean-caption x1.5 | 8 | 81.778 | -1.882 | 4/8 | 28.646 | 0.159 | 4/8 | 32.752 |
| Clean-caption x1.75 | 8 | 79.343 | -4.317 | 2/8 | 28.401 | -0.086 | 5/8 | 32.887 |

Follow-up interpretation:

- Subject-focused prompts remove the backpack-style occlusion issue and better isolate subject consistency.
- Original LoRA x2 has the best reference-centroid similarity, but the improvement over Base is small.
- Enhanced LoRA x1.5 is the best automatic subject-prompt setting and also gives the highest prompt CLIPScore.
- Enhanced LoRA x2 is too strong: it often darkens and simplifies the object, but can collapse the full headphone structure into ear cups or parts.
- Clean-caption x1.25 is the best conservative clean-data setting: it does not beat enhanced x1.5 on subject-prompt CLIP, but it keeps reference similarity close to Base and avoids the stronger scale collapse seen at higher scales.
- Final Day 5 conclusion should present LoRA as scale-sensitive and data-sensitive. Current results are enough for the report; new photos are optional for improving visual polish, not required to unblock the project.
