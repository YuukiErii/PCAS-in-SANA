# SANA PCAS Course Project

Project topic: Reproduction and Prompt-Complexity Adaptive Sampling for Efficient Text-to-Image Generation with SANA.

This repository follows the one-week plan in `SANA课程项目详细大纲.docx`. Day 1 focuses on environment setup, one working SANA inference run, the first baseline images, and a short reproducibility record.

## Day 1 Goal

- Create a clean Python environment.
- Install PyTorch CUDA, Diffusers, Transformers, Accelerate, and utility packages.
- Verify RTX 5080 / CUDA availability.
- Run a small SANA inference smoke test.
- Save generated images and metadata under `outputs/day1_baseline/`.
- Save the environment report under `results/day1_environment.md`.

## Environment Setup

Use Python 3.11 on this machine:

```powershell
& "C:\Users\Mahiru\AppData\Local\Programs\Python\Python311\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-torch-cu128.txt
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the CUDA wheel changes in the future, use the command shown on the official PyTorch install page and keep this README updated.

## Day 1 Commands

Check the environment:

```powershell
.\.venv\Scripts\python.exe .\src\day1_env_check.py --output .\results\day1_environment.md
```

Run the SANA smoke baseline:

```powershell
.\.venv\Scripts\python.exe .\src\run_sana_baseline.py --config .\configs\day1_smoke.yaml
```

If the official SANA model download is slow, resume the largest missing shard with the Hugging Face mirror:

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
.\.venv\Scripts\hf.exe download Efficient-Large-Model/Sana_600M_512px_diffusers text_encoder/model.fp16-00001-of-00002.safetensors
```

For a fast pipeline-only debug check, use the tiny random SANA model:

```powershell
.\.venv\Scripts\python.exe .\src\run_sana_baseline.py --config .\configs\day1_tiny_debug.yaml
```

For the first real 1024px baseline, after the smoke test succeeds:

```powershell
.\.venv\Scripts\python.exe .\src\run_sana_baseline.py --config .\configs\sana_baseline.yaml
```

## Project Layout

```text
configs/      Inference configuration files.
prompts/      Prompt benchmark files.
src/          Reproduction and experiment scripts.
outputs/      Generated images and per-image metadata.
results/      CSV/Markdown results and figures.
report/       Written report and final slides.
```

## Current Day 1 Notes

- GPU detected: NVIDIA GeForce RTX 5080 Laptop GPU, 16GB VRAM.
- System `python` alias points to Microsoft Store, so use the explicit Python 3.11 path or `.venv\Scripts\python.exe`.
- `git` is not currently on PATH.
- The recommended first target is the 0.6B / 512px diffusers checkpoint to prove the pipeline before spending time on 1024px experiments.

## Day 2 Preview

Build a 30-prompt benchmark split into 10-word, 30-word, and 50-word prompts. Then run fixed-step baselines for 10, 20, and 28 steps and collect speed numbers.

## Current Day 2 Notes

- Built a controlled 30-prompt benchmark under `prompts/`: 10 prompts each with exactly 10, 30, and 50 words.
- Ran 512px fixed-step baselines for 10, 20, and 28 steps with the cached SANA-0.6B checkpoint.
- Saved generated images under `outputs/day2_baseline_*steps/`.
- Saved speed tables under `results/day2_speed_results.csv` and `results/day2_speed_summary.md`.
- Saved high-resolution visual comparison grids with full prompts under `results/figures/day2_baseline_grid_*full_prompts.png`.

## Current Day 3 Notes

- Implemented rule-based Prompt-Complexity Adaptive Sampling in `src/prompt_complexity.py` and `src/run_sana_pcas.py`.
- PCAS maps 10-word prompts to 10 steps / guidance 4.0, 30-word prompts to 20 steps / guidance 4.5, and 50-word prompts to 28 steps / guidance 5.0.
- Ran PCAS on the Day 2 benchmark and saved outputs under `outputs/day3_pcas/`.
- Saved PCAS comparison tables under `results/day3_pcas_summary.md` and `results/day3_pcas_vs_fixed20.csv`.
- Saved high-resolution PCAS comparison figures under `results/figures/day3_pcas_vs_fixed20_*.png`.
- Implemented Section 7.3 DeepSeek-assisted PCAS in `src/prompt_complexity_deepseek.py` and `src/run_sana_pcas_deepseek.py`.
- DeepSeek API access reads from `DEEPSEEK_API_KEY` or local `API_DEEPSEEK.txt`; the local key file is ignored by `.gitignore`.
- Ran DeepSeek-PCAS and saved outputs under `outputs/day3_pcas_deepseek/`.
- Saved 7.2 vs 7.3 comparison tables under `results/day3_deepseek_pcas_summary.md` and `results/day3_7_2_7_3_summary.csv`.
- Saved 7.2 vs 7.3 comparison figures under `results/figures/day3_7_2_vs_7_3_*.png`.
- Added an efficiency-oriented Balanced-PCAS follow-up with 8/16/24 steps for 10/30/50-word prompts.
- Balanced-PCAS saved outputs under `outputs/day3_pcas_balanced/`.
- Balanced-PCAS improves overall no-warmup speed vs Fixed-20 from the original Rule-PCAS 1.9% saving to 24.6% saving, while keeping CLIPScore very close to Fixed-20.
- Saved Balanced-PCAS tables under `results/day3_pcas_balanced_*.csv` and figures under `results/figures/day3_pcas_balanced_*.png`.
- Added DeepSeek-Balanced PCAS to fix the original DeepSeek-PCAS being too conservative.
- DeepSeek-Balanced reuses the cached DeepSeek semantic labels but applies an 8/16/22-step policy for low/medium/high prompts.
- DeepSeek-Balanced changes DeepSeek-PCAS from 30.8% slower than Fixed-20 to 15.3% faster than Fixed-20, while keeping CLIPScore close to the original DeepSeek-PCAS.
- Saved DeepSeek-Balanced tables under `results/day3_deepseek_balanced_*.csv` and figures under `results/figures/day3_deepseek_balanced_*.png`.

## Current Day 4 Notes

- Implemented CLIPScore evaluation in `src/evaluate_clipscore.py` and visual summaries in `src/make_day4_figures.py`.
- Evaluated Fixed-10, Fixed-20, Fixed-28, Rule-PCAS 7.2, and DeepSeek-PCAS 7.3 with `openai/clip-vit-base-patch32`.
- Saved Day 4 quality tables under `results/day4_clipscore_*.csv` and `results/day4_clipscore_summary.md`.
- Saved high-resolution speed-quality figures under `results/figures/day4_speed_quality_tradeoff.png` and `results/figures/day4_clipscore_by_group.png`.
- Ran a 20-step guidance-scale ablation for guidance 1.5, 3.5, 4.5, 5.5, 6.5, and 8.5. Guidance 1.5 and 8.5 are added stress-test points beyond the original normal band.
- Saved guidance ablation tables under `results/day4_guidance_ablation_*.csv` and `results/day4_guidance_ablation_summary.md`.
- Saved the high-resolution guidance chart under `results/figures/day4_guidance_ablation_clipscore.png`.
- Saved guidance stress-test analysis under `results/day4_guidance_stress_analysis.md` and a qualitative grid under `results/figures/day4_guidance_stress_qualitative_grid.png`.
- Added a hard-prompt qualitative supplement for the "CLIPScore improvement is not obvious" issue.
- Generated a hard-prompt comparison grid under `results/figures/day4_hard_prompt_qualitative_grid.png`.
- Added a visual-difference supplement because many side-by-side images are hard to distinguish by eye.
- Saved difference metrics under `results/day4_hard_prompt_difference_vs_fixed20.csv`.
- Saved the difference heatmap under `results/figures/day4_hard_prompt_difference_heatmap_vs_fixed20.png`.
- Saved the hard-prompt report draft under `report/day4_hard_prompt_evaluation_draft.md`.
- Main Day 4 finding: all methods are very close in CLIPScore and many side-by-side outputs are visually hard to distinguish. PCAS should be framed as preserving CLIP-based alignment and visual quality while reallocating compute, rather than as a clearly proven quality-improving method. Guidance scale is also mostly flat in the 3.5-6.5 normal band; 1.5 is too weak, while 8.5 slightly improves CLIPScore but is not treated as a proven visual-quality gain.

## Current Day 5 Notes

- Prepared a 9-image DreamBooth dataset from the user's headphone photos under `data/dreambooth/zzmearphone/`.
- Ran lightweight SANA DreamBooth LoRA training with rank 8, alpha 8, 200 steps, bf16, and CPU offload.
- Saved LoRA weights under `outputs/day5_lora_zzmearphone/pytorch_lora_weights.safetensors`.
- Implemented base-vs-LoRA validation generation in `src/run_sana_lora_validation.py`.
- Generated validation images for Base SANA, LoRA scale 1.0, and LoRA scale 2.0.
- Evaluated generated images with CLIP image similarity against the training-photo reference centroid in `src/evaluate_day5_lora_subject_similarity.py`.
- Saved Day 5 tables under `results/day5_lora_validation_scale*_*.csv` and a summary under `results/day5_lora_summary.md`.
- Saved Day 5 figures under `results/figures/day5_lora_base_vs_lora_scale*_grid.png` and `results/figures/day5_lora_validation_scale*_metrics.png`.
- Added an enhanced subject-consistency follow-up: rank 16, alpha 16, 500 steps, and a more explicit instance prompt (`a photo of zzmearphone black over-ear headphones with large oval ear cups and a padded headband`).
- Added a clean-captioned LoRA follow-up: 7 cleaner training images, per-image sidecar captions, rank 16, alpha 16, 400 steps.
- Added subject-focused validation prompts that keep the headphones centered and unobstructed, then compared Base, original LoRA x2, enhanced LoRA x1.5/x2, and clean-captioned LoRA x1.25/x1.5/x1.75.
- Saved subject-consistency tables under `results/day5_lora_subject_consistency_*.csv`, summary under `results/day5_lora_subject_consistency_summary.md`, and visual grid under `results/figures/day5_lora_subject_consistency_grid.png`.
- Main Day 5 finding: LoRA training and loading succeeded; original LoRA x2 is closest to the training-photo reference centroid, enhanced LoRA x1.5 gives the best subject-prompt CLIPScore and prompt CLIPScore, and clean-caption x1.25 is the most conservative clean-data compromise. Stronger scales can distort the headphone structure. Present Day 5 as an exploratory personalization reproduction with clear limits; new photos are optional for better visual polish, not required for the current report.

## Current Day 6 Notes

- Added a Calibrated-PCAS extension based on `report/CALIBRATED_PCAS_OUTLINE.md`.
- Generated a six-step calibration grid for the 30 benchmark prompts: 8, 12, 16, 20, 24, and 28 steps.
- Built minimal sufficient step labels relative to Fixed-20 with `epsilon=0.2` CLIPScore tolerance.
- Implemented rule prompt features in `src/prompt_features.py` and DeepSeek JSON prompt features in `src/prompt_features_deepseek.py`.
- Implemented pure-Python decision tree training in `src/train_calibrated_pcas_predictor.py`.
- Implemented calibrated SANA inference in `src/run_sana_calibrated_pcas.py`.
- Added `--no-default-methods` to `src/evaluate_clipscore.py` so one CLIPScore run can evaluate only the requested Day6 comparison methods.
- Saved Day6 tables under `results/day6_*` and the report draft under `report/day6_calibrated_pcas_draft.md`.
- Main Day 6 finding: the minimal sufficient steps distribution is 8 steps for 18 prompts, 12 steps for 4 prompts, 16 steps for 6 prompts, and 20 steps for 2 prompts. Rule-feature and LLM-feature Calibrated-PCAS both reach 96.7% Fixed-20 constraint satisfaction on the current calibration set, with average steps of 10.667 and 11.333 respectively.
- Treat Calibrated-PCAS as an additional research extension. The strongest main-report baseline remains Balanced-PCAS because the Day6 calibration set is small and wall-clock latency varies between reruns.
