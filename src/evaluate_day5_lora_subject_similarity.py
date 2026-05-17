from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


def feature_tensor(features: Any) -> torch.Tensor:
    if isinstance(features, torch.Tensor):
        return features
    for name in ("image_embeds", "text_embeds", "pooler_output"):
        value = getattr(features, name, None)
        if isinstance(value, torch.Tensor):
            return value
    if isinstance(features, (tuple, list)) and features and isinstance(features[0], torch.Tensor):
        return features[0]
    raise TypeError(f"Cannot extract a tensor from {type(features).__name__}.")


def load_summary(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_image(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def encode_images(
    model: CLIPModel,
    processor: CLIPProcessor,
    image_paths: list[Path],
    device: str,
) -> torch.Tensor:
    images = [load_image(path) for path in image_paths]
    inputs = processor(images=images, return_tensors="pt").to(device)
    with torch.no_grad():
        features = feature_tensor(model.get_image_features(**inputs))
    return torch.nn.functional.normalize(features, dim=-1)


def encode_texts(
    model: CLIPModel,
    processor: CLIPProcessor,
    prompts: list[str],
    device: str,
) -> torch.Tensor:
    inputs = processor(text=prompts, padding=True, truncation=True, return_tensors="pt").to(device)
    with torch.no_grad():
        features = feature_tensor(model.get_text_features(**inputs))
    return torch.nn.functional.normalize(features, dim=-1)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    method_rows = [row for row in rows if row["method"] == method]
    no_warmup = method_rows[1:] if len(method_rows) > 1 else method_rows
    return {
        "method": method,
        "images": len(method_rows),
        "avg_time_seconds": mean(float(row["elapsed_seconds"]) for row in method_rows),
        "avg_time_no_warmup_seconds": mean(float(row["elapsed_seconds"]) for row in no_warmup),
        "avg_peak_vram_gb": mean(float(row["peak_vram_gb"]) for row in method_rows),
        "avg_reference_clip_similarity": mean(float(row["reference_clip_similarity"]) for row in method_rows),
        "avg_prompt_clipscore": mean(float(row["prompt_clipscore"]) for row in method_rows),
    }


def format_float(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_markdown(path: Path, summary_rows: list[dict[str, Any]], model_id: str) -> None:
    lines = [
        "# Day 5 LoRA Validation Summary",
        "",
        f"CLIP model: `{model_id}`.",
        "",
        "Reference CLIP similarity is the cosine similarity between each generated image and the mean CLIP image embedding of the 9 prepared earphone training photos, multiplied by 100. Higher is better.",
        "",
        "| Method | Images | Avg time no-warmup (s) | Avg peak VRAM (GB) | Avg reference similarity | Avg prompt CLIPScore |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            "| {method} | {images} | {time} | {vram} | {ref_sim} | {clipscore} |".format(
                method=row["method"],
                images=row["images"],
                time=format_float(row["avg_time_no_warmup_seconds"]),
                vram=format_float(row["avg_peak_vram_gb"]),
                ref_sim=format_float(row["avg_reference_clip_similarity"]),
                clipscore=format_float(row["avg_prompt_clipscore"]),
            )
        )
    lines.extend(
        [
            "",
            "Interpretation: this metric is only a proxy for subject identity. It should be used together with the base-vs-LoRA visual grid, because CLIP image embeddings can miss fine-grained product details.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Day 5 LoRA validation images with CLIP image similarity.")
    parser.add_argument("--reference-dir", default="data/dreambooth/zzmearphone")
    parser.add_argument("--base-summary", default="outputs/day5_lora_validation_base/summary.json")
    parser.add_argument("--lora-summary", default="outputs/day5_lora_validation_lora/summary.json")
    parser.add_argument("--model-id", default="openai/clip-vit-base-patch32")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--output-prefix", default="day5_lora_validation")
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available.")

    reference_paths = sorted(Path(args.reference_dir).glob("*.jpg"))
    if not reference_paths:
        raise ValueError(f"No reference images found in {args.reference_dir}")

    records = load_summary(Path(args.base_summary)) + load_summary(Path(args.lora_summary))
    image_paths = [Path(record["image_path"]) for record in records]
    prompts = [record["prompt"] for record in records]

    model = CLIPModel.from_pretrained(args.model_id).to(args.device)
    processor = CLIPProcessor.from_pretrained(args.model_id)

    reference_features = encode_images(model, processor, reference_paths, args.device)
    reference_centroid = torch.nn.functional.normalize(reference_features.mean(dim=0, keepdim=True), dim=-1)
    image_features = encode_images(model, processor, image_paths, args.device)
    text_features = encode_texts(model, processor, prompts, args.device)

    results: list[dict[str, Any]] = []
    for index, (record, image_feature, text_feature) in enumerate(zip(records, image_features, text_features), start=1):
        method = record["method"]
        if method == "lora" and record.get("lora_scale") not in (None, 1, 1.0):
            method = f"lora_scale_{float(record['lora_scale']):g}"
        reference_similarity = float((image_feature.unsqueeze(0) @ reference_centroid.T).item() * 100.0)
        prompt_clipscore = float((image_feature @ text_feature).item() * 100.0)
        results.append(
            {
                "index": index,
                "method": method,
                "prompt": record["prompt"],
                "image_path": record["image_path"],
                "elapsed_seconds": record["elapsed_seconds"],
                "peak_vram_gb": record["peak_vram_gb"],
                "reference_clip_similarity": reference_similarity,
                "prompt_clipscore": prompt_clipscore,
            }
        )

    results_dir = Path("results")
    result_fields = [
        "index",
        "method",
        "prompt",
        "image_path",
        "elapsed_seconds",
        "peak_vram_gb",
        "reference_clip_similarity",
        "prompt_clipscore",
    ]
    write_csv(results_dir / f"{args.output_prefix}_results.csv", results, result_fields)

    methods = list(dict.fromkeys(row["method"] for row in results))
    summary_rows = [summarize(results, method) for method in methods]
    summary_fields = [
        "method",
        "images",
        "avg_time_seconds",
        "avg_time_no_warmup_seconds",
        "avg_peak_vram_gb",
        "avg_reference_clip_similarity",
        "avg_prompt_clipscore",
    ]
    write_csv(results_dir / f"{args.output_prefix}_summary.csv", summary_rows, summary_fields)
    write_markdown(results_dir / f"{args.output_prefix}_summary.md", summary_rows, args.model_id)
    print("Wrote Day 5 LoRA validation metrics.")


if __name__ == "__main__":
    main()
