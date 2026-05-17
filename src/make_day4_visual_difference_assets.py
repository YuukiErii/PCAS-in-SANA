from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, ImageStat


SOURCE_PATH = Path("results/day3_pcas_all_balanced_clipscore_results.csv")
METRICS_PATH = Path("results/day4_hard_prompt_difference_vs_fixed20.csv")
SUMMARY_PATH = Path("results/day4_hard_prompt_visual_tie_summary.md")
FIGURE_PATH = Path("results/figures/day4_hard_prompt_difference_heatmap_vs_fixed20.png")

HARD_PROMPT_INDICES = [18, 19, 21, 22, 23, 26, 28, 30]
REFERENCE_METHOD = "fixed_20"
CANDIDATE_METHODS = [
    "fixed_28",
    "rule_pcas_7_2",
    "balanced_pcas",
    "deepseek_balanced_pcas",
]
METHOD_LABELS = {
    "fixed_20": "Fixed-20",
    "fixed_28": "Fixed-28",
    "rule_pcas_7_2": "Rule-PCAS",
    "balanced_pcas": "Balanced-PCAS",
    "deepseek_balanced_pcas": "DeepSeek-Balanced",
}
METHODS = [REFERENCE_METHOD, *CANDIDATE_METHODS]


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    font: ImageFont.ImageFont,
    fill: str,
    max_width: int,
    line_height: int,
    max_lines: int,
) -> None:
    lines = wrap_text(draw, text, font, max_width)[:max_lines]
    for offset, line in enumerate(lines):
        draw.text((xy[0], xy[1] + offset * line_height), line, font=font, fill=fill)


def draw_centered_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], width: int, text: str, font: ImageFont.ImageFont, fill: str) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text((xy[0] + max(0, (width - text_w) // 2), xy[1]), text, font=font, fill=fill)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_rgb(path: str | Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def fit_image(image: Image.Image, size: int) -> Image.Image:
    image = image.copy()
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), "white")
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    return canvas


def max_channel_grayscale(diff: Image.Image) -> Image.Image:
    bands = diff.split()
    return ImageChops.lighter(ImageChops.lighter(bands[0], bands[1]), bands[2])


def enhanced_heatmap(diff: Image.Image, boost: int = 10) -> Image.Image:
    gray = max_channel_grayscale(diff)
    boosted = gray.point(lambda value: min(255, value * boost))
    return ImageOps.colorize(boosted, black="#f7f7f7", white="#c8161d", mid="#f6d04d")


def diff_metrics(reference: Image.Image, candidate: Image.Image) -> tuple[dict[str, float], Image.Image]:
    if candidate.size != reference.size:
        candidate = candidate.resize(reference.size, Image.Resampling.LANCZOS)
    diff = ImageChops.difference(reference, candidate)
    stat = ImageStat.Stat(diff)
    mean_abs = sum(stat.mean) / len(stat.mean)
    sq_mean = sum(value * value for value in stat.rms) / len(stat.rms)
    rmse = math.sqrt(sq_mean)

    gray = max_channel_grayscale(diff)
    hist = gray.histogram()
    total = reference.width * reference.height
    gt2 = sum(hist[3:]) / total * 100.0
    gt8 = sum(hist[9:]) / total * 100.0
    gt16 = sum(hist[17:]) / total * 100.0
    max_diff = max(index for index, count in enumerate(hist) if count)

    return (
        {
            "mean_abs_rgb_0_255": mean_abs,
            "rmse_rgb_0_255": rmse,
            "max_channel_diff_0_255": float(max_diff),
            "pixels_changed_gt2_pct": gt2,
            "pixels_changed_gt8_pct": gt8,
            "pixels_changed_gt16_pct": gt16,
        },
        diff,
    )


def similarity_bucket(mean_abs: float, gt8: float) -> str:
    if mean_abs < 1.0 and gt8 < 1.0:
        return "near_identical"
    if mean_abs < 3.0 and gt8 < 8.0:
        return "minor_detail_change"
    if mean_abs < 8.0 and gt8 < 25.0:
        return "noticeable_local_change"
    return "clear_visual_change"


def row_index(rows: list[dict[str, str]]) -> dict[tuple[int, str], dict[str, str]]:
    return {(int(row["prompt_index"]), row["method"]): row for row in rows}


def hard_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row["method"] in METHODS and int(row["prompt_index"]) in HARD_PROMPT_INDICES
    ]


def compute_rows(rows: list[dict[str, str]]) -> tuple[list[dict], dict[tuple[int, str], Image.Image]]:
    index = row_index(rows)
    prompt_indices = sorted({int(row["prompt_index"]) for row in rows})
    metric_rows: list[dict] = []
    heatmaps: dict[tuple[int, str], Image.Image] = {}

    for prompt_index in prompt_indices:
        reference_row = index[(prompt_index, REFERENCE_METHOD)]
        reference = load_rgb(reference_row["image_path"])
        for method in CANDIDATE_METHODS:
            candidate_row = index[(prompt_index, method)]
            candidate = load_rgb(candidate_row["image_path"])
            metrics, diff = diff_metrics(reference, candidate)
            bucket = similarity_bucket(metrics["mean_abs_rgb_0_255"], metrics["pixels_changed_gt8_pct"])
            heatmaps[(prompt_index, method)] = enhanced_heatmap(diff)

            metric_rows.append(
                {
                    "prompt_index": prompt_index,
                    "reference_method": REFERENCE_METHOD,
                    "candidate_method": method,
                    "reference_image_path": reference_row["image_path"],
                    "candidate_image_path": candidate_row["image_path"],
                    "mean_abs_rgb_0_255": f"{metrics['mean_abs_rgb_0_255']:.4f}",
                    "rmse_rgb_0_255": f"{metrics['rmse_rgb_0_255']:.4f}",
                    "max_channel_diff_0_255": f"{metrics['max_channel_diff_0_255']:.0f}",
                    "pixels_changed_gt2_pct": f"{metrics['pixels_changed_gt2_pct']:.2f}",
                    "pixels_changed_gt8_pct": f"{metrics['pixels_changed_gt8_pct']:.2f}",
                    "pixels_changed_gt16_pct": f"{metrics['pixels_changed_gt16_pct']:.2f}",
                    "similarity_bucket": bucket,
                }
            )
    return metric_rows, heatmaps


def make_heatmap_grid(rows: list[dict[str, str]], heatmaps: dict[tuple[int, str], Image.Image], output_path: Path) -> None:
    index = row_index(rows)
    prompt_indices = sorted({int(row["prompt_index"]) for row in rows})
    title_font = load_font(34, bold=True)
    subtitle_font = load_font(18)
    header_font = load_font(16, bold=True)
    small_font = load_font(13)

    margin = 28
    prompt_w = 300
    thumb = 164
    gap = 18
    header_h = 118
    row_h = 196
    columns = [REFERENCE_METHOD, *CANDIDATE_METHODS]
    width = margin * 2 + prompt_w + gap + len(columns) * thumb + (len(columns) - 1) * gap
    height = margin * 2 + header_h + len(prompt_indices) * row_h

    canvas = Image.new("RGB", (width, height), "#fbfaf6")
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 24), "Day 4 Visual Difference vs Fixed-20", font=title_font, fill="#202428")
    draw.text(
        (margin, 68),
        "Heatmaps are boosted absolute pixel differences. Pale means almost unchanged; yellow/red marks changed details.",
        font=subtitle_font,
        fill="#50606a",
    )

    x0 = margin + prompt_w + gap
    for col_i, method in enumerate(columns):
        label = METHOD_LABELS[method] if method == REFERENCE_METHOD else f"{METHOD_LABELS[method]} diff"
        draw_centered_text(draw, (x0 + col_i * (thumb + gap), 102), thumb, label, header_font, "#202428")

    y = margin + header_h
    for row_i, prompt_index in enumerate(prompt_indices):
        fill = "#ffffff" if row_i % 2 == 0 else "#f0f2ee"
        draw.rounded_rectangle((margin - 10, y - 10, width - margin + 10, y + row_h - 18), radius=10, fill=fill, outline="#d8ddd4")
        prompt = index[(prompt_index, REFERENCE_METHOD)]["prompt"]
        draw.text((margin, y + 4), f"Prompt {prompt_index}", font=header_font, fill="#202428")
        draw_wrapped_text(
            draw,
            prompt,
            (margin, y + 32),
            small_font,
            "#343a40",
            prompt_w - 18,
            18,
            max_lines=6,
        )

        ref = fit_image(load_rgb(index[(prompt_index, REFERENCE_METHOD)]["image_path"]), thumb)
        canvas.paste(ref, (x0, y + 6))
        draw.rectangle((x0, y + 6, x0 + thumb, y + 6 + thumb), outline="#b7c0b4")

        for col_i, method in enumerate(CANDIDATE_METHODS, start=1):
            x = x0 + col_i * (thumb + gap)
            tile = fit_image(heatmaps[(prompt_index, method)], thumb)
            canvas.paste(tile, (x, y + 6))
            draw.rectangle((x, y + 6, x + thumb, y + 6 + thumb), outline="#b7c0b4")
        y += row_h

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, quality=95)


def write_summary(rows: list[dict]) -> None:
    by_method: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_method[row["candidate_method"]].append(row)

    lines = [
        "# Day 4 Hard Prompt Visual Similarity Summary",
        "",
        "This supplement addresses the problem that many generated images look nearly the same by measuring each candidate method against Fixed-20.",
        "",
        "| Candidate | Pairs | Avg mean abs diff | Avg pixels changed >8 | Dominant bucket |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for method in CANDIDATE_METHODS:
        method_rows = by_method[method]
        avg_mean = sum(float(row["mean_abs_rgb_0_255"]) for row in method_rows) / len(method_rows)
        avg_gt8 = sum(float(row["pixels_changed_gt8_pct"]) for row in method_rows) / len(method_rows)
        buckets: dict[str, int] = defaultdict(int)
        for row in method_rows:
            buckets[row["similarity_bucket"]] += 1
        dominant = max(buckets.items(), key=lambda item: item[1])[0]
        lines.append(f"| {METHOD_LABELS[method]} | {len(method_rows)} | {avg_mean:.3f} | {avg_gt8:.2f}% | {dominant} |")

    lines.extend(
        [
            "",
            "Recommended interpretation:",
            "",
            "- Do not force manual scores when the visual difference is largely imperceptible.",
            "- Treat the hard-prompt side-by-side comparison as a qualitative sanity check.",
            "- In the report, describe Day 4 as evidence that PCAS preserves visual appearance under lower compute, not as strong evidence of quality improvement.",
            "",
            "Files:",
            "",
            f"- Difference metrics: `{METRICS_PATH}`",
            f"- Difference heatmap: `{FIGURE_PATH}`",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = hard_rows(read_csv(SOURCE_PATH))
    metric_rows, heatmaps = compute_rows(rows)
    write_csv(
        METRICS_PATH,
        metric_rows,
        [
            "prompt_index",
            "reference_method",
            "candidate_method",
            "reference_image_path",
            "candidate_image_path",
            "mean_abs_rgb_0_255",
            "rmse_rgb_0_255",
            "max_channel_diff_0_255",
            "pixels_changed_gt2_pct",
            "pixels_changed_gt8_pct",
            "pixels_changed_gt16_pct",
            "similarity_bucket",
        ],
    )
    make_heatmap_grid(rows, heatmaps, FIGURE_PATH)
    write_summary(metric_rows)
    print("Wrote Day 4 visual difference assets.")


if __name__ == "__main__":
    main()
