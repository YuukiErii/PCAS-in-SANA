from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


def prompt_group_from_words(word_count: int) -> str:
    if word_count <= 20:
        return "10_words"
    if word_count <= 40:
        return "30_words"
    return "50_words"


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_fixed20_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["method"] == "fixed_20"]
    normalized: list[dict] = []
    for row in rows:
        normalized.append(
            {
                "method": "fixed_20",
                "prompt_index": int(row["prompt_index"]),
                "prompt_length_group": row["prompt_length_group"],
                "actual_words": int(row["actual_words"]),
                "prompt": row["prompt"],
                "selected_steps": int(row["steps"]),
                "selected_guidance_scale": float(row["guidance_scale"]),
                "complexity": "",
                "source": "fixed_baseline",
                "elapsed_seconds": float(row["elapsed_seconds"]),
                "peak_vram_gb": float(row["peak_vram_gb"]),
                "image_path": row["image_path"],
                "is_first_prompt": row["is_first_prompt"].lower() == "true",
            }
        )
    return normalized


def load_deepseek_rows(path: Path, method: str) -> list[dict]:
    records = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for index, record in enumerate(records, start=1):
        rows.append(
            {
                "method": method,
                "prompt_index": index,
                "prompt_length_group": prompt_group_from_words(int(record["word_count"])),
                "actual_words": int(record["word_count"]),
                "prompt": record["prompt"],
                "selected_steps": int(record["selected_steps"]),
                "selected_guidance_scale": float(record["selected_guidance_scale"]),
                "complexity": record["complexity"],
                "source": record["source"],
                "elapsed_seconds": float(record["elapsed_seconds"]),
                "peak_vram_gb": float(record["peak_vram_gb"]),
                "image_path": record["image_path"],
                "is_first_prompt": index == 1,
            }
        )
    return rows


def summarize_group(rows: list[dict], method: str, group: str) -> dict:
    no_warmup = [row for row in rows if not row["is_first_prompt"]]
    elapsed_source = no_warmup if no_warmup else rows
    return {
        "method": method,
        "prompt_length_group": group,
        "num_prompts": len(rows),
        "avg_words": mean(row["actual_words"] for row in rows),
        "avg_steps": mean(row["selected_steps"] for row in rows),
        "avg_guidance_scale": mean(row["selected_guidance_scale"] for row in rows),
        "avg_elapsed_seconds": mean(row["elapsed_seconds"] for row in rows),
        "avg_elapsed_seconds_no_warmup": mean(row["elapsed_seconds"] for row in elapsed_source),
        "max_elapsed_seconds": max(row["elapsed_seconds"] for row in rows),
        "avg_peak_vram_gb": mean(row["peak_vram_gb"] for row in rows),
    }


def aggregate(rows: list[dict]) -> list[dict]:
    method_order = {"fixed_20": 0, "deepseek_pcas_7_3": 1, "deepseek_balanced_pcas": 2}
    group_order = {"all": 0, "10_words": 1, "30_words": 2, "50_words": 3}
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["method"], row["prompt_length_group"])].append(row)

    summary: list[dict] = []
    for method in sorted({row["method"] for row in rows}, key=lambda value: method_order[value]):
        method_rows = [row for row in rows if row["method"] == method]
        summary.append(summarize_group(method_rows, method, "all"))
        for group in ("10_words", "30_words", "50_words"):
            summary.append(summarize_group(grouped[(method, group)], method, group))
    return sorted(summary, key=lambda row: (method_order[row["method"]], group_order[row["prompt_length_group"]]))


def compare(summary_rows: list[dict]) -> list[dict]:
    index = {(row["method"], row["prompt_length_group"]): row for row in summary_rows}
    rows: list[dict] = []
    for method in ("deepseek_pcas_7_3", "deepseek_balanced_pcas"):
        for group in ("all", "10_words", "30_words", "50_words"):
            current = index[(method, group)]
            fixed = index[("fixed_20", group)]
            current_steps = float(current["avg_steps"])
            fixed_steps = float(fixed["avg_steps"])
            current_time = float(current["avg_elapsed_seconds_no_warmup"])
            fixed_time = float(fixed["avg_elapsed_seconds_no_warmup"])
            rows.append(
                {
                    "method": method,
                    "prompt_length_group": group,
                    "avg_steps": current_steps,
                    "fixed20_avg_steps": fixed_steps,
                    "step_saving_percent_vs_fixed20": 100.0 * (fixed_steps - current_steps) / fixed_steps,
                    "avg_time_no_warmup": current_time,
                    "fixed20_time_no_warmup": fixed_time,
                    "time_saving_seconds_vs_fixed20": fixed_time - current_time,
                    "time_saving_percent_vs_fixed20": 100.0 * (fixed_time - current_time) / fixed_time,
                }
            )
    return rows


def complexity_counts(rows: list[dict]) -> list[dict]:
    result: list[dict] = []
    for method in ("deepseek_pcas_7_3", "deepseek_balanced_pcas"):
        counts = Counter(row["complexity"] for row in rows if row["method"] == method)
        for label in ("low", "medium", "high"):
            result.append({"method": method, "complexity": label, "count": counts[label]})
    return result


def fmt(value: object) -> str:
    return f"{float(value):.3f}"


def write_markdown(path: Path, summary_rows: list[dict], comparison_rows: list[dict], count_rows: list[dict]) -> None:
    lines = [
        "# DeepSeek-Balanced PCAS Summary",
        "",
        "DeepSeek-Balanced PCAS keeps the same cached DeepSeek semantic complexity labels, but applies a budget-constrained policy: low=8 steps, medium=16 steps, high=22 steps. This addresses the original DeepSeek-PCAS being too conservative and slower than Fixed-20.",
        "",
        "## DeepSeek Label Counts",
        "",
        "| Method | Low | Medium | High |",
        "| --- | ---: | ---: | ---: |",
    ]
    for method in ("deepseek_pcas_7_3", "deepseek_balanced_pcas"):
        row = {item["complexity"]: item["count"] for item in count_rows if item["method"] == method}
        lines.append(f"| {method} | {row.get('low', 0)} | {row.get('medium', 0)} | {row.get('high', 0)} |")

    lines.extend(
        [
            "",
            "## Speed Summary",
            "",
            "| Method | Group | Prompts | Avg steps | Avg guidance | Avg time no-warmup (s) | Avg peak VRAM (GB) |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary_rows:
        lines.append(
            "| {method} | {group} | {n} | {steps} | {guidance} | {time} | {vram} |".format(
                method=row["method"],
                group=row["prompt_length_group"],
                n=row["num_prompts"],
                steps=fmt(row["avg_steps"]),
                guidance=fmt(row["avg_guidance_scale"]),
                time=fmt(row["avg_elapsed_seconds_no_warmup"]),
                vram=fmt(row["avg_peak_vram_gb"]),
            )
        )

    lines.extend(
        [
            "",
            "## Compared With Fixed-20",
            "",
            "| Method | Group | Avg steps | Step saving | Avg time (s) | Time saving |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in comparison_rows:
        lines.append(
            "| {method} | {group} | {steps} | {step_pct}% | {time} | {time_pct}% |".format(
                method=row["method"],
                group=row["prompt_length_group"],
                steps=fmt(row["avg_steps"]),
                step_pct=fmt(row["step_saving_percent_vs_fixed20"]),
                time=fmt(row["avg_time_no_warmup"]),
                time_pct=fmt(row["time_saving_percent_vs_fixed20"]),
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The original DeepSeek-PCAS is semantically useful but too conservative: because 19 of 30 prompts are labeled high, its 28-step high policy makes it slower than Fixed-20.",
            "- DeepSeek-Balanced keeps the same semantic labels but lowers the action taken for each label, especially high prompts.",
            "- This turns DeepSeek from a quality-conservative strategy into a budget-constrained semantic scheduler.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize DeepSeek-Balanced PCAS.")
    parser.add_argument("--day2-results", default="results/day2_speed_results.csv")
    parser.add_argument("--deepseek-summary", default="outputs/day3_pcas_deepseek/summary.json")
    parser.add_argument("--deepseek-balanced-summary", default="outputs/day3_pcas_deepseek_balanced/summary.json")
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()

    rows: list[dict] = []
    rows.extend(load_fixed20_rows(Path(args.day2_results)))
    rows.extend(load_deepseek_rows(Path(args.deepseek_summary), "deepseek_pcas_7_3"))
    rows.extend(load_deepseek_rows(Path(args.deepseek_balanced_summary), "deepseek_balanced_pcas"))

    summary_rows = aggregate(rows)
    comparison_rows = compare(summary_rows)
    count_rows = complexity_counts(rows)
    results_dir = Path(args.results_dir)

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
    comparison_fields = [
        "method",
        "prompt_length_group",
        "avg_steps",
        "fixed20_avg_steps",
        "step_saving_percent_vs_fixed20",
        "avg_time_no_warmup",
        "fixed20_time_no_warmup",
        "time_saving_seconds_vs_fixed20",
        "time_saving_percent_vs_fixed20",
    ]
    count_fields = ["method", "complexity", "count"]

    write_csv(results_dir / "day3_deepseek_balanced_summary.csv", summary_rows, summary_fields)
    write_csv(results_dir / "day3_deepseek_balanced_vs_fixed20.csv", comparison_rows, comparison_fields)
    write_csv(results_dir / "day3_deepseek_balanced_complexity_counts.csv", count_rows, count_fields)
    write_markdown(results_dir / "day3_deepseek_balanced_summary.md", summary_rows, comparison_rows, count_rows)
    print("Wrote DeepSeek-Balanced summary files.")


if __name__ == "__main__":
    main()
