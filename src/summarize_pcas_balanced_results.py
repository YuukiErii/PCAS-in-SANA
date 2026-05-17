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


def load_fixed20_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["method"] == "fixed_20"]
    for row in rows:
        row["method"] = "fixed_20"
        row["prompt_index"] = int(row["prompt_index"])
        row["prompt_length_group"] = row["prompt_length_group"]
        row["actual_words"] = int(row["actual_words"])
        row["selected_steps"] = int(row["steps"])
        row["selected_guidance_scale"] = float(row["guidance_scale"])
        row["elapsed_seconds"] = float(row["elapsed_seconds"])
        row["peak_vram_gb"] = float(row["peak_vram_gb"])
        row["is_first_prompt"] = row["is_first_prompt"].lower() == "true"
    return rows


def load_pcas_rows(path: Path, method: str) -> list[dict]:
    records = json.loads(path.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for index, record in enumerate(records, start=1):
        rows.append(
            {
                "method": method,
                "prompt_index": index,
                "prompt_length_group": GROUP_LABELS[record["complexity_label"]],
                "actual_words": int(record["word_count"]),
                "prompt": record["prompt"],
                "selected_steps": int(record["selected_steps"]),
                "selected_guidance_scale": float(record["selected_guidance_scale"]),
                "elapsed_seconds": float(record["elapsed_seconds"]),
                "peak_vram_gb": float(record["peak_vram_gb"]),
                "image_path": record["image_path"],
                "is_first_prompt": index == 1,
            }
        )
    return rows


def summarize_group(rows: list[dict], method: str, group: str) -> dict:
    no_warmup = [row for row in rows if not row["is_first_prompt"]]
    return {
        "method": method,
        "prompt_length_group": group,
        "num_prompts": len(rows),
        "avg_words": mean(row["actual_words"] for row in rows),
        "avg_steps": mean(row["selected_steps"] for row in rows),
        "avg_guidance_scale": mean(row["selected_guidance_scale"] for row in rows),
        "avg_elapsed_seconds": mean(row["elapsed_seconds"] for row in rows),
        "avg_elapsed_seconds_no_warmup": mean(row["elapsed_seconds"] for row in no_warmup) if no_warmup else "",
        "max_elapsed_seconds": max(row["elapsed_seconds"] for row in rows),
        "avg_peak_vram_gb": mean(row["peak_vram_gb"] for row in rows),
    }


def aggregate(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["method"], row["prompt_length_group"])].append(row)

    method_order = {"fixed_20": 0, "rule_pcas_7_2": 1, "balanced_pcas": 2}
    group_order = {"all": 0, "10_words": 1, "30_words": 2, "50_words": 3}
    result: list[dict] = []
    for method in sorted({row["method"] for row in rows}, key=lambda name: method_order.get(name, 99)):
        method_rows = [row for row in rows if row["method"] == method]
        result.append(summarize_group(method_rows, method, "all"))
        for group in ("10_words", "30_words", "50_words"):
            group_rows = grouped[(method, group)]
            result.append(summarize_group(group_rows, method, group))
    return sorted(result, key=lambda row: (method_order.get(row["method"], 99), group_order[row["prompt_length_group"]]))


def compare_to_fixed20(summary_rows: list[dict]) -> list[dict]:
    index = {(row["method"], row["prompt_length_group"]): row for row in summary_rows}
    comparisons: list[dict] = []
    for method in ("rule_pcas_7_2", "balanced_pcas"):
        for group in ("all", "10_words", "30_words", "50_words"):
            candidate = index[(method, group)]
            fixed = index[("fixed_20", group)]
            fixed_time = float(fixed["avg_elapsed_seconds_no_warmup"])
            candidate_time = float(candidate["avg_elapsed_seconds_no_warmup"])
            fixed_steps = float(fixed["avg_steps"])
            candidate_steps = float(candidate["avg_steps"])
            comparisons.append(
                {
                    "method": method,
                    "prompt_length_group": group,
                    "avg_steps": candidate_steps,
                    "fixed20_avg_steps": fixed_steps,
                    "step_saving_percent_vs_fixed20": 100.0 * (fixed_steps - candidate_steps) / fixed_steps,
                    "avg_time_no_warmup": candidate_time,
                    "fixed20_time_no_warmup": fixed_time,
                    "time_saving_seconds_vs_fixed20": fixed_time - candidate_time,
                    "time_saving_percent_vs_fixed20": 100.0 * (fixed_time - candidate_time) / fixed_time,
                }
            )
    return comparisons


def fmt(value: object) -> str:
    if value == "":
        return ""
    return f"{float(value):.3f}"


def write_markdown(path: Path, summary_rows: list[dict], comparisons: list[dict]) -> None:
    lines = [
        "# Balanced-PCAS Speed Summary",
        "",
        "Balanced-PCAS is introduced to solve the small overall speed gain of the original Rule-PCAS. It uses a fixed average-step budget below Fixed-20: short prompts use 8 steps, medium prompts use 16 steps, and long prompts use 24 steps.",
        "",
        "| Method | Group | Prompts | Avg steps | Avg guidance | Avg time no-warmup (s) | Avg peak VRAM (GB) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
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
    for row in comparisons:
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
            "- The original Rule-PCAS mainly reallocates compute: it saves time on short prompts but spends extra time on long prompts, so the balanced 10/30/50 benchmark has only a small overall speed gain.",
            "- Balanced-PCAS constrains every group below Fixed-20, so its overall speed gain is much larger and easier to report as an efficiency-oriented PCAS variant.",
            "- The trade-off is that long prompts now receive 24 rather than 28 steps, so this variant should be framed as efficiency-first. A follow-up quality check is needed before replacing the original PCAS in the main quality discussion.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize Balanced-PCAS against Fixed-20 and original Rule-PCAS.")
    parser.add_argument("--day2-results", default="results/day2_speed_results.csv")
    parser.add_argument("--rule-pcas-summary", default="outputs/day3_pcas/summary.json")
    parser.add_argument("--balanced-pcas-summary", default="outputs/day3_pcas_balanced/summary.json")
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()

    rows = []
    rows.extend(load_fixed20_rows(Path(args.day2_results)))
    rows.extend(load_pcas_rows(Path(args.rule_pcas_summary), "rule_pcas_7_2"))
    rows.extend(load_pcas_rows(Path(args.balanced_pcas_summary), "balanced_pcas"))

    summary_rows = aggregate(rows)
    comparison_rows = compare_to_fixed20(summary_rows)
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
    write_csv(results_dir / "day3_pcas_balanced_summary.csv", summary_rows, summary_fields)
    write_csv(results_dir / "day3_pcas_balanced_vs_fixed20.csv", comparison_rows, comparison_fields)
    write_markdown(results_dir / "day3_pcas_balanced_summary.md", summary_rows, comparison_rows)
    print("Wrote Balanced-PCAS summary files.")


if __name__ == "__main__":
    main()
