# Repository Structure

The repository follows a paper-artifact layout while preserving the default paths used by the experiment scripts.

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
|-- docs/
|-- prompts/
|-- report/
|-- results/
|-- src/
`-- tools/
```

## Public Source and Configs

- `src/` contains runnable source code for inference, prompt analysis, CLIPScore evaluation, calibration, and visualization.
- `configs/` contains YAML configs for the experiments.
- `prompts/` contains the controlled prompt benchmark and validation prompt files.
- `tools/` contains utility scripts for draft report generation.

## Public Lightweight Artifacts

- `results/*.csv`, `results/*.json`, and `results/*.md` contain lightweight numeric summaries and cached analysis tables.
- `report/*.md` and `report/latex/*.tex` contain draft writeups and LaTeX source.

## Local-Only Artifacts

The following paths are ignored:

- `outputs/`: generated images and per-image metadata.
- `data/` and `ZZM Earphone/`: private or derived DreamBooth images.
- `.venv/`: Python environment.
- `.codex_tmp/`: local temporary files.
- `results/figures/`: generated figures and image grids.
- `*.safetensors`, `*.bin`, `*.pt`, `*.pth`, `*.ckpt`: model weights and checkpoints.
- `*.ppt`, `*.pptx`, `*.docx`, `SANA.pdf`: presentation, document, and local paper files.
- `API_DEEPSEEK.txt`, `.env`: secrets and local environment files.

This keeps the GitHub repository small and reproducible without leaking private data or credentials.
