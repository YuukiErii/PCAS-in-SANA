# Day 1 Status

Date: 2026-05-16

## Completed

- Created the project structure: `configs/`, `prompts/`, `src/`, `outputs/`, `results/`, `report/`.
- Created a Python 3.11 virtual environment in `.venv`.
- Installed PyTorch CUDA and project dependencies.
- Verified CUDA with RTX 5080 Laptop GPU.
- Wrote the environment report to `results/day1_environment.md`.
- Wrote reusable SANA baseline inference code in `src/run_sana_baseline.py`.
- Ran a tiny random SanaPipeline debug pass successfully:
  - Config: `configs/day1_tiny_debug.yaml`
  - Output: `outputs/day1_tiny_debug/summary.json`
- Downloaded the missing official SANA-0.6B 512px text encoder shard with BITS.
- Ran the official SANA-0.6B 512px smoke baseline successfully:
  - Config: `configs/day1_smoke.yaml`
  - Output: `outputs/day1_baseline/summary.json`
  - Prompts generated: 3
  - Steps: 10
  - Guidance scale: 4.5
  - Peak VRAM: about 6.98GB

## Day 1 Official Smoke Results

| Prompt | Time | Output |
| --- | ---: | --- |
| `a red apple on a wooden table, realistic photo` | 2.34s | `outputs/day1_baseline/01_a_red_apple_on_a_wooden_table_realistic_photo.png` |
| `a robot chef cooking pasta in a modern kitchen, cinematic lighting` | 0.53s | `outputs/day1_baseline/02_a_robot_chef_cooking_pasta_in_a_modern_kitchen_cinematic_lightin.png` |
| `a small robot holding a red umbrella next to a cat, in front of a bookstore with a sign that says SANA` | 0.53s | `outputs/day1_baseline/03_a_small_robot_holding_a_red_umbrella_next_to_a_cat_in_front_of_a.png` |

## Recommended Next Step

Run the 1024px baseline if time permits:

```powershell
.\.venv\Scripts\python.exe .\src\run_sana_baseline.py --config .\configs\sana_baseline.yaml
```

For Day 2, build the full prompt benchmark and run fixed-step baselines.
