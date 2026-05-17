from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

import torch

from prompt_complexity import analyze_prompt
from run_sana_baseline import load_config, load_pipeline, read_prompts, safe_name


def generate_one_pcas(pipe, prompt: str, config: dict, index: int, output_dir: Path) -> dict:
    device = config.get("device", "cuda")
    seed = int(config.get("seed", 42)) + index
    generator = torch.Generator(device=device).manual_seed(seed)
    decision = analyze_prompt(prompt, config.get("pcas_policy"))

    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()

    start = time.perf_counter()
    result = pipe(
        prompt=prompt,
        height=decision.selected_height,
        width=decision.selected_width,
        num_inference_steps=decision.selected_steps,
        guidance_scale=decision.selected_guidance_scale,
        generator=generator,
    )
    if device == "cuda":
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - start

    peak_vram_gb = None
    if device == "cuda":
        peak_vram_gb = torch.cuda.max_memory_allocated() / 1024**3

    stem = f"{index:02d}_{decision.complexity_label}_{safe_name(prompt)}"
    image_path = output_dir / f"{stem}.png"
    metadata_path = output_dir / f"{stem}.json"
    result.images[0].save(image_path)

    metadata = {
        "prompt": prompt,
        "image_path": str(image_path),
        "model_id": config.get("model_id"),
        "seed": seed,
        "elapsed_seconds": elapsed,
        "peak_vram_gb": peak_vram_gb,
        **asdict(decision),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Prompt-Complexity Adaptive Sampling with SANA.")
    parser.add_argument("--config", default=None)
    parser.add_argument("--model-id", default=None)
    parser.add_argument("--prompt-file", default=None)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    for key, value in vars(args).items():
        if key == "config" or value is None:
            continue
        config[key] = value

    if config.get("device", "cuda") == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available. Check the PyTorch CUDA installation first.")

    output_dir = Path(config.get("output_dir", "outputs/day3_pcas"))
    output_dir.mkdir(parents=True, exist_ok=True)
    prompts = read_prompts(config.get("prompt_file"), config.get("prompt"))

    pipe = load_pipeline(config)
    results = [generate_one_pcas(pipe, prompt, config, i, output_dir) for i, prompt in enumerate(prompts, start=1)]

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
