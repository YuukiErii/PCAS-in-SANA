from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import torch

from prompt_features import feature_row
from run_sana_baseline import load_config, load_pipeline, read_prompts, safe_name
from train_calibrated_pcas_predictor import explain_tree_path, predict_tree
import csv


def load_model(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_feature_map(path: str | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return {row["prompt"]: row for row in csv.DictReader(handle)}


def available_steps(model: dict[str, Any], config: dict[str, Any]) -> list[int]:
    if "allowed_steps" in config:
        return [int(step) for step in config["allowed_steps"]]
    labels = set()
    for rule in model.get("rules", []):
        marker = "-> "
        suffix = " steps"
        if marker in rule and suffix in rule:
            labels.add(int(rule.split(marker, 1)[1].split(suffix, 1)[0]))
    return sorted(labels) if labels else [8, 12, 16, 20, 24]


def choose_available_step(predicted: int, steps: list[int]) -> int:
    for step in sorted(steps):
        if step >= predicted:
            return step
    return max(steps)


def guidance_for_step(config: dict[str, Any], step: int) -> float:
    guidance_by_steps = config.get("guidance_by_steps") or {}
    if step in guidance_by_steps:
        return float(guidance_by_steps[step])
    if str(step) in guidance_by_steps:
        return float(guidance_by_steps[str(step)])
    return float(config.get("guidance_scale", 4.5))


def predict_decision(
    prompt: str,
    model: dict[str, Any],
    config: dict[str, Any],
    feature_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    features = dict(feature_override) if feature_override else feature_row(prompt)
    features["prompt"] = prompt
    raw_prediction = predict_tree(model["tree"], features)
    offset = int(config.get("conservative_offset", model.get("conservative_offset", 0)))
    selected_steps = choose_available_step(raw_prediction + offset, available_steps(model, config))
    return {
        "prompt": prompt,
        "raw_predicted_steps": raw_prediction,
        "conservative_offset": offset,
        "selected_steps": selected_steps,
        "selected_guidance_scale": guidance_for_step(config, selected_steps),
        "selected_height": int(config.get("height", 512)),
        "selected_width": int(config.get("width", 512)),
        "tree_path": explain_tree_path(model["tree"], features),
        **{key: value for key, value in features.items() if key not in {"prompt", "prompt_index"}},
    }


def generate_one(pipe, prompt: str, config: dict, model: dict, index: int, output_dir: Path) -> dict:
    device = config.get("device", "cuda")
    seed = int(config.get("seed", 42)) + index
    generator = torch.Generator(device=device).manual_seed(seed)
    feature_map = config.get("_feature_map", {})
    decision = predict_decision(prompt, model, config, feature_map.get(prompt))

    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()

    start = time.perf_counter()
    result = pipe(
        prompt=prompt,
        height=decision["selected_height"],
        width=decision["selected_width"],
        num_inference_steps=decision["selected_steps"],
        guidance_scale=decision["selected_guidance_scale"],
        generator=generator,
    )
    if device == "cuda":
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - start

    peak_vram_gb = None
    if device == "cuda":
        peak_vram_gb = torch.cuda.max_memory_allocated() / 1024**3

    stem = f"{index:02d}_s{decision['selected_steps']:02d}_{safe_name(prompt)}"
    image_path = output_dir / f"{stem}.png"
    metadata_path = output_dir / f"{stem}.json"
    result.images[0].save(image_path)

    metadata = {
        "prompt": prompt,
        "prompt_index": index,
        "image_path": str(image_path),
        "model_id": config.get("model_id"),
        "seed": seed,
        "elapsed_seconds": elapsed,
        "peak_vram_gb": peak_vram_gb,
        **decision,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SANA with a trained Calibrated-PCAS predictor.")
    parser.add_argument("--config", default="configs/day6_calibrated_pcas.yaml")
    parser.add_argument("--predictor", default="results/day6_calibrated_pcas_tree.json")
    parser.add_argument("--feature-file", default=None)
    parser.add_argument("--model-id", default=None)
    parser.add_argument("--prompt-file", default=None)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--output-dir", default="outputs/day6_calibrated_pcas")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    for key, value in vars(args).items():
        if key in {"config", "predictor"} or value is None:
            continue
        config[key] = value

    if config.get("device", "cuda") == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available. Check the PyTorch CUDA installation first.")

    model = load_model(Path(args.predictor))
    config["_feature_map"] = load_feature_map(args.feature_file)
    output_dir = Path(config.get("output_dir", "outputs/day6_calibrated_pcas"))
    output_dir.mkdir(parents=True, exist_ok=True)
    prompts = read_prompts(config.get("prompt_file"), config.get("prompt"))

    pipe = load_pipeline(config)
    results = [generate_one(pipe, prompt, config, model, i, output_dir) for i, prompt in enumerate(prompts, start=1)]

    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
