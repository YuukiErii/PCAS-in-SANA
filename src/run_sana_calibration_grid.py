from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import torch

from prompt_features import feature_row
from run_sana_baseline import load_config, load_pipeline, read_prompts, safe_name


def parse_steps(value: Any) -> list[int]:
    if value is None:
        return [8, 12, 16, 20, 24, 28]
    if isinstance(value, str):
        return [int(part.strip()) for part in value.split(",") if part.strip()]
    return [int(step) for step in value]


def metadata_paths(output_dir: Path, prompt_index: int, step: int, prompt: str) -> tuple[Path, Path]:
    stem = f"{prompt_index:02d}_s{step:02d}_{safe_name(prompt)}"
    return output_dir / f"{stem}.png", output_dir / f"{stem}.json"


def generate_one(
    pipe,
    prompt: str,
    config: dict,
    prompt_index: int,
    step: int,
    output_dir: Path,
    force: bool = False,
) -> dict:
    image_path, metadata_path = metadata_paths(output_dir, prompt_index, step, prompt)
    if not force and image_path.exists() and metadata_path.exists():
        return json.loads(metadata_path.read_text(encoding="utf-8"))

    device = config.get("device", "cuda")
    seed = int(config.get("seed", 42)) + prompt_index
    generator = torch.Generator(device=device).manual_seed(seed)

    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()

    start = time.perf_counter()
    result = pipe(
        prompt=prompt,
        height=int(config.get("height", 512)),
        width=int(config.get("width", 512)),
        num_inference_steps=step,
        guidance_scale=float(config.get("guidance_scale", 4.5)),
        generator=generator,
    )
    if device == "cuda":
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - start

    peak_vram_gb = None
    if device == "cuda":
        peak_vram_gb = torch.cuda.max_memory_allocated() / 1024**3

    result.images[0].save(image_path)
    features = feature_row(prompt)
    features.pop("prompt", None)
    metadata = {
        "prompt": prompt,
        "prompt_index": prompt_index,
        "image_path": str(image_path),
        "model_id": config.get("model_id"),
        "height": int(config.get("height", 512)),
        "width": int(config.get("width", 512)),
        "num_inference_steps": step,
        "selected_steps": step,
        "guidance_scale": float(config.get("guidance_scale", 4.5)),
        "selected_guidance_scale": float(config.get("guidance_scale", 4.5)),
        "seed": seed,
        "elapsed_seconds": elapsed,
        "peak_vram_gb": peak_vram_gb,
        "reference_steps": int(config.get("reference_steps", 20)),
        "is_reference_step": step == int(config.get("reference_steps", 20)),
        **features,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return metadata


def write_summary(path: Path, records: list[dict]) -> None:
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a multi-step calibration grid for Calibrated PCAS.")
    parser.add_argument("--config", default="configs/day6_calibrated_pcas.yaml")
    parser.add_argument("--model-id", default=None)
    parser.add_argument("--prompt-file", default=None)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--steps", default=None, help="Comma-separated override, for example 8,12,16,20,24,28.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    for key, value in vars(args).items():
        if key in {"config", "steps", "force"} or value is None:
            continue
        config[key] = value
    if args.steps:
        config["calibration_steps"] = parse_steps(args.steps)

    if config.get("device", "cuda") == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available. Check the PyTorch CUDA installation first.")

    output_dir = Path(config.get("output_dir", "outputs/day6_calibration_grid"))
    output_dir.mkdir(parents=True, exist_ok=True)
    prompts = read_prompts(config.get("prompt_file"), config.get("prompt"))
    steps = parse_steps(config.get("calibration_steps"))

    pipe = load_pipeline(config)
    records: list[dict] = []
    summary_path = output_dir / "summary.json"
    for prompt_index, prompt in enumerate(prompts, start=1):
        for step in steps:
            record = generate_one(pipe, prompt, config, prompt_index, step, output_dir, force=args.force)
            records.append(record)
            write_summary(summary_path, records)

    write_summary(summary_path, records)
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
