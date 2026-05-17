from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import torch
import yaml
from diffusers import SanaPipeline


DTYPES = {
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
    "float32": torch.float32,
}


def load_config(path: str | None) -> dict:
    if path is None:
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def read_prompts(prompt_file: str | None, prompt: str | None) -> list[str]:
    prompts: list[str] = []
    if prompt:
        prompts.append(prompt)
    if prompt_file:
        for line in Path(prompt_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                prompts.append(line)
    if not prompts:
        raise ValueError("Provide --prompt or --prompt-file in the config/CLI.")
    return prompts


def safe_name(text: str, limit: int = 64) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text[:limit] or "prompt"


def move_auxiliary_modules(pipe: SanaPipeline, dtype: torch.dtype, device: str) -> None:
    for name in ("vae", "text_encoder"):
        module = getattr(pipe, name, None)
        if module is not None:
            module.to(device=device, dtype=dtype)


def load_pipeline(config: dict) -> SanaPipeline:
    model_id = config.get("model_id", "Efficient-Large-Model/Sana_600M_512px_diffusers")
    dtype = DTYPES[config.get("torch_dtype", "float16")]
    variant = config.get("variant")

    kwargs = {"torch_dtype": dtype}
    if variant:
        kwargs["variant"] = variant
    if "local_files_only" in config:
        kwargs["local_files_only"] = bool(config["local_files_only"])

    try:
        pipe = SanaPipeline.from_pretrained(model_id, **kwargs)
    except OSError:
        if "variant" in kwargs:
            kwargs.pop("variant")
            pipe = SanaPipeline.from_pretrained(model_id, **kwargs)
        else:
            raise

    device = config.get("device", "cuda")
    pipe = pipe.to(device)

    auxiliary_dtype_name = config.get("auxiliary_dtype")
    if auxiliary_dtype_name:
        move_auxiliary_modules(pipe, DTYPES[auxiliary_dtype_name], device)

    pipe.set_progress_bar_config(disable=False)
    return pipe


def generate_one(pipe: SanaPipeline, prompt: str, config: dict, index: int, output_dir: Path) -> dict:
    device = config.get("device", "cuda")
    seed = int(config.get("seed", 42)) + index
    generator = torch.Generator(device=device).manual_seed(seed)

    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()

    start = time.perf_counter()
    result = pipe(
        prompt=prompt,
        height=int(config.get("height", 512)),
        width=int(config.get("width", 512)),
        num_inference_steps=int(config.get("num_inference_steps", 10)),
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

    metadata = {
        "prompt": prompt,
        "image_path": str(image_path),
        "model_id": config.get("model_id"),
        "height": int(config.get("height", 512)),
        "width": int(config.get("width", 512)),
        "num_inference_steps": int(config.get("num_inference_steps", 10)),
        "guidance_scale": float(config.get("guidance_scale", 4.5)),
        "seed": seed,
        "elapsed_seconds": elapsed,
        "peak_vram_gb": peak_vram_gb,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a SANA baseline inference batch.")
    parser.add_argument("--config", default=None)
    parser.add_argument("--model-id", default=None)
    parser.add_argument("--prompt-file", default=None)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--num-inference-steps", type=int, default=None)
    parser.add_argument("--guidance-scale", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    for key, value in vars(args).items():
        if key == "config" or value is None:
            continue
        config[key] = value

    if config.get("device", "cuda") == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available. Check the PyTorch CUDA installation first.")

    output_dir = Path(config.get("output_dir", "outputs/day1_baseline"))
    output_dir.mkdir(parents=True, exist_ok=True)
    prompts = read_prompts(config.get("prompt_file"), config.get("prompt"))

    pipe = load_pipeline(config)
    results = [generate_one(pipe, prompt, config, i, output_dir) for i, prompt in enumerate(prompts, start=1)]

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
