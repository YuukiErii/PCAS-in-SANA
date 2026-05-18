from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


DEFAULT_FEATURE_COLUMNS = [
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


def parse_feature_columns(value: str | None) -> list[str]:
    if not value:
        return list(DEFAULT_FEATURE_COLUMNS)
    return [column.strip() for column in value.split(",") if column.strip()]


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def merge_feature_file(labels: list[dict[str, Any]], feature_file: Path | None) -> list[dict[str, Any]]:
    if feature_file is None:
        return labels
    feature_rows = read_csv(feature_file)
    by_prompt = {row["prompt"]: row for row in feature_rows}
    merged: list[dict[str, Any]] = []
    for label in labels:
        row = dict(label)
        extra = by_prompt.get(label["prompt"])
        if extra is None:
            raise ValueError(f"No feature row found for prompt: {label['prompt']}")
        for key, value in extra.items():
            if key not in {"prompt", "prompt_index"}:
                row[key] = value
        merged.append(row)
    return merged


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def as_float(row: dict[str, Any], key: str) -> float:
    return float(row[key])


def as_int(row: dict[str, Any], key: str) -> int:
    return int(float(row[key]))


def class_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(as_int(row, "minimal_sufficient_steps")) for row in rows))


def majority_label(rows: list[dict[str, Any]]) -> int:
    counts = Counter(as_int(row, "minimal_sufficient_steps") for row in rows)
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def gini(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    counts = Counter(as_int(row, "minimal_sufficient_steps") for row in rows)
    impurity = 1.0
    total = len(rows)
    for count in counts.values():
        probability = count / total
        impurity -= probability * probability
    return impurity


def candidate_thresholds(rows: list[dict[str, Any]], feature: str) -> list[float]:
    values = sorted({as_float(row, feature) for row in rows})
    return [(left + right) / 2.0 for left, right in zip(values, values[1:])]


def best_split(
    rows: list[dict[str, Any]],
    features: list[str],
    min_samples_leaf: int,
) -> tuple[str, float, list[dict[str, Any]], list[dict[str, Any]], float] | None:
    base = gini(rows)
    best: tuple[str, float, list[dict[str, Any]], list[dict[str, Any]], float] | None = None
    for feature in features:
        for threshold in candidate_thresholds(rows, feature):
            left = [row for row in rows if as_float(row, feature) <= threshold]
            right = [row for row in rows if as_float(row, feature) > threshold]
            if len(left) < min_samples_leaf or len(right) < min_samples_leaf:
                continue
            weighted = (len(left) / len(rows)) * gini(left) + (len(right) / len(rows)) * gini(right)
            gain = base - weighted
            if best is None or gain > best[4]:
                best = (feature, threshold, left, right, gain)
    return best


def build_tree(
    rows: list[dict[str, Any]],
    features: list[str],
    depth: int,
    max_depth: int,
    min_samples_leaf: int,
) -> dict[str, Any]:
    prediction = majority_label(rows)
    counts = class_counts(rows)
    if depth >= max_depth or len(counts) == 1 or len(rows) < 2 * min_samples_leaf:
        return {
            "type": "leaf",
            "prediction": prediction,
            "samples": len(rows),
            "class_counts": counts,
        }

    split = best_split(rows, features, min_samples_leaf)
    if split is None or split[4] <= 0:
        return {
            "type": "leaf",
            "prediction": prediction,
            "samples": len(rows),
            "class_counts": counts,
        }
    feature, threshold, left, right, gain = split
    return {
        "type": "split",
        "feature": feature,
        "threshold": threshold,
        "gain": gain,
        "samples": len(rows),
        "class_counts": counts,
        "fallback_prediction": prediction,
        "left": build_tree(left, features, depth + 1, max_depth, min_samples_leaf),
        "right": build_tree(right, features, depth + 1, max_depth, min_samples_leaf),
    }


def predict_tree(tree: dict[str, Any], row: dict[str, Any]) -> int:
    node = tree
    while node["type"] != "leaf":
        value = as_float(row, node["feature"])
        node = node["left"] if value <= float(node["threshold"]) else node["right"]
    return int(node["prediction"])


def explain_tree_path(tree: dict[str, Any], row: dict[str, Any]) -> str:
    node = tree
    parts: list[str] = []
    while node["type"] != "leaf":
        feature = node["feature"]
        threshold = float(node["threshold"])
        value = as_float(row, feature)
        if value <= threshold:
            parts.append(f"{feature} <= {threshold:.3f}")
            node = node["left"]
        else:
            parts.append(f"{feature} > {threshold:.3f}")
            node = node["right"]
    parts.append(f"predict {int(node['prediction'])} steps")
    return " | ".join(parts)


def tree_to_rules(tree: dict[str, Any], prefix: list[str] | None = None) -> list[str]:
    prefix = prefix or []
    if tree["type"] == "leaf":
        counts = ", ".join(f"{label}:{count}" for label, count in sorted(tree["class_counts"].items()))
        condition = " and ".join(prefix) if prefix else "always"
        return [f"if {condition} -> {int(tree['prediction'])} steps (n={tree['samples']}, labels={counts})"]
    feature = tree["feature"]
    threshold = float(tree["threshold"])
    left_rules = tree_to_rules(tree["left"], [*prefix, f"{feature} <= {threshold:.3f}"])
    right_rules = tree_to_rules(tree["right"], [*prefix, f"{feature} > {threshold:.3f}"])
    return left_rules + right_rules


def leave_one_out(rows: list[dict[str, Any]], features: list[str], max_depth: int, min_samples_leaf: int) -> dict[str, Any]:
    predictions: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        train_rows = [candidate for i, candidate in enumerate(rows) if i != index]
        tree = build_tree(train_rows, features, 0, max_depth, min_samples_leaf)
        pred = predict_tree(tree, row)
        truth = as_int(row, "minimal_sufficient_steps")
        predictions.append(
            {
                "prompt_index": as_int(row, "prompt_index"),
                "true_steps": truth,
                "predicted_steps": pred,
                "exact": pred == truth,
                "under_budget": pred < truth,
                "over_budget": pred > truth,
            }
        )
    return {
        "num_prompts": len(predictions),
        "exact_accuracy": sum(1 for row in predictions if row["exact"]) / len(predictions),
        "under_budget_rate": sum(1 for row in predictions if row["under_budget"]) / len(predictions),
        "over_budget_rate": sum(1 for row in predictions if row["over_budget"]) / len(predictions),
        "mean_step_error": mean(row["predicted_steps"] - row["true_steps"] for row in predictions),
        "predictions": predictions,
    }


def grid_index(rows: list[dict[str, Any]]) -> dict[tuple[int, int], dict[str, Any]]:
    return {
        (as_int(row, "prompt_index"), as_int(row, "selected_steps")): row
        for row in rows
    }


def choose_available_step(predicted: int, available_steps: list[int]) -> int:
    for step in sorted(available_steps):
        if step >= predicted:
            return step
    return max(available_steps)


def build_prediction_rows(
    labels: list[dict[str, Any]],
    grid_rows: list[dict[str, Any]],
    tree: dict[str, Any],
    feature_columns: list[str],
    conservative_offset: int,
) -> list[dict[str, Any]]:
    by_prompt: dict[int, list[int]] = defaultdict(list)
    for row in grid_rows:
        by_prompt[as_int(row, "prompt_index")].append(as_int(row, "selected_steps"))
    by_prompt_step = grid_index(grid_rows)

    rows: list[dict[str, Any]] = []
    for label in labels:
        prompt_index = as_int(label, "prompt_index")
        raw_predicted = predict_tree(tree, label)
        predicted = raw_predicted + conservative_offset
        selected_step = choose_available_step(predicted, by_prompt[prompt_index])
        selected = by_prompt_step[(prompt_index, selected_step)]
        reference = by_prompt_step[(prompt_index, as_int(label, "reference_steps"))]
        selected_clip = float(selected["clip_score"])
        reference_clip = float(reference["clip_score"])
        threshold = float(label["clip_threshold"])
        row = {
            "prompt_index": prompt_index,
            "prompt": label["prompt"],
            "true_minimal_sufficient_steps": as_int(label, "minimal_sufficient_steps"),
            "raw_predicted_steps": raw_predicted,
            "conservative_offset": conservative_offset,
            "selected_steps": selected_step,
            "selected_guidance_scale": float(selected.get("selected_guidance_scale", selected.get("guidance_scale", 4.5))),
            "selected_clip_score": selected_clip,
            "fixed20_clip_score": reference_clip,
            "clip_delta_vs_fixed20": selected_clip - reference_clip,
            "clip_threshold": threshold,
            "quality_constraint_satisfied": selected_clip >= threshold,
            "selected_elapsed_seconds": float(selected["elapsed_seconds"]),
            "fixed20_elapsed_seconds": float(reference["elapsed_seconds"]),
            "speedup_percent_vs_fixed20": 100.0
            * (float(reference["elapsed_seconds"]) - float(selected["elapsed_seconds"]))
            / float(reference["elapsed_seconds"]),
            "tree_path": explain_tree_path(tree, label),
        }
        for feature in feature_columns:
            row[feature] = label[feature]
        rows.append(row)
    return rows


def method_summary(method: str, rows: list[dict[str, Any]], labels: list[dict[str, Any]], fixed20_time: float) -> dict[str, Any]:
    label_by_prompt = {as_int(label, "prompt_index"): label for label in labels}
    no_warmup = [row for row in rows if as_int(row, "prompt_index") != 1]
    elapsed_source = no_warmup if no_warmup else rows
    satisfied = 0
    deltas: list[float] = []
    for row in rows:
        prompt_index = as_int(row, "prompt_index")
        label = label_by_prompt[prompt_index]
        clip_score = float(row["clip_score"])
        deltas.append(clip_score - float(label["reference_clip_score"]))
        if clip_score >= float(label["clip_threshold"]):
            satisfied += 1
    current_time = mean(float(row["elapsed_seconds"]) for row in elapsed_source)
    return {
        "method": method,
        "num_prompts": len(rows),
        "avg_steps": mean(as_int(row, "selected_steps") for row in rows),
        "avg_elapsed_seconds_no_warmup": current_time,
        "speedup_percent_vs_fixed20": 100.0 * (fixed20_time - current_time) / fixed20_time,
        "avg_clip_score": mean(float(row["clip_score"]) for row in rows),
        "avg_clip_delta_vs_fixed20": mean(deltas),
        "quality_satisfaction_rate": satisfied / len(rows),
    }


def prediction_rows_as_method_rows(prediction_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in prediction_rows:
        rows.append(
            {
                "prompt_index": row["prompt_index"],
                "selected_steps": row["selected_steps"],
                "elapsed_seconds": row["selected_elapsed_seconds"],
                "clip_score": row["selected_clip_score"],
            }
        )
    return rows


def load_existing_method_rows(path: Path, methods: list[str]) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {}
    rows = read_csv(path)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        method = row["method"]
        if method not in methods:
            continue
        grouped[method].append(
            {
                "prompt_index": as_int(row, "prompt_index"),
                "selected_steps": as_int(row, "selected_steps"),
                "elapsed_seconds": float(row["elapsed_seconds"]),
                "clip_score": float(row["clip_score"]),
            }
        )
    return grouped


def average_no_warmup_time(rows: list[dict[str, Any]]) -> float:
    no_warmup = [row for row in rows if as_int(row, "prompt_index") != 1]
    return mean(float(row["elapsed_seconds"]) for row in (no_warmup or rows))


def fixed20_rows_from_grid(grid_rows: list[dict[str, Any]], reference_steps: int) -> list[dict[str, Any]]:
    return [
        {
            "prompt_index": as_int(row, "prompt_index"),
            "selected_steps": as_int(row, "selected_steps"),
            "elapsed_seconds": float(row["elapsed_seconds"]),
            "clip_score": float(row["clip_score"]),
        }
        for row in grid_rows
        if as_int(row, "selected_steps") == reference_steps
    ]


def oracle_rows_from_grid(labels: list[dict[str, Any]], grid_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_prompt_step = grid_index(grid_rows)
    rows: list[dict[str, Any]] = []
    for label in labels:
        selected = by_prompt_step[(as_int(label, "prompt_index"), as_int(label, "minimal_sufficient_steps"))]
        rows.append(
            {
                "prompt_index": as_int(selected, "prompt_index"),
                "selected_steps": as_int(selected, "selected_steps"),
                "elapsed_seconds": float(selected["elapsed_seconds"]),
                "clip_score": float(selected["clip_score"]),
            }
        )
    return rows


def write_markdown(
    path: Path,
    model: dict[str, Any],
    prediction_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Calibrated-PCAS Predictor Summary",
        "",
        "The predictor is a small rule-based decision tree trained on prompt features and minimal sufficient step labels.",
        "",
        "## Learned Rules",
        "",
    ]
    for rule in model["rules"]:
        lines.append(f"- {rule}")

    cv = model["leave_one_out"]
    lines.extend(
        [
            "",
            "## Leave-One-Out Diagnostics",
            "",
            f"- Exact label accuracy: {cv['exact_accuracy'] * 100.0:.1f}%",
            f"- Under-budget rate: {cv['under_budget_rate'] * 100.0:.1f}%",
            f"- Over-budget rate: {cv['over_budget_rate'] * 100.0:.1f}%",
            f"- Mean step error: {cv['mean_step_error']:.3f}",
            "",
            "## Method Comparison",
            "",
            "| Method | Prompts | Avg steps | Avg time no-warmup (s) | Speedup vs Fixed-20 | Avg CLIPScore | Avg CLIP delta | Constraint satisfaction |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary_rows:
        lines.append(
            "| {method} | {n} | {steps:.3f} | {time:.3f} | {speed:.3f}% | {clip:.3f} | {delta:.3f} | {sat:.1f}% |".format(
                method=row["method"],
                n=int(row["num_prompts"]),
                steps=float(row["avg_steps"]),
                time=float(row["avg_elapsed_seconds_no_warmup"]),
                speed=float(row["speedup_percent_vs_fixed20"]),
                clip=float(row["avg_clip_score"]),
                delta=float(row["avg_clip_delta_vs_fixed20"]),
                sat=float(row["quality_satisfaction_rate"]) * 100.0,
            )
        )

    misses = [row for row in prediction_rows if str(row["quality_constraint_satisfied"]).lower() not in {"true", "1"}]
    lines.extend(
        [
            "",
            "## Constraint Misses",
            "",
        ]
    )
    if not misses:
        lines.append("No calibrated predictor outputs violate the CLIPScore tolerance on this calibration set.")
    else:
        lines.extend(
            [
                "| Prompt | True steps | Predicted steps | CLIP delta | Tree path |",
                "| --- | ---: | ---: | ---: | --- |",
            ]
        )
        for row in misses:
            lines.append(
                "| {prompt} | {truth} | {pred} | {delta:.3f} | {path} |".format(
                    prompt=str(row["prompt"]).replace("|", "/"),
                    truth=int(row["true_minimal_sufficient_steps"]),
                    pred=int(row["selected_steps"]),
                    delta=float(row["clip_delta_vs_fixed20"]),
                    path=str(row["tree_path"]).replace("|", "/"),
                )
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train an interpretable predictor for Calibrated PCAS.")
    parser.add_argument("--labels", default="results/day6_calibration_labels.csv")
    parser.add_argument("--grid", default="results/day6_calibration_grid_clipscore.csv")
    parser.add_argument("--feature-file", default=None)
    parser.add_argument("--feature-columns", default=None)
    parser.add_argument("--comparison-results", default="results/day3_pcas_all_balanced_clipscore_results.csv")
    parser.add_argument(
        "--comparison-methods",
        default="fixed_20,balanced_pcas,deepseek_balanced_pcas,calibrated_pcas",
        help="Comma-separated method names to import from --comparison-results when present.",
    )
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--output-prefix", default="day6_calibrated_pcas")
    parser.add_argument("--model-output", default="results/day6_calibrated_pcas_tree.json")
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--min-samples-leaf", type=int, default=3)
    parser.add_argument("--conservative-offset", type=int, default=0)
    args = parser.parse_args()

    labels = merge_feature_file(read_csv(Path(args.labels)), Path(args.feature_file) if args.feature_file else None)
    grid_rows = read_csv(Path(args.grid))
    reference_steps = as_int(labels[0], "reference_steps")
    feature_columns = parse_feature_columns(args.feature_columns)

    tree = build_tree(labels, feature_columns, 0, args.max_depth, args.min_samples_leaf)
    cv = leave_one_out(labels, feature_columns, args.max_depth, args.min_samples_leaf)
    model = {
        "model_type": "pure_python_decision_tree_classifier",
        "target": "minimal_sufficient_steps",
        "feature_columns": feature_columns,
        "max_depth": args.max_depth,
        "min_samples_leaf": args.min_samples_leaf,
        "conservative_offset": args.conservative_offset,
        "tree": tree,
        "rules": tree_to_rules(tree),
        "leave_one_out": cv,
    }

    prediction_rows = build_prediction_rows(labels, grid_rows, tree, feature_columns, args.conservative_offset)
    imported_methods = [method.strip() for method in args.comparison_methods.split(",") if method.strip()]
    imported_rows = load_existing_method_rows(Path(args.comparison_results), imported_methods)

    method_rows: dict[str, list[dict[str, Any]]] = {
        "fixed_20": imported_rows.get("fixed_20", fixed20_rows_from_grid(grid_rows, reference_steps)),
        "oracle_min_sufficient": oracle_rows_from_grid(labels, grid_rows),
        "calibrated_pcas": imported_rows.get("calibrated_pcas", prediction_rows_as_method_rows(prediction_rows)),
    }
    for method, rows in imported_rows.items():
        if method not in method_rows:
            method_rows[method] = rows

    fixed20_time = average_no_warmup_time(method_rows["fixed_20"])

    base_order = ["fixed_20", "balanced_pcas", "deepseek_balanced_pcas", "oracle_min_sufficient", "calibrated_pcas"]
    method_order = base_order + sorted(method for method in method_rows if method not in base_order)
    summary_rows = [
        method_summary(method, method_rows[method], labels, fixed20_time)
        for method in method_order
        if method in method_rows
    ]

    results_dir = Path(args.results_dir)
    Path(args.model_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.model_output).write_text(json.dumps(model, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(results_dir / f"{args.output_prefix}_predictions.csv", prediction_rows)
    write_csv(
        results_dir / f"{args.output_prefix}_summary.csv",
        summary_rows,
        [
            "method",
            "num_prompts",
            "avg_steps",
            "avg_elapsed_seconds_no_warmup",
            "speedup_percent_vs_fixed20",
            "avg_clip_score",
            "avg_clip_delta_vs_fixed20",
            "quality_satisfaction_rate",
        ],
    )
    write_markdown(results_dir / f"{args.output_prefix}_summary.md", model, prediction_rows, summary_rows)
    print(f"Wrote {args.model_output}")
    print(f"Wrote {results_dir / f'{args.output_prefix}_predictions.csv'}")
    print(f"Wrote {results_dir / f'{args.output_prefix}_summary.csv'}")
    print(f"Wrote {results_dir / f'{args.output_prefix}_summary.md'}")


if __name__ == "__main__":
    main()
