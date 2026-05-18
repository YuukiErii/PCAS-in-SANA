from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from prompt_features import feature_row


FEATURE_COLUMNS = [
    "word_count",
    "content_word_count",
    "comma_count",
    "object_count",
    "attribute_count",
    "relation_count",
    "spatial_relation_count",
    "action_count",
    "style_constraint_count",
    "text_rendering_flag",
    "scene_density_score",
    "rare_concept_score",
    "lexical_complexity_score",
    "rule_complexity_score",
]


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def cache_key(record: dict[str, Any], model_id: str) -> str:
    return json.dumps(
        {
            "model_id": model_id,
            "prompt": record["prompt"],
            "image_path": record["image_path"],
        },
        ensure_ascii=False,
        sort_keys=True,
    )


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
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fmt(value: float) -> str:
    return f"{value:.3f}"


def enrich_records_with_clip(
    records: list[dict[str, Any]],
    model_id: str,
    device: str,
    cache_path: Path,
) -> list[dict[str, Any]]:
    cache = load_cache(cache_path)
    model = CLIPModel.from_pretrained(model_id).to(device)
    processor = CLIPProcessor.from_pretrained(model_id)
    model.eval()

    rows: list[dict[str, Any]] = []
    for record in records:
        key = cache_key(record, model_id)
        if key not in cache:
            cosine, score = compute_clip_score(model, processor, record["prompt"], record["image_path"], device)
            cache[key] = {"clip_cosine": cosine, "clip_score": score}
        row = dict(record)
        row["clip_model_id"] = model_id
        row["clip_cosine"] = float(cache[key]["clip_cosine"])
        row["clip_score"] = float(cache[key]["clip_score"])
        row["prompt_index"] = int(row.get("prompt_index", 0))
        row["selected_steps"] = int(row.get("selected_steps", row.get("num_inference_steps")))
        row["num_inference_steps"] = int(row.get("num_inference_steps", row["selected_steps"]))
        row["elapsed_seconds"] = float(row["elapsed_seconds"])
        row["peak_vram_gb"] = float(row["peak_vram_gb"]) if row.get("peak_vram_gb") is not None else ""
        row["is_first_prompt"] = row["prompt_index"] == 1
        rows.append(row)

    save_cache(cache_path, cache)
    return rows


def build_labels(rows: list[dict[str, Any]], reference_steps: int, clip_tolerance: float) -> list[dict[str, Any]]:
    by_prompt: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_prompt[int(row["prompt_index"])].append(row)

    labels: list[dict[str, Any]] = []
    for prompt_index in sorted(by_prompt):
        prompt_rows = sorted(by_prompt[prompt_index], key=lambda row: int(row["selected_steps"]))
        reference = next((row for row in prompt_rows if int(row["selected_steps"]) == reference_steps), None)
        if reference is None:
            raise ValueError(f"Prompt {prompt_index} has no reference row for {reference_steps} steps.")
        threshold = float(reference["clip_score"]) - clip_tolerance
        sufficient = [row for row in prompt_rows if float(row["clip_score"]) >= threshold]
        selected = min(sufficient, key=lambda row: int(row["selected_steps"]))
        features = feature_row(reference["prompt"])
        label = {
            "prompt_index": prompt_index,
            "prompt": reference["prompt"],
            **{column: features[column] for column in FEATURE_COLUMNS},
            "reference_steps": reference_steps,
            "reference_clip_score": float(reference["clip_score"]),
            "clip_tolerance": clip_tolerance,
            "clip_threshold": threshold,
            "minimal_sufficient_steps": int(selected["selected_steps"]),
            "minimal_clip_score": float(selected["clip_score"]),
            "minimal_clip_delta_vs_fixed20": float(selected["clip_score"]) - float(reference["clip_score"]),
            "minimal_elapsed_seconds": float(selected["elapsed_seconds"]),
            "fixed20_elapsed_seconds": float(reference["elapsed_seconds"]),
            "time_saving_seconds_vs_fixed20": float(reference["elapsed_seconds"]) - float(selected["elapsed_seconds"]),
            "quality_constraint_satisfied": float(selected["clip_score"]) >= threshold,
        }
        for row in prompt_rows:
            step = int(row["selected_steps"])
            label[f"clip_score_s{step}"] = float(row["clip_score"])
            label[f"elapsed_seconds_s{step}"] = float(row["elapsed_seconds"])
        labels.append(label)
    return labels


def summarize_policy(rows: list[dict[str, Any]], labels: list[dict[str, Any]], reference_steps: int) -> list[dict[str, Any]]:
    by_prompt_step = {
        (int(row["prompt_index"]), int(row["selected_steps"])): row
        for row in rows
    }
    fixed_rows = [by_prompt_step[(int(label["prompt_index"]), reference_steps)] for label in labels]
    oracle_rows = [
        by_prompt_step[(int(label["prompt_index"]), int(label["minimal_sufficient_steps"]))]
        for label in labels
    ]

    def summarize(method: str, selected_rows: list[dict[str, Any]]) -> dict[str, Any]:
        selected_no_warmup = [row for row in selected_rows if int(row["prompt_index"]) != 1]
        fixed_no_warmup = [row for row in fixed_rows if int(row["prompt_index"]) != 1]
        elapsed_source = selected_no_warmup if selected_no_warmup else selected_rows
        fixed_elapsed_source = fixed_no_warmup if fixed_no_warmup else fixed_rows
        label_by_prompt = {int(label["prompt_index"]): label for label in labels}
        satisfied = 0
        deltas: list[float] = []
        for row in selected_rows:
            label = label_by_prompt[int(row["prompt_index"])]
            delta = float(row["clip_score"]) - float(label["reference_clip_score"])
            deltas.append(delta)
            if float(row["clip_score"]) >= float(label["clip_threshold"]):
                satisfied += 1
        fixed_time = mean(float(row["elapsed_seconds"]) for row in fixed_elapsed_source)
        current_time = mean(float(row["elapsed_seconds"]) for row in elapsed_source)
        return {
            "method": method,
            "num_prompts": len(selected_rows),
            "avg_steps": mean(int(row["selected_steps"]) for row in selected_rows),
            "avg_elapsed_seconds_no_warmup": current_time,
            "fixed20_elapsed_seconds_no_warmup": fixed_time,
            "speedup_percent_vs_fixed20": 100.0 * (fixed_time - current_time) / fixed_time,
            "avg_clip_score": mean(float(row["clip_score"]) for row in selected_rows),
            "avg_clip_delta_vs_fixed20": mean(deltas),
            "quality_satisfaction_rate": satisfied / len(selected_rows),
        }

    return [
        summarize("fixed_20", fixed_rows),
        summarize("oracle_min_sufficient", oracle_rows),
    ]


def write_markdown(
    path: Path,
    labels: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    reference_steps: int,
    clip_tolerance: float,
) -> None:
    counts = Counter(int(label["minimal_sufficient_steps"]) for label in labels)
    lines = [
        "# Calibrated PCAS Calibration Dataset",
        "",
        f"Reference policy: Fixed-{reference_steps}.",
        f"Quality constraint: `CLIPScore(s) >= CLIPScore(Fixed-{reference_steps}) - {clip_tolerance}`.",
        "",
        "## Minimal Sufficient Steps Distribution",
        "",
        "| Steps | Prompts |",
        "| ---: | ---: |",
    ]
    for step in sorted(counts):
        lines.append(f"| {step} | {counts[step]} |")

    lines.extend(
        [
            "",
            "## Oracle Policy Summary",
            "",
            "| Method | Prompts | Avg steps | Avg time no-warmup (s) | Speedup vs Fixed-20 | Avg CLIPScore | Avg CLIP delta | Constraint satisfaction |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary_rows:
        lines.append(
            "| {method} | {n} | {steps} | {time} | {speed}% | {clip} | {delta} | {sat}% |".format(
                method=row["method"],
                n=row["num_prompts"],
                steps=fmt(float(row["avg_steps"])),
                time=fmt(float(row["avg_elapsed_seconds_no_warmup"])),
                speed=fmt(float(row["speedup_percent_vs_fixed20"])),
                clip=fmt(float(row["avg_clip_score"])),
                delta=fmt(float(row["avg_clip_delta_vs_fixed20"])),
                sat=fmt(float(row["quality_satisfaction_rate"]) * 100.0),
            )
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- The oracle policy is not a deployable predictor; it is the upper-bound scheduler that directly reads the calibration grid label for each prompt.",
            "- The next step is to train a lightweight predictor from prompt features to the minimal sufficient steps label.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the calibration grid and build minimal sufficient step labels.")
    parser.add_argument("--summary", default="outputs/day6_calibration_grid/summary.json")
    parser.add_argument("--model-id", default="openai/clip-vit-base-patch32")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--cache", default="results/day6_calibration_clipscore_cache.json")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--output-prefix", default="day6_calibration")
    parser.add_argument("--reference-steps", type=int, default=20)
    parser.add_argument("--clip-tolerance", type=float, default=0.2)
    args = parser.parse_args()

    records = load_json(Path(args.summary))
    rows = enrich_records_with_clip(records, args.model_id, args.device, Path(args.cache))
    labels = build_labels(rows, args.reference_steps, args.clip_tolerance)
    summary_rows = summarize_policy(rows, labels, args.reference_steps)

    results_dir = Path(args.results_dir)
    grid_fields = [
        "prompt_index",
        "prompt",
        "selected_steps",
        "guidance_scale",
        "seed",
        "height",
        "width",
        "elapsed_seconds",
        "peak_vram_gb",
        "image_path",
        "is_first_prompt",
        *FEATURE_COLUMNS,
        "clip_model_id",
        "clip_cosine",
        "clip_score",
    ]
    label_fields = list(labels[0].keys())
    summary_fields = [
        "method",
        "num_prompts",
        "avg_steps",
        "avg_elapsed_seconds_no_warmup",
        "fixed20_elapsed_seconds_no_warmup",
        "speedup_percent_vs_fixed20",
        "avg_clip_score",
        "avg_clip_delta_vs_fixed20",
        "quality_satisfaction_rate",
    ]

    write_csv(results_dir / f"{args.output_prefix}_grid_clipscore.csv", rows, grid_fields)
    write_csv(results_dir / f"{args.output_prefix}_labels.csv", labels, label_fields)
    write_csv(results_dir / f"{args.output_prefix}_oracle_summary.csv", summary_rows, summary_fields)
    write_markdown(
        results_dir / f"{args.output_prefix}_summary.md",
        labels,
        summary_rows,
        args.reference_steps,
        args.clip_tolerance,
    )
    print(f"Wrote {results_dir / f'{args.output_prefix}_grid_clipscore.csv'}")
    print(f"Wrote {results_dir / f'{args.output_prefix}_labels.csv'}")
    print(f"Wrote {results_dir / f'{args.output_prefix}_oracle_summary.csv'}")
    print(f"Wrote {results_dir / f'{args.output_prefix}_summary.md'}")


if __name__ == "__main__":
    main()
