from __future__ import annotations

import argparse
import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


METHOD_ORDER = ["fixed_10", "fixed_20", "fixed_28", "rule_pcas_7_2", "deepseek_pcas_7_3"]
METHOD_LABELS = {
    "fixed_10": "Fixed-10",
    "fixed_20": "Fixed-20",
    "fixed_28": "Fixed-28",
    "rule_pcas_7_2": "Rule-PCAS 7.2",
    "deepseek_pcas_7_3": "DeepSeek-PCAS 7.3",
}
GROUP_ORDER = ["10_words", "30_words", "50_words"]
COLORS = {
    "fixed_10": "#4c78a8",
    "fixed_20": "#8a8f98",
    "fixed_28": "#d9903d",
    "rule_pcas_7_2": "#2f6f73",
    "deepseek_pcas_7_3": "#7f5f9f",
}


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def read_summary(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def row_index(rows: list[dict]) -> dict[tuple[str, str], dict]:
    return {(row["method"], row["prompt_length_group"]): row for row in rows}


def draw_axes(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], x_ticks: list[float], y_ticks: list[float], x_min: float, x_max: float, y_min: float, y_max: float, font: ImageFont.ImageFont) -> None:
    x0, y0, x1, y1 = box
    draw.line((x0, y1, x1, y1), fill="#27323a", width=3)
    draw.line((x0, y0, x0, y1), fill="#27323a", width=3)
    for tick in x_ticks:
        x = x0 + int((tick - x_min) / (x_max - x_min) * (x1 - x0))
        draw.line((x, y0, x, y1), fill="#e0e5dd", width=2)
        draw.text((x - 30, y1 + 18), f"{tick:.1f}", font=font, fill="#52616b")
    for tick in y_ticks:
        y = y1 - int((tick - y_min) / (y_max - y_min) * (y1 - y0))
        draw.line((x0, y, x1, y), fill="#e0e5dd", width=2)
        draw.text((x0 - 78, y - 14), f"{tick:.1f}", font=font, fill="#52616b")


def make_tradeoff_chart(rows: list[dict], output_path: Path) -> None:
    index = row_index(rows)
    all_rows = [index[(method, "all")] for method in METHOD_ORDER]
    times = [float(row["avg_elapsed_seconds_no_warmup"]) for row in all_rows]
    scores = [float(row["avg_clip_score"]) for row in all_rows]
    x_min, x_max = 0.45, max(times) + 0.15
    y_min, y_max = min(scores) - 0.15, max(scores) + 0.15

    width, height = 2600, 1650
    margin = 130
    chart = (360, 300, width - margin, height - 260)
    image = Image.new("RGB", (width, height), "#fbfbf7")
    draw = ImageDraw.Draw(image)
    title_font = load_font(54, bold=True)
    subtitle_font = load_font(28)
    axis_font = load_font(24)
    label_font = load_font(25, bold=True)

    draw.text((margin, 82), "Day 4 Speed-Quality Tradeoff", font=title_font, fill="#1f2328")
    draw.text((margin, 150), "CLIPScore is CLIP image-text cosine similarity x100; higher is better, lower time is faster.", font=subtitle_font, fill="#52616b")
    draw.text((margin, 192), "The methods are very close in CLIPScore, so runtime and compute allocation become the main visible difference.", font=subtitle_font, fill="#52616b")

    x_ticks = [0.5, 0.8, 1.1, 1.4]
    y_ticks = [round(y_min, 1), round((y_min + y_max) / 2, 1), round(y_max, 1)]
    draw_axes(draw, chart, x_ticks, y_ticks, x_min, x_max, y_min, y_max, axis_font)
    draw.text((chart[0] + 640, height - 180), "Average time per image, no warm-up (s)", font=axis_font, fill="#1f2328")
    draw.text((margin - 20, chart[1] - 48), "Avg CLIPScore", font=axis_font, fill="#1f2328")

    for row in all_rows:
        method = row["method"]
        x_val = float(row["avg_elapsed_seconds_no_warmup"])
        y_val = float(row["avg_clip_score"])
        steps = float(row["avg_steps"])
        x = chart[0] + int((x_val - x_min) / (x_max - x_min) * (chart[2] - chart[0]))
        y = chart[3] - int((y_val - y_min) / (y_max - y_min) * (chart[3] - chart[1]))
        radius = int(20 + steps * 1.1)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=COLORS[method], outline="#1f2328", width=3)
        draw.text((x + radius + 18, y - 22), f"{METHOD_LABELS[method]}  {x_val:.3f}s / {y_val:.3f}", font=label_font, fill="#1f2328")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def make_group_clipscore_chart(rows: list[dict], output_path: Path) -> None:
    index = row_index(rows)
    width, height = 2800, 1700
    margin = 120
    chart_x = 300
    chart_y = 300
    chart_w = width - chart_x - margin
    chart_h = height - chart_y - 250
    image = Image.new("RGB", (width, height), "#fbfbf7")
    draw = ImageDraw.Draw(image)

    title_font = load_font(54, bold=True)
    subtitle_font = load_font(28)
    axis_font = load_font(24)
    label_font = load_font(24, bold=True)
    value_font = load_font(22)

    draw.text((margin, 82), "Day 4 CLIPScore by Prompt Length Group", font=title_font, fill="#1f2328")
    draw.text((margin, 150), "All methods remain close in CLIP-based text-image alignment across 10, 30, and 50-word prompts.", font=subtitle_font, fill="#52616b")

    scores = [float(index[(method, group)]["avg_clip_score"]) for method in METHOD_ORDER for group in GROUP_ORDER]
    y_min = min(scores) - 0.4
    y_max = max(scores) + 0.4

    draw.line((chart_x, chart_y, chart_x, chart_y + chart_h), fill="#27323a", width=3)
    draw.line((chart_x, chart_y + chart_h, chart_x + chart_w, chart_y + chart_h), fill="#27323a", width=3)
    for tick in [34.0, 35.0, 36.0, 37.0]:
        y = chart_y + chart_h - int((tick - y_min) / (y_max - y_min) * chart_h)
        draw.line((chart_x, y, chart_x + chart_w, y), fill="#e0e5dd", width=2)
        draw.text((chart_x - 76, y - 14), f"{tick:.1f}", font=axis_font, fill="#52616b")

    group_w = chart_w // len(GROUP_ORDER)
    bar_w = 58
    bar_gap = 18
    for g_idx, group in enumerate(GROUP_ORDER):
        center_x = chart_x + g_idx * group_w + group_w // 2
        draw.text((center_x - 60, chart_y + chart_h + 32), group, font=label_font, fill="#1f2328")
        start_x = center_x - (len(METHOD_ORDER) * bar_w + (len(METHOD_ORDER) - 1) * bar_gap) // 2
        for m_idx, method in enumerate(METHOD_ORDER):
            score = float(index[(method, group)]["avg_clip_score"])
            x0 = start_x + m_idx * (bar_w + bar_gap)
            y0 = chart_y + chart_h - int((score - y_min) / (y_max - y_min) * chart_h)
            draw.rounded_rectangle((x0, y0, x0 + bar_w, chart_y + chart_h), radius=8, fill=COLORS[method])
            draw.text((x0 - 14, y0 - 30), f"{score:.1f}", font=value_font, fill="#1f2328")

    legend_x = margin
    legend_y = height - 140
    for method in METHOD_ORDER:
        draw.rounded_rectangle((legend_x, legend_y, legend_x + 38, legend_y + 38), radius=7, fill=COLORS[method])
        draw.text((legend_x + 52, legend_y + 4), METHOD_LABELS[method], font=axis_font, fill="#1f2328")
        legend_x += 430

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Day 4 CLIPScore figures.")
    parser.add_argument("--summary", default="results/day4_clipscore_summary.csv")
    parser.add_argument("--figures-dir", default="results/figures")
    args = parser.parse_args()

    rows = read_summary(Path(args.summary))
    figures_dir = Path(args.figures_dir)
    make_tradeoff_chart(rows, figures_dir / "day4_speed_quality_tradeoff.png")
    make_group_clipscore_chart(rows, figures_dir / "day4_clipscore_by_group.png")
    print(f"Wrote {figures_dir / 'day4_speed_quality_tradeoff.png'}")
    print(f"Wrote {figures_dir / 'day4_clipscore_by_group.png'}")


if __name__ == "__main__":
    main()
