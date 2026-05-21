# Contributing

Contributions are welcome, especially improvements to reproducibility, prompt benchmarks, evaluation scripts, and documentation.

## Development Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-torch-cu128.txt
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Before Submitting Changes

- Do not commit API keys, `.env` files, generated images, model weights, LoRA weights, checkpoints, private data, logs, or presentation binaries.
- Keep experiment defaults compatible with the existing `configs/`, `prompts/`, `results/`, and `outputs/` layout.
- Prefer small, focused changes with clear result tables when adding new experiments.
- Run a syntax check before committing:

```powershell
$files = (Get-ChildItem src -Recurse -Filter *.py).FullName
.\.venv\Scripts\python.exe -m py_compile @files
```

## Documentation

When adding a new method or experiment, update:

- `README.md` for the high-level summary.
- `docs/REPRODUCIBILITY.md` for commands.
- `docs/RESULTS.md` for stable result tables and caveats.
