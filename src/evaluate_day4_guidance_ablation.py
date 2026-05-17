from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

import torch
from transformers import CLIPModel, CLIPProcessor

from evaluate_clipscore import compute_clip_score, load_cache, prompt_group, save_cache, write_csv


GUIDANCE_RUNS = [
    ("guidance_1_5", 1.5, "outputs/day4_guidance_1_5/summary.json"),
    ("guidance_3_5", 3.5, "outputs/day4_guidance_3_5/summary.json"),
    ("guidance_4_5", 4.5, "outputs/day2_baseline_20steps/summary.json"),
    ("guidance_5_5", 5.5, "outputs/day4_guidance_5_5/summary.json"),
    ("guidance_6_5", 6.5, "outputs/day4_guidance_6_5/summary.json"),
    ("guidance_8_5", 8.5, "outputs/day4_guidance_8_5/summary.json"),
]

GROUPS = ["all", "10_words", "30_words", "50_words"]


def cache_key(row: dict[str, Any], model_id: str) -> str:
    return json.dumps(
        {
            "model_id": model_id,
            "experiment": "day4_guidance_ablation",
            "method": row["method"],
            "prompt": row["prompt"],
            "image_path": row["image_path"],
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def load_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for method, guidance_scale, summary_path in GUIDANCE_RUNS:
        records = json.loads(Path(summary_path).read_text(encoding="utf-8"))
        for index, record in enumerate(records, start=1):
            word_count = len(record["prompt"].split())
            rows.append(
                {
                    "method": method,
                    "guidance_scale": guidance_scale,
                    "prompt_index": index,
                    "prompt_length_group": prompt_group(word_count),
                    "word_count": word_count,
                    "prompt": record["prompt"],
                    "image_path": record["image_path"],
                    "num_inference_steps": int(record["num_inference_steps"]),
                    "elapsed_seconds": float(record["elapsed_seconds"]),
                    "peak_vram_gb": float(record["peak_vram_gb"]),
                    "is_first_prompt": index == 1,
                }
            )
    return rows


def summarize(rows: list[dict[str, Any]], method: str, group: str) -> dict[str, Any]:
    group_rows = [row for row in rows if row["method"] == method and (group == "all" or row["prompt_length_group"] == group)]
    no_warmup = [row for row in group_rows if not row["is_first_prompt"]]
    elapsed_source = no_warmup if no_warmup else group_rows
    return {
        "method": method,
        "guidance_scale": group_rows[0]["guidance_scale"],
        "prompt_length_group": group,
        "num_images": len(group_rows),
        "avg_words": mean(row["word_count"] for row in group_rows),
        "avg_steps": mean(row["num_inference_steps"] for row in group_rows),
        "avg_elapsed_seconds_no_warmup": mean(row["elapsed_seconds"] for row in elapsed_source),
        "avg_clip_cosine": mean(row["clip_cosine"] for row in group_rows),
        "avg_clip_score": mean(row["clip_score"] for row in group_rows),
        "min_clip_score": min(row["clip_score"] for row in group_rows),
        "max_clip_score": max(row["clip_score"] for row in group_rows),
        "avg_peak_vram_gb": mean(row["peak_vram_gb"] for row in group_rows),
    }


def build_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [summarize(rows, method, group) for method, _, _ in GUIDANCE_RUNS for group in GROUPS]


def format_float(value: object) -> str:
    return f"{float(value):.3f}"


def write_markdown(path: Path, summary_rows: list[dict[str, Any]], model_id: str) -> None:
    lines = [
        "# Day 4 Guidance Ablation Summary",
        "",
        f"CLIP model: `{model_id}`.",
        "",
        "All runs use 20 inference steps, 512x512 resolution, and the same 30 prompts. Guidance 4.5 reuses the Day 2 fixed-20 baseline. Guidance 1.5 and 8.5 are added as low/high stress-test points beyond the original 3.5-6.5 band.",
        "",
        "| Guidance | Group | Images | Avg time no-warmup (s) | Avg CLIPScore | Min | Max |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            "| {guidance} | {group} | {num_images} | {time} | {score} | {min_score} | {max_score} |".format(
                guidance=format_float(row["guidance_scale"]),
                group=row["prompt_length_group"],
                num_images=row["num_images"],
                time=format_float(row["avg_elapsed_seconds_no_warmup"]),
                score=format_float(row["avg_clip_score"]),
                min_score=format_float(row["min_clip_score"]),
                max_score=format_float(row["max_clip_score"]),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Day 4 guidance-scale ablation with CLIPScore.")
    parser.add_argument("--model-id", default="openai/clip-vit-base-patch32")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--cache", default="results/day4_clipscore_cache.json")
    args = parser.parse_args()

    rows = load_records()
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
        "guidance_scale",
        "prompt_index",
        "prompt_length_group",
        "word_count",
        "prompt",
        "image_path",
        "num_inference_steps",
        "elapsed_seconds",
        "peak_vram_gb",
        "is_first_prompt",
        "clip_cosine",
        "clip_score",
    ]
    write_csv(results_dir / "day4_guidance_ablation_results.csv", rows, detail_fields)

    summary_rows = build_summary(rows)
    summary_fields = [
        "method",
        "guidance_scale",
        "prompt_length_group",
        "num_images",
        "avg_words",
        "avg_steps",
        "avg_elapsed_seconds_no_warmup",
        "avg_clip_cosine",
        "avg_clip_score",
        "min_clip_score",
        "max_clip_score",
        "avg_peak_vram_gb",
    ]
    write_csv(results_dir / "day4_guidance_ablation_summary.csv", summary_rows, summary_fields)
    write_markdown(results_dir / "day4_guidance_ablation_summary.md", summary_rows, args.model_id)
    print(f"Wrote {results_dir / 'day4_guidance_ablation_results.csv'}")
    print(f"Wrote {results_dir / 'day4_guidance_ablation_summary.csv'}")
    print(f"Wrote {results_dir / 'day4_guidance_ablation_summary.md'}")


if __name__ == "__main__":
    main()
