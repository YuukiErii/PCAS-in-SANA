# Repository Structure

The repository follows an experiment-artifact layout while preserving the default paths used by the scripts.

```text
PCAS-in-SANA/
|-- README.md
|-- CITATION.cff
|-- LICENSE
|-- NOTICE
|-- CONTRIBUTING.md
|-- requirements.txt
|-- requirements-torch-cu128.txt
|-- configs/
|-- data/
|-- docs/
|-- outputs/
|-- prompts/
|-- results/
`-- src/
```

## Public Source and Configs

- `src/` contains runnable source code for inference, prompt analysis, CLIPScore evaluation, calibration, and visualization.
- `configs/` contains YAML configs for the experiments.
- `prompts/` contains the controlled prompt benchmark and validation prompt files.
- `data/` contains raw and prepared LoRA/DreamBooth data when included for reproducibility.

## Public Artifacts

- `results/*.csv`, `results/*.json`, and `results/*.md` contain lightweight numeric summaries and cached analysis tables.
- `results/figures/` contains generated charts and visual comparison grids.
- `outputs/` contains generated samples, per-run metadata, and LoRA/checkpoint artifacts when present.

## Local-Only Artifacts

The following paths are ignored:

- `.venv/`: Python environment.
- `.codex_tmp/`: local temporary files.
- `private/`: local course deliverables and render previews.
- `report/`, `reports/`, `presentations/`, `slides/`, and common report/PPT filename patterns: compatibility guards against accidentally recreating deliverable folders in the public tree.
- `*.ppt`, `*.pptx`, `*.doc`, `*.docx`, `*.pdf`, `*.tex`: local report and presentation deliverables.
- `*.log`, `*.err.log`, `*.pid`: process noise.
- `API_DEEPSEEK.txt`, `.env`: secrets and local environment files.

This keeps the GitHub repository centered on code, reproducibility assets, results, generated outputs, and weights while keeping local deliverables out of the public tree.
