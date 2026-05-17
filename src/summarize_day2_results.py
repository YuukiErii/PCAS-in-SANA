from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean


PROMPT_GROUPS = [
    ("10_words", 10, "day2_10word_prompts.txt"),
    ("30_words", 30, "day2_30word_prompts.txt"),
    ("50_words", 50, "day2_50word_prompts.txt"),
]


def count_words(prompt: str) -> int:
    return len(prompt.split())


def read_prompt_groups(prompt_dir: Path) -> dict[str, dict[str, object]]:
    groups: dict[str, dict[str, object]] = {}
    for label, target_words, filename in PROMPT_GROUPS:
        path = prompt_dir / filename
        for line in path.read_text(encoding="utf-8").splitlines():
            prompt = line.strip()
            if prompt and not prompt.startswith("#"):
                groups[prompt] = {
                    "prompt_length_group": label,
                    "target_words": target_words,
                    "actual_words": count_words(prompt),
                }
    return groups


def parse_steps(path: Path, records: list[dict]) -> int:
    if records:
        return int(records[0]["num_inference_steps"])
    match = re.search(r"(\d+)steps", path.parent.name)
    if not match:
        raise ValueError(f"Cannot infer step count from {path}")
    return int(match.group(1))


def load_records(outputs_dir: Path, prompt_groups: dict[str, dict[str, object]]) -> list[dict]:
    rows: list[dict] = []
    for summary_path in sorted(outputs_dir.glob("day2_baseline_*steps/summary.json")):
        records = json.loads(summary_path.read_text(encoding="utf-8"))
        steps = parse_steps(summary_path, records)
        for prompt_index, record in enumerate(records, start=1):
            prompt = record["prompt"]
            group = prompt_groups.get(
                prompt,
                {
                    "prompt_length_group": "unknown",
                    "target_words": "",
                    "actual_words": count_words(prompt),
                },
            )
            rows.append(
                {
                    "method": f"fixed_{steps}",
                    "steps": steps,
                    "prompt_index": prompt_index,
                    "prompt_length_group": group["prompt_length_group"],
                    "target_words": group["target_words"],
                    "actual_words": group["actual_words"],
                    "prompt": prompt,
                    "height": record["height"],
                    "width": record["width"],
                    "guidance_scale": record["guidance_scale"],
                    "seed": record["seed"],
                    "elapsed_seconds": record["elapsed_seconds"],
                    "peak_vram_gb": record["peak_vram_gb"],
                    "image_path": record["image_path"],
                    "is_first_prompt": prompt_index == 1,
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def aggregate(rows: list[dict]) -> list[dict]:
    aggregate_rows: list[dict] = []
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["method"], row["prompt_length_group"])].append(row)

    for (method, group_label), group in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        aggregate_rows.append(summarize_group(method, group_label, group))

    for method in sorted({row["method"] for row in rows}):
        group = [row for row in rows if row["method"] == method]
        aggregate_rows.append(summarize_group(method, "all", group))

    return aggregate_rows


def summarize_group(method: str, group_label: str, rows: list[dict]) -> dict:
    no_warmup = [row for row in rows if not row["is_first_prompt"]]
    elapsed = [float(row["elapsed_seconds"]) for row in rows]
    elapsed_no_warmup = [float(row["elapsed_seconds"]) for row in no_warmup]
    peak_vram = [float(row["peak_vram_gb"]) for row in rows if row["peak_vram_gb"] is not None]
    steps = int(rows[0]["steps"])
    actual_words = [int(row["actual_words"]) for row in rows if row["actual_words"] != ""]
    return {
        "method": method,
        "steps": steps,
        "prompt_length_group": group_label,
        "num_prompts": len(rows),
        "avg_words": mean(actual_words) if actual_words else "",
        "avg_elapsed_seconds": mean(elapsed),
        "avg_elapsed_seconds_no_warmup": mean(elapsed_no_warmup) if elapsed_no_warmup else "",
        "max_elapsed_seconds": max(elapsed),
        "avg_peak_vram_gb": mean(peak_vram) if peak_vram else "",
        "avg_steps": steps,
    }


def format_float(value: object) -> str:
    if value == "":
        return ""
    return f"{float(value):.3f}"


def write_markdown(path: Path, aggregate_rows: list[dict]) -> None:
    order = {"all": 0, "10_words": 1, "30_words": 2, "50_words": 3}
    rows = sorted(aggregate_rows, key=lambda row: (int(row["steps"]), order.get(row["prompt_length_group"], 99)))
    lines = [
        "# Day 2 Fixed-Step Baseline Speed Summary",
        "",
        "Model: `Efficient-Large-Model/Sana_600M_512px_diffusers` at 512x512.",
        "",
        "Prompt benchmark: 10 prompts with 10 words, 10 prompts with 30 words, and 10 prompts with 50 words.",
        "",
        "The no-warmup column excludes the first prompt of each fixed-step run, because it includes extra CUDA/runtime warm-up noise.",
        "",
        "| Method | Prompt group | Prompts | Avg words | Avg time (s) | Avg time no-warmup (s) | Max time (s) | Avg peak VRAM (GB) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {method} | {group} | {num_prompts} | {avg_words} | {avg} | {avg_no_warmup} | {max_time} | {vram} |".format(
                method=row["method"],
                group=row["prompt_length_group"],
                num_prompts=row["num_prompts"],
                avg_words=format_float(row["avg_words"]),
                avg=format_float(row["avg_elapsed_seconds"]),
                avg_no_warmup=format_float(row["avg_elapsed_seconds_no_warmup"]),
                max_time=format_float(row["max_elapsed_seconds"]),
                vram=format_float(row["avg_peak_vram_gb"]),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Day 2 fixed-step SANA baseline results.")
    parser.add_argument("--outputs-dir", default="outputs")
    parser.add_argument("--prompts-dir", default="prompts")
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()

    outputs_dir = Path(args.outputs_dir)
    prompts_dir = Path(args.prompts_dir)
    results_dir = Path(args.results_dir)

    prompt_groups = read_prompt_groups(prompts_dir)
    rows = load_records(outputs_dir, prompt_groups)
    if not rows:
        raise RuntimeError("No Day 2 baseline summary files were found.")

    detail_fields = [
        "method",
        "steps",
        "prompt_index",
        "prompt_length_group",
        "target_words",
        "actual_words",
        "prompt",
        "height",
        "width",
        "guidance_scale",
        "seed",
        "elapsed_seconds",
        "peak_vram_gb",
        "image_path",
        "is_first_prompt",
    ]
    write_csv(results_dir / "day2_speed_results.csv", rows, detail_fields)

    aggregate_rows = aggregate(rows)
    aggregate_fields = [
        "method",
        "steps",
        "prompt_length_group",
        "num_prompts",
        "avg_words",
        "avg_elapsed_seconds",
        "avg_elapsed_seconds_no_warmup",
        "max_elapsed_seconds",
        "avg_peak_vram_gb",
        "avg_steps",
    ]
    write_csv(results_dir / "day2_speed_summary.csv", aggregate_rows, aggregate_fields)
    write_markdown(results_dir / "day2_speed_summary.md", aggregate_rows)
    print(f"Wrote {results_dir / 'day2_speed_results.csv'}")
    print(f"Wrote {results_dir / 'day2_speed_summary.csv'}")
    print(f"Wrote {results_dir / 'day2_speed_summary.md'}")


if __name__ == "__main__":
    main()
