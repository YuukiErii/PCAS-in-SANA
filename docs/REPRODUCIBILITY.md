# Reproducibility Guide

This guide lists the main commands needed to reproduce the lightweight tables committed in `results/`. Generated images, model checkpoints, and private data are not stored in Git.

## 1. Environment

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-torch-cu128.txt
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Check the environment:

```powershell
.\.venv\Scripts\python.exe .\src\day1_env_check.py --output .\results\day1_environment.md
```

`results/day1_environment.md` is ignored because it contains machine-specific paths and process information.

## 2. Fixed-Step Baselines

```powershell
.\.venv\Scripts\python.exe .\src\run_sana_baseline.py --config .\configs\day2_baseline_10steps.yaml
.\.venv\Scripts\python.exe .\src\run_sana_baseline.py --config .\configs\day2_baseline_20steps.yaml
.\.venv\Scripts\python.exe .\src\run_sana_baseline.py --config .\configs\day2_baseline_28steps.yaml
.\.venv\Scripts\python.exe .\src\summarize_day2_results.py
```

## 3. Rule and Balanced PCAS

```powershell
.\.venv\Scripts\python.exe .\src\run_sana_pcas.py --config .\configs\day3_pcas.yaml
.\.venv\Scripts\python.exe .\src\run_sana_pcas.py --config .\configs\day3_pcas_balanced.yaml
.\.venv\Scripts\python.exe .\src\summarize_day3_results.py
.\.venv\Scripts\python.exe .\src\summarize_pcas_balanced_results.py
```

## 4. DeepSeek-Assisted PCAS

Set the API key in the shell:

```powershell
$env:DEEPSEEK_API_KEY="your_key_here"
```

Then run:

```powershell
.\.venv\Scripts\python.exe .\src\run_sana_pcas_deepseek.py --config .\configs\day3_pcas_deepseek.yaml
.\.venv\Scripts\python.exe .\src\run_sana_pcas_deepseek.py --config .\configs\day3_pcas_deepseek_balanced.yaml
.\.venv\Scripts\python.exe .\src\summarize_day3_deepseek_results.py
.\.venv\Scripts\python.exe .\src\summarize_deepseek_balanced_results.py
```

The code also supports a local `API_DEEPSEEK.txt` file. That file is ignored by Git.

## 5. CLIPScore Evaluation

Evaluate the default Day 4 methods:

```powershell
.\.venv\Scripts\python.exe .\src\evaluate_clipscore.py
```

Evaluate a custom method set, for example the Day 6 final comparison:

```powershell
.\.venv\Scripts\python.exe .\src\evaluate_clipscore.py `
  --no-default-methods `
  --output-prefix day6_calibrated_pcas_final_comparison `
  --cache .\results\day6_method_comparison_clipscore_cache.json `
  --title "Day6 Calibrated-PCAS Final CLIPScore Summary" `
  --extra-method fixed_20=outputs/day2_baseline_20steps/summary.json `
  --extra-method balanced_pcas=outputs/day3_pcas_balanced/summary.json `
  --extra-method deepseek_balanced_pcas=outputs/day3_pcas_deepseek_balanced/summary.json `
  --extra-method calibrated_pcas=outputs/day6_calibrated_pcas/summary.json `
  --extra-method calibrated_pcas_llm_features=outputs/day6_calibrated_pcas_llm_features/summary.json
```

## 6. Calibrated-PCAS

Generate a calibration grid:

```powershell
.\.venv\Scripts\python.exe .\src\run_sana_calibration_grid.py --config .\configs\day6_calibrated_pcas.yaml
```

Build minimal sufficient step labels:

```powershell
.\.venv\Scripts\python.exe .\src\build_calibration_dataset.py
```

Train the lightweight decision-tree predictor:

```powershell
.\.venv\Scripts\python.exe .\src\train_calibrated_pcas_predictor.py
```

Run calibrated inference:

```powershell
.\.venv\Scripts\python.exe .\src\run_sana_calibrated_pcas.py `
  --config .\configs\day6_calibrated_pcas.yaml `
  --predictor .\results\day6_calibrated_pcas_tree.json `
  --output-dir .\outputs\day6_calibrated_pcas
```

For the LLM-feature variant, pass the feature CSV:

```powershell
.\.venv\Scripts\python.exe .\src\run_sana_calibrated_pcas.py `
  --config .\configs\day6_calibrated_pcas.yaml `
  --predictor .\results\day6_calibrated_pcas_llm_tree.json `
  --feature-file .\results\day6_deepseek_prompt_features.csv `
  --output-dir .\outputs\day6_calibrated_pcas_llm_features
```

## 7. Optional LoRA Personalization

LoRA training data and weights are private/local artifacts. The included scripts support dataset preparation and validation, but the image data and generated LoRA weights are ignored:

```powershell
.\.venv\Scripts\python.exe .\src\prepare_lora_dataset.py
.\.venv\Scripts\python.exe .\src\run_sana_lora_validation.py --config .\configs\day5_lora_validation.yaml
```
