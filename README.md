# PCAS in SANA

Reproduction and prompt-complexity adaptive sampling for efficient text-to-image generation with SANA.

This repository studies a simple question: after SANA reduces the per-step cost of high-resolution text-to-image generation, should every prompt still receive the same inference budget? We reproduce SANA inference with Hugging Face Diffusers, build a controlled prompt benchmark, and evaluate several Prompt-Complexity Adaptive Sampling (PCAS) policies that allocate denoising steps according to prompt difficulty.

## Highlights

- Reproduces SANA-0.6B inference with Diffusers on a 30-prompt benchmark.
- Implements fixed-step baselines, rule-based PCAS, DeepSeek-assisted PCAS, budget-aware Balanced-PCAS, and a data-calibrated PCAS extension.
- Evaluates speed, step budget, CLIPScore alignment, guidance-scale sensitivity, and hard-prompt qualitative behavior.
- Includes an exploratory SANA DreamBooth LoRA personalization pipeline; private images and LoRA weights are intentionally excluded from Git.
- Keeps generated images, model weights, logs, API keys, and presentation binaries out of the repository.

## Method Overview

PCAS treats sampling steps and guidance scale as inference-time resources. Instead of assigning a fixed 20-step or 28-step policy to every prompt, a prompt analyzer estimates difficulty and selects a smaller or larger budget.

The repository contains four main policy families:

| Policy | Idea | Main files |
| --- | --- | --- |
| Fixed-step baselines | Use 10, 20, or 28 steps for all prompts | `configs/day2_baseline_*.yaml`, `src/run_sana_baseline.py` |
| Rule-PCAS | Map short, medium, and long prompts to different budgets | `src/prompt_complexity.py`, `src/run_sana_pcas.py` |
| DeepSeek-PCAS | Use an LLM to assign semantic difficulty labels | `src/prompt_complexity_deepseek.py`, `src/run_sana_pcas_deepseek.py` |
| Calibrated-PCAS | Learn a lightweight predictor for minimal sufficient steps under a Fixed-20 CLIPScore constraint | `src/build_calibration_dataset.py`, `src/train_calibrated_pcas_predictor.py`, `src/run_sana_calibrated_pcas.py` |

## Repository Layout

```text
configs/       YAML configs for inference, PCAS, LoRA validation, and calibration.
docs/          Clean documentation for reproduction, results, and repository policy.
prompts/       Controlled benchmark prompts and validation prompts.
report/        Research notes, draft writeups, and LaTeX report source.
results/       Lightweight CSV/JSON/Markdown result tables.
src/           Experiment, evaluation, visualization, and PCAS source code.
tools/         Utility scripts for report generation.
```

Generated samples are written to `outputs/`, which is ignored by Git. Private DreamBooth images are under `data/` and `ZZM Earphone/`, also ignored.

## Installation

Use Python 3.11. On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-torch-cu128.txt
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The PyTorch requirement file targets CUDA 12.8. If your CUDA stack differs, install the matching PyTorch wheel from the official PyTorch selector, then install `requirements.txt`.

## Quick Start

Run a small SANA smoke test:

```powershell
.\.venv\Scripts\python.exe .\src\run_sana_baseline.py --config .\configs\day1_smoke.yaml
```

Run the main Balanced-PCAS policy:

```powershell
.\.venv\Scripts\python.exe .\src\run_sana_pcas.py --config .\configs\day3_pcas_balanced.yaml
```

Run Calibrated-PCAS after the predictor file is available:

```powershell
.\.venv\Scripts\python.exe .\src\run_sana_calibrated_pcas.py `
  --config .\configs\day6_calibrated_pcas.yaml `
  --predictor .\results\day6_calibrated_pcas_tree.json `
  --output-dir .\outputs\day6_calibrated_pcas
```

## Reproducing Results

Detailed command sequences are in [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md). The short version is:

1. Generate fixed-step baselines with `configs/day2_baseline_*.yaml`.
2. Generate PCAS variants with `configs/day3_*.yaml`.
3. Evaluate CLIPScore with `src/evaluate_clipscore.py`.
4. Build Day 6 calibration labels with `src/build_calibration_dataset.py`.
5. Train and run calibrated predictors with `src/train_calibrated_pcas_predictor.py` and `src/run_sana_calibrated_pcas.py`.

Existing lightweight result tables are committed under `results/`; image outputs and checkpoints are not.

## Key Results

Balanced-PCAS is the most stable efficiency-oriented main result:

| Method | Avg steps | Avg time no-warmup | Speedup vs Fixed-20 | Avg CLIPScore |
| --- | ---: | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 0.996s | 0.0% | 35.762 |
| Rule-PCAS | 19.333 | 0.977s | 1.9% | 35.750 |
| Balanced-PCAS | 16.000 | 0.751s | 24.6% | 35.772 |
| DeepSeek-Balanced | 18.467 | 0.844s | 15.3% | 35.813 |

Calibrated-PCAS is a proof-of-concept extension that learns a minimal sufficient step predictor from a small 30-prompt calibration grid:

| Method | Avg steps | Avg time no-warmup | Speedup vs Fixed-20 | Avg CLIPScore | Constraint satisfaction |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fixed-20 | 20.000 | 1.537s | 0.0% | 35.762 | 100.0% |
| Balanced-PCAS | 16.000 | 1.740s | -13.2% | 35.772 | 73.3% |
| Calibrated-PCAS | 10.667 | 0.675s | 56.1% | 36.234 | 96.7% |
| LLM-feature Calibrated-PCAS | 11.333 | 1.093s | 28.9% | 36.230 | 96.7% |

The Day 6 timing table comes from a later rerun and should be read together with average steps and constraint satisfaction. See [docs/RESULTS.md](docs/RESULTS.md) for interpretation and caveats.

## DeepSeek-Assisted Policies

DeepSeek-assisted scripts read the API key from the environment variable `DEEPSEEK_API_KEY` or from a local `API_DEEPSEEK.txt` file. The local file is ignored by Git.

```powershell
$env:DEEPSEEK_API_KEY="your_key_here"
.\.venv\Scripts\python.exe .\src\run_sana_pcas_deepseek.py --config .\configs\day3_pcas_deepseek_balanced.yaml
```

Cached semantic labels and prompt features are stored as lightweight JSON/CSV files under `results/`.

## Artifact Policy

The following are intentionally not committed:

- API keys and `.env` files.
- Generated images and per-image metadata in `outputs/`.
- Private or derived DreamBooth images in `data/` and `ZZM Earphone/`.
- LoRA weights, checkpoints, optimizer states, and model binaries.
- Presentation binaries, Word documents, PDFs, logs, and process ids.

This keeps the repository small, reviewable, and suitable for public GitHub hosting.

## Citation

If you use this repository, please cite it with [CITATION.cff](CITATION.cff). Please also cite the original SANA paper and the Hugging Face Diffusers project when relevant.

## Acknowledgements

This project builds on SANA: Efficient High-Resolution Image Synthesis with Linear Diffusion Transformers, Hugging Face Diffusers, PyTorch, Transformers, Accelerate, CLIP, and DeepSeek for optional semantic prompt analysis.
