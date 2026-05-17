from __future__ import annotations

import csv
import json
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def read_summary(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def fit_image(path: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    x = (size[0] - image.width) // 2
    y = (size[1] - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


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
) -> int:
    y = xy[1]
    for line in wrap_text(draw, text, font, max_width):
        draw.text((xy[0], y), line, font=font, fill=fill)
        y += line_height
    return y


def make_comparison_grid(base_rows: list[dict], lora_rows: list[dict], output_path: Path, title: str, lora_label: str) -> None:
    title_font = load_font(32, bold=True)
    header_font = load_font(23, bold=True)
    prompt_font = load_font(18)
    metric_font = load_font(17)

    thumb = 320
    margin = 44
    prompt_w = 430
    gutter = 24
    row_h = thumb + 54
    header_h = 120
    width = margin * 2 + prompt_w + gutter + thumb * 2 + gutter
    height = header_h + row_h * len(base_rows) + margin

    canvas = Image.new("RGB", (width, height), "#f7f7f4")
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 28), title, font=title_font, fill="#111111")
    draw.text((margin + prompt_w + gutter, 84), "Base", font=header_font, fill="#333333")
    draw.text((margin + prompt_w + gutter + thumb + gutter, 84), lora_label, font=header_font, fill="#333333")

    for i, (base, lora) in enumerate(zip(base_rows, lora_rows)):
        y = header_h + i * row_h
        draw.line((margin, y - 12, width - margin, y - 12), fill="#dddddd", width=1)
        draw.text((margin, y + 4), f"Prompt {i + 1}", font=header_font, fill="#111111")
        text_y = draw_wrapped_text(
            draw,
            base["prompt"],
            (margin, y + 42),
            prompt_font,
            "#333333",
            prompt_w,
            24,
        )
        draw.text((margin, text_y + 8), f"seed {base['seed']} | 20 steps | cfg 4.5", font=metric_font, fill="#666666")

        base_img = fit_image(Path(base["image_path"]), (thumb, thumb))
        lora_img = fit_image(Path(lora["image_path"]), (thumb, thumb))
        x_base = margin + prompt_w + gutter
        x_lora = x_base + thumb + gutter
        canvas.paste(base_img, (x_base, y))
        canvas.paste(lora_img, (x_lora, y))
        draw.rectangle((x_base, y, x_base + thumb, y + thumb), outline="#cccccc", width=1)
        draw.rectangle((x_lora, y, x_lora + thumb, y + thumb), outline="#cccccc", width=1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def make_similarity_chart(summary_rows: list[dict[str, str]], output_path: Path) -> None:
    title_font = load_font(30, bold=True)
    label_font = load_font(22, bold=True)
    small_font = load_font(18)

    width, height = 980, 560
    canvas = Image.new("RGB", (width, height), "#fbfaf7")
    draw = ImageDraw.Draw(canvas)
    draw.text((54, 36), "Day 5 LoRA Validation Metrics", font=title_font, fill="#111111")

    methods = [row["method"] for row in summary_rows]
    ref_values = [float(row["avg_reference_clip_similarity"]) for row in summary_rows]
    text_values = [float(row["avg_prompt_clipscore"]) for row in summary_rows]

    chart_x, chart_y = 100, 140
    chart_w, chart_h = 780, 300
    max_value = max(ref_values + text_values) + 2
    min_value = min(ref_values + text_values) - 2
    value_range = max_value - min_value
    colors = {"reference": "#287c72", "prompt": "#b85b38"}

    draw.rectangle((chart_x, chart_y, chart_x + chart_w, chart_y + chart_h), outline="#d6d1c8", width=2)
    for tick in range(5):
        value = min_value + value_range * tick / 4
        y = chart_y + chart_h - int((value - min_value) / value_range * chart_h)
        draw.line((chart_x, y, chart_x + chart_w, y), fill="#e5e0d8", width=1)
        draw.text((42, y - 11), f"{value:.1f}", font=small_font, fill="#666666")

    group_w = chart_w // len(methods)
    bar_w = 90
    for i, method in enumerate(methods):
        center = chart_x + group_w * i + group_w // 2
        for offset, value, key in [(-50, ref_values[i], "reference"), (50, text_values[i], "prompt")]:
            bar_h = int((value - min_value) / value_range * chart_h)
            x0 = center + offset - bar_w // 2
            y0 = chart_y + chart_h - bar_h
            draw.rectangle((x0, y0, x0 + bar_w, chart_y + chart_h), fill=colors[key])
            draw.text((x0 + 8, y0 - 28), f"{value:.2f}", font=small_font, fill="#111111")
        draw.text((center - 38, chart_y + chart_h + 22), method, font=label_font, fill="#111111")

    draw.rectangle((620, 55, 646, 81), fill=colors["reference"])
    draw.text((656, 56), "Reference image similarity", font=small_font, fill="#333333")
    draw.rectangle((620, 88, 646, 114), fill=colors["prompt"])
    draw.text((656, 89), "Prompt CLIPScore", font=small_font, fill="#333333")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Make Day 5 LoRA validation figures.")
    parser.add_argument("--base-summary", default="outputs/day5_lora_validation_base/summary.json")
    parser.add_argument("--lora-summary", default="outputs/day5_lora_validation_lora/summary.json")
    parser.add_argument("--metrics-summary", default="results/day5_lora_validation_summary.csv")
    parser.add_argument("--grid-output", default="results/figures/day5_lora_base_vs_lora_grid.png")
    parser.add_argument("--chart-output", default="results/figures/day5_lora_validation_metrics.png")
    parser.add_argument("--title", default="Day 5: Base SANA vs zzmearphone LoRA")
    parser.add_argument("--lora-label", default="LoRA")
    args = parser.parse_args()

    base_rows = read_summary(Path(args.base_summary))
    lora_rows = read_summary(Path(args.lora_summary))
    make_comparison_grid(base_rows, lora_rows, Path(args.grid_output), args.title, args.lora_label)

    summary_rows = read_csv(Path(args.metrics_summary))
    make_similarity_chart(summary_rows, Path(args.chart_output))
    print("Wrote Day 5 LoRA figures.")


if __name__ == "__main__":
    main()
