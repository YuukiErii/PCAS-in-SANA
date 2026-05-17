from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SPEED_METHODS = ["fixed_20", "deepseek_pcas_7_3", "deepseek_balanced_pcas"]
TRADEOFF_METHODS = ["fixed_20", "deepseek_pcas_7_3", "deepseek_balanced_pcas", "balanced_pcas"]
METHOD_LABELS = {
    "fixed_20": "Fixed-20",
    "deepseek_pcas_7_3": "DeepSeek-PCAS",
    "deepseek_balanced_pcas": "DeepSeek-Balanced",
    "balanced_pcas": "Balanced-PCAS",
}
COLORS = {
    "fixed_20": "#8a8f98",
    "deepseek_pcas_7_3": "#7f5f9f",
    "deepseek_balanced_pcas": "#2f6f73",
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


def all_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["method"]: row for row in rows if row["prompt_length_group"] == "all"}


def make_speed_chart(summary_rows: list[dict[str, str]], output_path: Path) -> None:
    rows = all_rows(summary_rows)
    width, height = 1900, 1050
    margin = 100
    chart_x, chart_y = 320, 250
    chart_w, chart_h = width - chart_x - margin, 560
    image = Image.new("RGB", (width, height), "#fbfbf7")
    draw = ImageDraw.Draw(image)
    title_font = load_font(48, bold=True)
    subtitle_font = load_font(25)
    axis_font = load_font(22)
    label_font = load_font(24, bold=True)
    value_font = load_font(22)

    draw.text((margin, 64), "DeepSeek-PCAS: From Conservative to Budget-Constrained", font=title_font, fill="#1f2328")
    draw.text((margin, 128), "Average inference time per image, no warm-up. Lower is better.", font=subtitle_font, fill="#52616b")
    draw.text((margin, 164), "DeepSeek-Balanced keeps semantic labels but uses 8 / 16 / 22 steps for low / medium / high.", font=subtitle_font, fill="#52616b")

    max_time = max(float(rows[method]["avg_elapsed_seconds_no_warmup"]) for method in SPEED_METHODS) * 1.12
    for tick in range(6):
        value = max_time * tick / 5
        x = chart_x + int(chart_w * tick / 5)
        draw.line((x, chart_y, x, chart_y + chart_h), fill="#e0e5dd", width=2)
        draw.text((x - 30, chart_y + chart_h + 22), f"{value:.1f}s", font=axis_font, fill="#52616b")
    draw.line((chart_x, chart_y + chart_h, chart_x + chart_w, chart_y + chart_h), fill="#27323a", width=3)

    bar_h = 70
    gap = 46
    for idx, method in enumerate(SPEED_METHODS):
        y = chart_y + 30 + idx * (bar_h + gap)
        value = float(rows[method]["avg_elapsed_seconds_no_warmup"])
        steps = float(rows[method]["avg_steps"])
        bar_w = int(chart_w * value / max_time)
        draw.text((margin, y + 18), METHOD_LABELS[method], font=label_font, fill="#1f2328")
        draw.rounded_rectangle((chart_x, y, chart_x + bar_w, y + bar_h), radius=10, fill=COLORS[method])
        draw.text((chart_x + bar_w + 20, y + 18), f"{value:.3f}s | {steps:.1f} steps", font=value_font, fill="#1f2328")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def make_tradeoff_chart(clip_rows: list[dict[str, str]], output_path: Path) -> None:
    rows = all_rows(clip_rows)
    width, height = 2000, 1300
    margin = 110
    chart = (280, 270, width - margin, height - 220)
    image = Image.new("RGB", (width, height), "#fbfbf7")
    draw = ImageDraw.Draw(image)
    title_font = load_font(48, bold=True)
    subtitle_font = load_font(25)
    axis_font = load_font(22)
    label_font = load_font(23, bold=True)

    draw.text((margin, 70), "DeepSeek-Balanced Speed-Quality Tradeoff", font=title_font, fill="#1f2328")
    draw.text((margin, 134), "DeepSeek-Balanced recovers speed while keeping CLIPScore close to original DeepSeek-PCAS.", font=subtitle_font, fill="#52616b")

    times = [float(rows[method]["avg_elapsed_seconds_no_warmup"]) for method in TRADEOFF_METHODS]
    scores = [float(rows[method]["avg_clip_score"]) for method in TRADEOFF_METHODS]
    x_min, x_max = min(times) - 0.08, max(times) + 0.08
    y_min, y_max = min(scores) - 0.08, max(scores) + 0.08
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

    for method in TRADEOFF_METHODS:
        row = rows[method]
        x_value = float(row["avg_elapsed_seconds_no_warmup"])
        y_value = float(row["avg_clip_score"])
        steps = float(row["avg_steps"])
        x = x0 + int((x_value - x_min) / (x_max - x_min) * (x1 - x0))
        y = y1 - int((y_value - y_min) / (y_max - y_min) * (y1 - y0))
        radius = int(24 + steps * 1.25)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=COLORS[method], outline="#1f2328", width=3)
        label = f"{METHOD_LABELS[method]}  {x_value:.3f}s / {y_value:.3f}"
        label_width = draw.textbbox((0, 0), label, font=label_font)[2]
        label_x = x + radius + 18
        if label_x + label_width > x1 - 12:
            label_x = x - radius - label_width - 18
        draw.text((label_x, y - 16), label, font=label_font, fill="#1f2328")

    draw.text((chart[0] + 470, height - 138), "Average time per image, no warm-up", font=axis_font, fill="#1f2328")
    draw.text((margin - 18, chart[1] - 42), "Avg CLIPScore", font=axis_font, fill="#1f2328")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def main() -> None:
    summary_rows = read_csv(Path("results/day3_deepseek_balanced_summary.csv"))
    clip_rows = read_csv(Path("results/day3_pcas_all_balanced_clipscore_summary.csv"))
    make_speed_chart(summary_rows, Path("results/figures/day3_deepseek_balanced_speed_chart.png"))
    make_tradeoff_chart(clip_rows, Path("results/figures/day3_deepseek_balanced_speed_quality_tradeoff.png"))
    print("Wrote DeepSeek-Balanced figures.")


if __name__ == "__main__":
    main()
