from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


METHODS = ["fixed_20", "rule_pcas_7_2", "balanced_pcas"]
METHOD_LABELS = {
    "fixed_20": "Fixed-20",
    "rule_pcas_7_2": "Rule-PCAS",
    "balanced_pcas": "Balanced-PCAS",
}
GROUPS = ["all", "10_words", "30_words", "50_words"]
COLORS = {
    "fixed_20": "#8a8f98",
    "rule_pcas_7_2": "#2f6f73",
    "balanced_pcas": "#b85b38",
}


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def index_rows(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(row["method"], row["prompt_length_group"]): row for row in rows}


def make_speed_chart(summary_rows: list[dict[str, str]], output_path: Path) -> None:
    index = index_rows(summary_rows)
    width, height = 2600, 1500
    margin = 120
    chart_x, chart_y = 360, 280
    chart_w, chart_h = width - chart_x - margin, 880
    image = Image.new("RGB", (width, height), "#fbfbf7")
    draw = ImageDraw.Draw(image)

    title_font = load_font(54, bold=True)
    subtitle_font = load_font(28)
    axis_font = load_font(24)
    label_font = load_font(25, bold=True)
    value_font = load_font(22)

    draw.text((margin, 78), "Balanced-PCAS Solves the Small Overall Speed Gain", font=title_font, fill="#1f2328")
    draw.text((margin, 146), "Average inference time per image, no warm-up. Lower is better.", font=subtitle_font, fill="#52616b")
    draw.text((margin, 188), "Policy: 8 / 16 / 24 steps for 10 / 30 / 50-word prompts.", font=subtitle_font, fill="#52616b")

    max_time = max(float(index[(method, group)]["avg_elapsed_seconds_no_warmup"]) for method in METHODS for group in GROUPS)
    max_time *= 1.12
    for tick in range(6):
        value = max_time * tick / 5
        x = chart_x + int(chart_w * tick / 5)
        draw.line((x, chart_y, x, chart_y + chart_h), fill="#e0e5dd", width=2)
        draw.text((x - 26, chart_y + chart_h + 24), f"{value:.1f}s", font=axis_font, fill="#52616b")
    draw.line((chart_x, chart_y + chart_h, chart_x + chart_w, chart_y + chart_h), fill="#27323a", width=3)
    draw.line((chart_x, chart_y, chart_x, chart_y + chart_h), fill="#27323a", width=3)

    group_h = chart_h // len(GROUPS)
    bar_h = 38
    for g_idx, group in enumerate(GROUPS):
        y0 = chart_y + g_idx * group_h + 28
        draw.text((margin, y0 + 42), group, font=label_font, fill="#1f2328")
        for m_idx, method in enumerate(METHODS):
            time_value = float(index[(method, group)]["avg_elapsed_seconds_no_warmup"])
            bar_w = int(chart_w * time_value / max_time)
            y = y0 + m_idx * (bar_h + 12)
            draw.rounded_rectangle((chart_x, y, chart_x + bar_w, y + bar_h), radius=8, fill=COLORS[method])
            draw.text((chart_x + bar_w + 18, y + 5), f"{METHOD_LABELS[method]} {time_value:.3f}s", font=value_font, fill="#1f2328")

    legend_y = height - 140
    legend_x = margin
    for method in METHODS:
        draw.rounded_rectangle((legend_x, legend_y, legend_x + 38, legend_y + 38), radius=7, fill=COLORS[method])
        draw.text((legend_x + 52, legend_y + 4), METHOD_LABELS[method], font=axis_font, fill="#1f2328")
        legend_x += 360

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def make_tradeoff_chart(clip_rows: list[dict[str, str]], output_path: Path) -> None:
    index = index_rows(clip_rows)
    all_rows = [index[(method, "all")] for method in METHODS]
    times = [float(row["avg_elapsed_seconds_no_warmup"]) for row in all_rows]
    scores = [float(row["avg_clip_score"]) for row in all_rows]

    width, height = 2000, 1300
    margin = 110
    chart = (270, 260, width - margin, height - 220)
    image = Image.new("RGB", (width, height), "#fbfbf7")
    draw = ImageDraw.Draw(image)

    title_font = load_font(48, bold=True)
    subtitle_font = load_font(25)
    axis_font = load_font(22)
    label_font = load_font(23, bold=True)

    draw.text((margin, 70), "Balanced-PCAS Speed-Quality Tradeoff", font=title_font, fill="#1f2328")
    draw.text((margin, 134), "CLIPScore stays close while runtime drops. Lower time is better; higher CLIPScore is better.", font=subtitle_font, fill="#52616b")

    x_min, x_max = min(times) - 0.08, max(times) + 0.08
    y_min, y_max = min(scores) - 0.06, max(scores) + 0.06
    x0, y0, x1, y1 = chart
    draw.line((x0, y1, x1, y1), fill="#27323a", width=3)
    draw.line((x0, y0, x0, y1), fill="#27323a", width=3)
    for tick in range(5):
        value = x_min + (x_max - x_min) * tick / 4
        x = x0 + int((value - x_min) / (x_max - x_min) * (x1 - x0))
        draw.line((x, y0, x, y1), fill="#e0e5dd", width=2)
        draw.text((x - 36, y1 + 18), f"{value:.2f}s", font=axis_font, fill="#52616b")
    for tick in range(5):
        value = y_min + (y_max - y_min) * tick / 4
        y = y1 - int((value - y_min) / (y_max - y_min) * (y1 - y0))
        draw.line((x0, y, x1, y), fill="#e0e5dd", width=2)
        draw.text((x0 - 88, y - 13), f"{value:.2f}", font=axis_font, fill="#52616b")

    for row in all_rows:
        method = row["method"]
        x_value = float(row["avg_elapsed_seconds_no_warmup"])
        y_value = float(row["avg_clip_score"])
        steps = float(row["avg_steps"])
        x = x0 + int((x_value - x_min) / (x_max - x_min) * (x1 - x0))
        y = y1 - int((y_value - y_min) / (y_max - y_min) * (y1 - y0))
        radius = int(24 + steps * 1.4)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=COLORS[method], outline="#1f2328", width=3)
        draw.text((x + radius + 18, y - 16), f"{METHOD_LABELS[method]}  {x_value:.3f}s / {y_value:.3f}", font=label_font, fill="#1f2328")

    draw.text((chart[0] + 480, height - 138), "Average time per image, no warm-up", font=axis_font, fill="#1f2328")
    draw.text((margin - 18, chart[1] - 42), "Avg CLIPScore", font=axis_font, fill="#1f2328")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def main() -> None:
    summary_rows = read_csv(Path("results/day3_pcas_balanced_summary.csv"))
    clip_rows = read_csv(Path("results/day3_pcas_balanced_clipscore_summary.csv"))
    make_speed_chart(summary_rows, Path("results/figures/day3_pcas_balanced_speed_chart.png"))
    make_tradeoff_chart(clip_rows, Path("results/figures/day3_pcas_balanced_speed_quality_tradeoff.png"))
    print("Wrote Balanced-PCAS figures.")


if __name__ == "__main__":
    main()
