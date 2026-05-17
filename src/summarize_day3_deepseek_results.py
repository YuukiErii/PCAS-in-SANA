from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
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


def load_fixed_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    normalized = []
    for row in rows:
        normalized.append(
            {
                "method": row["method"],
                "prompt_index": int(row["prompt_index"]),
                "prompt_length_group": row["prompt_length_group"],
                "actual_words": int(row["actual_words"]),
                "prompt": row["prompt"],
                "selected_steps": int(row["steps"]),
                "selected_guidance_scale": float(row["guidance_scale"]),
                "complexity": "",
                "complexity_score": "",
                "source": "fixed_baseline",
                "elapsed_seconds": float(row["elapsed_seconds"]),
                "peak_vram_gb": float(row["peak_vram_gb"]),
                "image_path": row["image_path"],
                "is_first_prompt": row["is_first_prompt"].lower() == "true",
            }
        )
    return normalized


def load_rule_pcas_rows(path: Path) -> list[dict]:
    records = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for index, record in enumerate(records, start=1):
        rows.append(
            {
                "method": "rule_pcas_7_2",
                "prompt_index": index,
                "prompt_length_group": prompt_group_from_words(int(record["word_count"])),
                "actual_words": int(record["word_count"]),
                "prompt": record["prompt"],
                "selected_steps": int(record["selected_steps"]),
                "selected_guidance_scale": float(record["selected_guidance_scale"]),
                "complexity": record["complexity_label"],
                "complexity_score": float(record["complexity_score"]),
                "source": "rule_based",
                "elapsed_seconds": float(record["elapsed_seconds"]),
                "peak_vram_gb": float(record["peak_vram_gb"]),
                "image_path": record["image_path"],
                "is_first_prompt": index == 1,
            }
        )
    return rows


def load_deepseek_pcas_rows(path: Path) -> list[dict]:
    records = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for index, record in enumerate(records, start=1):
        rows.append(
            {
                "method": "deepseek_pcas_7_3",
                "prompt_index": index,
                "prompt_length_group": prompt_group_from_words(int(record["word_count"])),
                "actual_words": int(record["word_count"]),
                "prompt": record["prompt"],
                "selected_steps": int(record["selected_steps"]),
                "selected_guidance_scale": float(record["selected_guidance_scale"]),
                "complexity": record["complexity"],
                "complexity_score": float(record["complexity_score"]),
                "source": record["source"],
                "elapsed_seconds": float(record["elapsed_seconds"]),
                "peak_vram_gb": float(record["peak_vram_gb"]),
                "image_path": record["image_path"],
                "is_first_prompt": index == 1,
            }
        )
    return rows


def summarize(rows: list[dict], method: str, group: str) -> dict:
    no_warmup = [row for row in rows if not row["is_first_prompt"]]
    elapsed = [row["elapsed_seconds"] for row in rows]
    elapsed_no_warmup = [row["elapsed_seconds"] for row in no_warmup]
    return {
        "method": method,
        "prompt_length_group": group,
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
    result = []
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["method"], row["prompt_length_group"])].append(row)
    for (method, group), group_rows in sorted(grouped.items()):
        result.append(summarize(group_rows, method, group))
    for method in sorted({row["method"] for row in rows}):
        result.append(summarize([row for row in rows if row["method"] == method], method, "all"))
    return result


def build_index(rows: list[dict]) -> dict[tuple[str, str], dict]:
    return {(row["method"], row["prompt_length_group"]): row for row in rows}


def pct(delta: float, base: float) -> float:
    return 100.0 * delta / base if base else 0.0


def compare_methods(summary_rows: list[dict], reference: str = "fixed_20") -> list[dict]:
    index = build_index(summary_rows)
    rows = []
    for method in ("rule_pcas_7_2", "deepseek_pcas_7_3"):
        for group in ("all", "10_words", "30_words", "50_words"):
            current = index[(method, group)]
            ref = index[(reference, group)]
            time_delta = float(ref["avg_elapsed_seconds_no_warmup"]) - float(current["avg_elapsed_seconds_no_warmup"])
            step_delta = float(ref["avg_steps"]) - float(current["avg_steps"])
            rows.append(
                {
                    "method": method,
                    "reference": reference,
                    "prompt_length_group": group,
                    "method_avg_steps": current["avg_steps"],
                    "reference_avg_steps": ref["avg_steps"],
                    "step_saving_percent": pct(step_delta, float(ref["avg_steps"])),
                    "method_time_no_warmup": current["avg_elapsed_seconds_no_warmup"],
                    "reference_time_no_warmup": ref["avg_elapsed_seconds_no_warmup"],
                    "time_saving_seconds": time_delta,
                    "time_saving_percent": pct(time_delta, float(ref["avg_elapsed_seconds_no_warmup"])),
                }
            )
    return rows


def format_float(value: object) -> str:
    if value == "":
        return ""
    return f"{float(value):.3f}"


def write_markdown(path: Path, summary_rows: list[dict], comparisons: list[dict]) -> None:
    group_order = {"all": 0, "10_words": 1, "30_words": 2, "50_words": 3}
    method_order = {
        "fixed_10": 0,
        "fixed_20": 1,
        "fixed_28": 2,
        "rule_pcas_7_2": 3,
        "deepseek_pcas_7_3": 4,
    }
    rows = sorted(summary_rows, key=lambda row: (method_order[row["method"]], group_order[row["prompt_length_group"]]))
    lines = [
        "# Day 3 DeepSeek-PCAS Summary",
        "",
        "This extends Section 7.2 rule-based PCAS with a Section 7.3 DeepSeek-assisted semantic prompt analyzer.",
        "",
        "| Method | Prompt group | Prompts | Avg steps | Avg guidance | Avg time no-warmup (s) | Avg peak VRAM (GB) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {method} | {group} | {num_prompts} | {steps} | {guidance} | {time} | {vram} |".format(
                method=row["method"],
                group=row["prompt_length_group"],
                num_prompts=row["num_prompts"],
                steps=format_float(row["avg_steps"]),
                guidance=format_float(row["avg_guidance_scale"]),
                time=format_float(row["avg_elapsed_seconds_no_warmup"]),
                vram=format_float(row["avg_peak_vram_gb"]),
            )
        )

    lines.extend(
        [
            "",
            "## PCAS Methods vs Fixed-20",
            "",
            "| Method | Group | Avg steps | Fixed-20 steps | Step saving | Avg time (s) | Fixed-20 time (s) | Time saving |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    comp_order = {"rule_pcas_7_2": 0, "deepseek_pcas_7_3": 1}
    for row in sorted(comparisons, key=lambda row: (comp_order[row["method"]], group_order[row["prompt_length_group"]])):
        lines.append(
            "| {method} | {group} | {steps} | {ref_steps} | {step_pct}% | {time} | {ref_time} | {time_pct}% |".format(
                method=row["method"],
                group=row["prompt_length_group"],
                steps=format_float(row["method_avg_steps"]),
                ref_steps=format_float(row["reference_avg_steps"]),
                step_pct=format_float(row["step_saving_percent"]),
                time=format_float(row["method_time_no_warmup"]),
                ref_time=format_float(row["reference_time_no_warmup"]),
                time_pct=format_float(row["time_saving_percent"]),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Section 7.2 rule PCAS and Section 7.3 DeepSeek PCAS.")
    parser.add_argument("--day2-results", default="results/day2_speed_results.csv")
    parser.add_argument("--rule-pcas-summary", default="outputs/day3_pcas/summary.json")
    parser.add_argument("--deepseek-pcas-summary", default="outputs/day3_pcas_deepseek/summary.json")
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()

    fixed_rows = load_fixed_rows(Path(args.day2_results))
    rule_rows = load_rule_pcas_rows(Path(args.rule_pcas_summary))
    deepseek_rows = load_deepseek_pcas_rows(Path(args.deepseek_pcas_summary))
    all_rows = fixed_rows + rule_rows + deepseek_rows
    summary_rows = aggregate(all_rows)
    comparison_rows = compare_methods(summary_rows)

    results_dir = Path(args.results_dir)
    detail_fields = [
        "method",
        "prompt_index",
        "prompt_length_group",
        "actual_words",
        "prompt",
        "selected_steps",
        "selected_guidance_scale",
        "complexity",
        "complexity_score",
        "source",
        "elapsed_seconds",
        "peak_vram_gb",
        "image_path",
        "is_first_prompt",
    ]
    write_csv(results_dir / "day3_7_2_7_3_results.csv", all_rows, detail_fields)
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
    write_csv(results_dir / "day3_7_2_7_3_summary.csv", summary_rows, summary_fields)
    comparison_fields = [
        "method",
        "reference",
        "prompt_length_group",
        "method_avg_steps",
        "reference_avg_steps",
        "step_saving_percent",
        "method_time_no_warmup",
        "reference_time_no_warmup",
        "time_saving_seconds",
        "time_saving_percent",
    ]
    write_csv(results_dir / "day3_7_2_7_3_vs_fixed20.csv", comparison_rows, comparison_fields)
    write_markdown(results_dir / "day3_deepseek_pcas_summary.md", summary_rows, comparison_rows)

    print(f"Wrote {results_dir / 'day3_7_2_7_3_results.csv'}")
    print(f"Wrote {results_dir / 'day3_7_2_7_3_summary.csv'}")
    print(f"Wrote {results_dir / 'day3_7_2_7_3_vs_fixed20.csv'}")
    print(f"Wrote {results_dir / 'day3_deepseek_pcas_summary.md'}")


if __name__ == "__main__":
    main()
