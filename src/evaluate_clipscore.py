from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


METHODS = [
    ("fixed_10", "outputs/day2_baseline_10steps/summary.json"),
    ("fixed_20", "outputs/day2_baseline_20steps/summary.json"),
    ("fixed_28", "outputs/day2_baseline_28steps/summary.json"),
    ("rule_pcas_7_2", "outputs/day3_pcas/summary.json"),
    ("deepseek_pcas_7_3", "outputs/day3_pcas_deepseek/summary.json"),
]


def prompt_group(word_count: int) -> str:
    if word_count <= 20:
        return "10_words"
    if word_count <= 40:
        return "30_words"
    return "50_words"


def selected_steps(record: dict[str, Any]) -> int:
    if "selected_steps" in record:
        return int(record["selected_steps"])
    return int(record["num_inference_steps"])


def selected_guidance(record: dict[str, Any]) -> float:
    if "selected_guidance_scale" in record:
        return float(record["selected_guidance_scale"])
    return float(record["guidance_scale"])


def selected_size(record: dict[str, Any]) -> tuple[int, int]:
    if "selected_height" in record and "selected_width" in record:
        return int(record["selected_height"]), int(record["selected_width"])
    return int(record["height"]), int(record["width"])


def parse_extra_method(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Extra methods must use METHOD=SUMMARY_JSON.")
    method, summary_path = value.split("=", 1)
    method = method.strip()
    summary_path = summary_path.strip()
    if not method or not summary_path:
        raise argparse.ArgumentTypeError("Extra methods must use METHOD=SUMMARY_JSON.")
    return method, summary_path


def load_records(methods: list[tuple[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for method, summary_path in methods:
        path = Path(summary_path)
        records = json.loads(path.read_text(encoding="utf-8"))
        for index, record in enumerate(records, start=1):
            word_count = len(record["prompt"].split())
            height, width = selected_size(record)
            rows.append(
                {
                    "method": method,
                    "prompt_index": index,
                    "prompt_length_group": prompt_group(word_count),
                    "word_count": word_count,
                    "prompt": record["prompt"],
                    "image_path": record["image_path"],
                    "selected_steps": selected_steps(record),
                    "selected_guidance_scale": selected_guidance(record),
                    "height": height,
                    "width": width,
                    "elapsed_seconds": float(record["elapsed_seconds"]),
                    "peak_vram_gb": float(record["peak_vram_gb"]),
                    "is_first_prompt": index == 1,
                }
            )
    return rows


def cache_key(row: dict[str, Any], model_id: str) -> str:
    return json.dumps(
        {
            "model_id": model_id,
            "method": row["method"],
            "prompt": row["prompt"],
            "image_path": row["image_path"],
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def load_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


@torch.inference_mode()
def compute_clip_score(
    model: CLIPModel,
    processor: CLIPProcessor,
    prompt: str,
    image_path: str,
    device: str,
) -> tuple[float, float]:
    image = Image.open(image_path).convert("RGB")
    inputs = processor(text=[prompt], images=[image], return_tensors="pt", padding=True, truncation=True).to(device)
    outputs = model(**inputs)
    image_features = outputs.image_embeds / outputs.image_embeds.norm(dim=-1, keepdim=True)
    text_features = outputs.text_embeds / outputs.text_embeds.norm(dim=-1, keepdim=True)
    cosine = float((image_features * text_features).sum(dim=-1).item())
    return cosine, max(cosine, 0.0) * 100.0


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, Any]], method: str, group: str) -> dict[str, Any]:
    group_rows = [row for row in rows if row["method"] == method and (group == "all" or row["prompt_length_group"] == group)]
    no_warmup = [row for row in group_rows if not row["is_first_prompt"]]
    elapsed_source = no_warmup if no_warmup else group_rows
    return {
        "method": method,
        "prompt_length_group": group,
        "num_images": len(group_rows),
        "avg_words": mean(row["word_count"] for row in group_rows),
        "avg_steps": mean(row["selected_steps"] for row in group_rows),
        "avg_guidance_scale": mean(row["selected_guidance_scale"] for row in group_rows),
        "avg_elapsed_seconds_no_warmup": mean(row["elapsed_seconds"] for row in elapsed_source),
        "avg_clip_cosine": mean(row["clip_cosine"] for row in group_rows),
        "avg_clip_score": mean(row["clip_score"] for row in group_rows),
        "min_clip_score": min(row["clip_score"] for row in group_rows),
        "max_clip_score": max(row["clip_score"] for row in group_rows),
        "avg_peak_vram_gb": mean(row["peak_vram_gb"] for row in group_rows),
    }


def build_summary(rows: list[dict[str, Any]], methods: list[tuple[str, str]]) -> list[dict[str, Any]]:
    methods = [method for method, _ in methods]
    groups = ["all", "10_words", "30_words", "50_words"]
    return [summarize(rows, method, group) for method in methods for group in groups]


def format_float(value: object) -> str:
    return f"{float(value):.3f}"


def write_markdown(path: Path, summary_rows: list[dict[str, Any]], model_id: str) -> None:
    lines = [
        "# Day 4 CLIPScore Summary",
        "",
        f"CLIP model: `{model_id}`.",
        "",
        "The reported score is cosine similarity between CLIP image and text embeddings multiplied by 100. Higher is better.",
        "",
        "| Method | Group | Images | Avg steps | Avg time no-warmup (s) | Avg CLIPScore | Min | Max |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            "| {method} | {group} | {num_images} | {steps} | {time} | {score} | {min_score} | {max_score} |".format(
                method=row["method"],
                group=row["prompt_length_group"],
                num_images=row["num_images"],
                steps=format_float(row["avg_steps"]),
                time=format_float(row["avg_elapsed_seconds_no_warmup"]),
                score=format_float(row["avg_clip_score"]),
                min_score=format_float(row["min_clip_score"]),
                max_score=format_float(row["max_clip_score"]),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate image-text alignment with CLIP cosine score.")
    parser.add_argument("--model-id", default="openai/clip-vit-base-patch32")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--cache", default="results/day4_clipscore_cache.json")
    parser.add_argument("--extra-method", action="append", type=parse_extra_method, default=[])
    parser.add_argument("--output-prefix", default="day4_clipscore")
    args = parser.parse_args()

    methods = METHODS + args.extra_method
    rows = load_records(methods)
    cache_path = Path(args.cache)
    cache = load_cache(cache_path)

    model = CLIPModel.from_pretrained(args.model_id).to(args.device)
    processor = CLIPProcessor.from_pretrained(args.model_id)
    model.eval()

    for row in rows:
        key = cache_key(row, args.model_id)
        if key not in cache:
            cosine, score = compute_clip_score(model, processor, row["prompt"], row["image_path"], args.device)
            cache[key] = {"clip_cosine": cosine, "clip_score": score}
        row["clip_cosine"] = float(cache[key]["clip_cosine"])
        row["clip_score"] = float(cache[key]["clip_score"])

    save_cache(cache_path, cache)
    results_dir = Path(args.results_dir)
    detail_fields = [
        "method",
        "prompt_index",
        "prompt_length_group",
        "word_count",
        "prompt",
        "image_path",
        "selected_steps",
        "selected_guidance_scale",
        "height",
        "width",
        "elapsed_seconds",
        "peak_vram_gb",
        "is_first_prompt",
        "clip_cosine",
        "clip_score",
    ]
    write_csv(results_dir / f"{args.output_prefix}_results.csv", rows, detail_fields)

    summary_rows = build_summary(rows, methods)
    summary_fields = [
        "method",
        "prompt_length_group",
        "num_images",
        "avg_words",
        "avg_steps",
        "avg_guidance_scale",
        "avg_elapsed_seconds_no_warmup",
        "avg_clip_cosine",
        "avg_clip_score",
        "min_clip_score",
        "max_clip_score",
        "avg_peak_vram_gb",
    ]
    write_csv(results_dir / f"{args.output_prefix}_summary.csv", summary_rows, summary_fields)
    write_markdown(results_dir / f"{args.output_prefix}_summary.md", summary_rows, args.model_id)
    print(f"Wrote {results_dir / f'{args.output_prefix}_results.csv'}")
    print(f"Wrote {results_dir / f'{args.output_prefix}_summary.csv'}")
    print(f"Wrote {results_dir / f'{args.output_prefix}_summary.md'}")


if __name__ == "__main__":
    main()
