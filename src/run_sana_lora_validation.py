from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch

from run_sana_baseline import load_config, load_pipeline, read_prompts, safe_name


def generate_one(pipe, prompt: str, config: dict, index: int, output_dir: Path, method: str) -> dict:
    device = config.get("device", "cuda")
    seed = int(config.get("seed", 142)) + index
    generator = torch.Generator(device=device).manual_seed(seed)

    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()

    start = time.perf_counter()
    result = pipe(
        prompt=prompt,
        height=int(config.get("height", 512)),
        width=int(config.get("width", 512)),
        num_inference_steps=int(config.get("num_inference_steps", 20)),
        guidance_scale=float(config.get("guidance_scale", 4.5)),
        generator=generator,
    )
    if device == "cuda":
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - start

    peak_vram_gb = None
    if device == "cuda":
        peak_vram_gb = torch.cuda.max_memory_allocated() / 1024**3

    stem = f"{index:02d}_{safe_name(prompt)}"
    image_path = output_dir / f"{stem}.png"
    metadata_path = output_dir / f"{stem}.json"
    result.images[0].save(image_path)

    is_lora = method != "base"
    metadata = {
        "method": method,
        "prompt": prompt,
        "image_path": str(image_path),
        "model_id": config.get("model_id"),
        "lora_weights": config.get("lora_weights") if is_lora else None,
        "lora_scale": float(config.get("lora_scale", 1.0)) if is_lora else None,
        "height": int(config.get("height", 512)),
        "width": int(config.get("width", 512)),
        "num_inference_steps": int(config.get("num_inference_steps", 20)),
        "guidance_scale": float(config.get("guidance_scale", 4.5)),
        "seed": seed,
        "elapsed_seconds": elapsed,
        "peak_vram_gb": peak_vram_gb,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def write_summary(output_dir: Path, rows: list[dict]) -> None:
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {summary_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate base-vs-LoRA SANA validation images.")
    parser.add_argument("--config", default="configs/day5_lora_validation.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    if config.get("device", "cuda") == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available. Check the PyTorch CUDA installation first.")

    prompts = read_prompts(config.get("prompt_file"), config.get("prompt"))
    base_output_dir = Path(config.get("base_output_dir", "outputs/day5_lora_validation_base"))
    lora_output_dir = Path(config.get("lora_output_dir", "outputs/day5_lora_validation_lora"))
    base_output_dir.mkdir(parents=True, exist_ok=True)
    lora_output_dir.mkdir(parents=True, exist_ok=True)

    pipe = load_pipeline(config)
    if bool(config.get("skip_base", False)) and (base_output_dir / "summary.json").exists():
        print(f"Skipped base generation; using existing {base_output_dir / 'summary.json'}")
    else:
        base_rows = [
            generate_one(pipe, prompt, config, index, base_output_dir, "base")
            for index, prompt in enumerate(prompts, start=1)
        ]
        write_summary(base_output_dir, base_rows)

    lora_weights = config.get("lora_weights")
    if not lora_weights:
        raise ValueError("Provide lora_weights in the config.")
    adapter_name = config.get("lora_adapter_name", "zzmearphone")
    pipe.load_lora_weights(lora_weights, adapter_name=adapter_name)
    pipe.set_adapters(adapter_name, adapter_weights=float(config.get("lora_scale", 1.0)))
    lora_method = config.get("lora_method", "lora")
    lora_rows = [
        generate_one(pipe, prompt, config, index, lora_output_dir, lora_method)
        for index, prompt in enumerate(prompts, start=1)
    ]
    write_summary(lora_output_dir, lora_rows)


if __name__ == "__main__":
    main()
