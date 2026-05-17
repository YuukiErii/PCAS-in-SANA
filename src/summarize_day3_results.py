from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


GROUP_LABELS = {
    "short": "10_words",
    "medium": "30_words",
    "long": "50_words",
}


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_fixed_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["steps"] = int(row["steps"])
        row["prompt_index"] = int(row["prompt_index"])
        row["actual_words"] = int(row["actual_words"])
        row["elapsed_seconds"] = float(row["elapsed_seconds"])
        row["peak_vram_gb"] = float(row["peak_vram_gb"])
        row["is_first_prompt"] = row["is_first_prompt"].lower() == "true"
        row["selected_guidance_scale"] = float(row["guidance_scale"])
        row["selected_steps"] = row["steps"]
    return rows


def load_pcas_rows(path: Path) -> list[dict]:
    records = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for index, record in enumerate(records, start=1):
        rows.append(
            {
                "method": "pcas",
                "steps": int(record["selected_steps"]),
                "prompt_index": index,
                "prompt_length_group": GROUP_LABELS[record["complexity_label"]],
                "actual_words": int(record["word_count"]),
                "prompt": record["prompt"],
                "height": int(record["selected_height"]),
                "width": int(record["selected_width"]),
                "guidance_scale": float(record["selected_guidance_scale"]),
                "selected_guidance_scale": float(record["selected_guidance_scale"]),
                "selected_steps": int(record["selected_steps"]),
                "complexity_score": float(record["complexity_score"]),
                "complexity_label": record["complexity_label"],
                "relation_count": int(record["relation_count"]),
                "style_count": int(record["style_count"]),
                "text_rendering": bool(record["text_rendering"]),
                "seed": int(record["seed"]),
                "elapsed_seconds": float(record["elapsed_seconds"]),
                "peak_vram_gb": float(record["peak_vram_gb"]),
                "image_path": record["image_path"],
                "is_first_prompt": index == 1,
            }
        )
    return rows


def summarize(rows: list[dict], method: str, group_label: str) -> dict:
    no_warmup = [row for row in rows if not row["is_first_prompt"]]
    elapsed = [row["elapsed_seconds"] for row in rows]
    elapsed_no_warmup = [row["elapsed_seconds"] for row in no_warmup]
    return {
        "method": method,
        "prompt_length_group": group_label,
        "num_prompts": len(rows),
        "avg_words": mean(row["actual_words"] for row in rows),
        "avg_steps": mean(row["selected_steps"] for row in rows),
        "avg_guidance_scale": mean(row["selected_guidance_scale"] for row in rows),
        "avg_elapsed_seconds": mean(elapsed),
        "avg_elapsed_seconds_no_warmup": mean(elapsed_no_warmup) if elapsed_no_warmup else "",
        "max_elapsed_seconds": max(elapsed),
        "avg_peak_vram_gb": mean(row["peak_vram_gb"] for row in rows),
    }


def aggregate(rows: list[dict]) -> list[dict]:
    result: list[dict] = []
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["method"], row["prompt_length_group"])].append(row)
    for (method, group_label), group_rows in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        result.append(summarize(group_rows, method, group_label))
    for method in sorted({row["method"] for row in rows}):
        method_rows = [row for row in rows if row["method"] == method]
        result.append(summarize(method_rows, method, "all"))
    return result


def by_key(summary_rows: list[dict]) -> dict[tuple[str, str], dict]:
    return {(row["method"], row["prompt_length_group"]): row for row in summary_rows}


def safe_pct(numerator: float, denominator: float) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


def build_comparisons(summary_rows: list[dict]) -> list[dict]:
    index = by_key(summary_rows)
    comparisons: list[dict] = []
    for group_label in ("all", "10_words", "30_words", "50_words"):
        pcas = index[("pcas", group_label)]
        fixed20 = index[("fixed_20", group_label)]
        time_delta = float(fixed20["avg_elapsed_seconds_no_warmup"]) - float(pcas["avg_elapsed_seconds_no_warmup"])
        step_delta = float(fixed20["avg_steps"]) - float(pcas["avg_steps"])
        comparisons.append(
            {
                "group": group_label,
                "pcas_avg_steps": pcas["avg_steps"],
                "fixed20_avg_steps": fixed20["avg_steps"],
                "step_saving_percent_vs_fixed20": safe_pct(step_delta, float(fixed20["avg_steps"])),
                "pcas_time_no_warmup": pcas["avg_elapsed_seconds_no_warmup"],
                "fixed20_time_no_warmup": fixed20["avg_elapsed_seconds_no_warmup"],
                "time_saving_seconds_vs_fixed20": time_delta,
                "time_saving_percent_vs_fixed20": safe_pct(time_delta, float(fixed20["avg_elapsed_seconds_no_warmup"])),
            }
        )
    return comparisons


def format_float(value: object) -> str:
    if value == "":
        return ""
    return f"{float(value):.3f}"


def write_markdown(path: Path, summary_rows: list[dict], comparisons: list[dict]) -> None:
    order = {"all": 0, "10_words": 1, "30_words": 2, "50_words": 3}
    methods = {"fixed_10": 0, "fixed_20": 1, "fixed_28": 2, "pcas": 3}
    rows = sorted(summary_rows, key=lambda row: (methods.get(row["method"], 99), order.get(row["prompt_length_group"], 99)))

    lines = [
        "# Day 3 PCAS Summary",
        "",
        "PCAS policy: short prompts use 10 steps and guidance 4.0, medium prompts use 20 steps and guidance 4.5, long prompts use 28 steps and guidance 5.0. Resolution is fixed at 512x512 for this first comparison.",
        "",
        "The no-warmup column excludes the first prompt of each run.",
        "",
        "| Method | Prompt group | Prompts | Avg steps | Avg guidance | Avg time no-warmup (s) | Avg peak VRAM (GB) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {method} | {group} | {num_prompts} | {avg_steps} | {avg_guidance} | {avg_time} | {vram} |".format(
                method=row["method"],
                group=row["prompt_length_group"],
                num_prompts=row["num_prompts"],
                avg_steps=format_float(row["avg_steps"]),
                avg_guidance=format_float(row["avg_guidance_scale"]),
                avg_time=format_float(row["avg_elapsed_seconds_no_warmup"]),
                vram=format_float(row["avg_peak_vram_gb"]),
            )
        )

    lines.extend(
        [
            "",
            "## PCAS vs Fixed-20",
            "",
            "| Prompt group | PCAS steps | Fixed-20 steps | Step saving | PCAS time (s) | Fixed-20 time (s) | Time saving |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in comparisons:
        lines.append(
            "| {group} | {pcas_steps} | {fixed_steps} | {step_pct}% | {pcas_time} | {fixed_time} | {time_pct}% |".format(
                group=row["group"],
                pcas_steps=format_float(row["pcas_avg_steps"]),
                fixed_steps=format_float(row["fixed20_avg_steps"]),
                step_pct=format_float(row["step_saving_percent_vs_fixed20"]),
                pcas_time=format_float(row["pcas_time_no_warmup"]),
                fixed_time=format_float(row["fixed20_time_no_warmup"]),
                time_pct=format_float(row["time_saving_percent_vs_fixed20"]),
            )
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Day 3 PCAS results against Day 2 fixed baselines.")
    parser.add_argument("--day2-results", default="results/day2_speed_results.csv")
    parser.add_argument("--pcas-summary", default="outputs/day3_pcas/summary.json")
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()

    fixed_rows = load_fixed_rows(Path(args.day2_results))
    pcas_rows = load_pcas_rows(Path(args.pcas_summary))
    all_rows = fixed_rows + pcas_rows
    summary_rows = aggregate(all_rows)
    comparisons = build_comparisons(summary_rows)

    results_dir = Path(args.results_dir)
    detail_fields = [
        "method",
        "steps",
        "prompt_index",
        "prompt_length_group",
        "actual_words",
        "prompt",
        "height",
        "width",
        "guidance_scale",
        "selected_steps",
        "selected_guidance_scale",
        "elapsed_seconds",
        "peak_vram_gb",
        "image_path",
        "is_first_prompt",
    ]
    normalized_rows = [{field: row.get(field, "") for field in detail_fields} for row in all_rows]
    write_csv(results_dir / "day3_pcas_results.csv", normalized_rows, detail_fields)

    summary_fields = [
        "method",
        "prompt_length_group",
        "num_prompts",
        "avg_words",
        "avg_steps",
        "avg_guidance_scale",
        "avg_elapsed_seconds",
        "avg_elapsed_seconds_no_warmup",
        "max_elapsed_seconds",
        "avg_peak_vram_gb",
    ]
    write_csv(results_dir / "day3_pcas_summary.csv", summary_rows, summary_fields)

    comparison_fields = [
        "group",
        "pcas_avg_steps",
        "fixed20_avg_steps",
        "step_saving_percent_vs_fixed20",
        "pcas_time_no_warmup",
        "fixed20_time_no_warmup",
        "time_saving_seconds_vs_fixed20",
        "time_saving_percent_vs_fixed20",
    ]
    write_csv(results_dir / "day3_pcas_vs_fixed20.csv", comparisons, comparison_fields)
    write_markdown(results_dir / "day3_pcas_summary.md", summary_rows, comparisons)

    print(f"Wrote {results_dir / 'day3_pcas_results.csv'}")
    print(f"Wrote {results_dir / 'day3_pcas_summary.csv'}")
    print(f"Wrote {results_dir / 'day3_pcas_vs_fixed20.csv'}")
    print(f"Wrote {results_dir / 'day3_pcas_summary.md'}")


if __name__ == "__main__":
    main()
