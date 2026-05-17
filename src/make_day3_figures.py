from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


GROUP_ORDER = ["all", "10_words", "30_words", "50_words"]


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


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_pcas_summary(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if width <= max_width:
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
    lines = wrap_text(draw, text, font, max_width)
    for offset, line in enumerate(lines):
        draw.text((xy[0], xy[1] + offset * line_height), line, font=font, fill=fill)
    return len(lines) * line_height


def fit_image(path: Path, size: int) -> Image.Image:
    image = Image.open(path).convert("RGB")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), "white")
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    return canvas


def make_time_chart(comparisons: list[dict], output_path: Path) -> None:
    rows = [row for row in comparisons if row["group"] in GROUP_ORDER]
    rows.sort(key=lambda row: GROUP_ORDER.index(row["group"]))

    width = 2600
    height = 1600
    margin = 120
    chart_x = 420
    chart_y = 330
    chart_width = width - chart_x - margin
    chart_height = 880
    image = Image.new("RGB", (width, height), "#fbfbf7")
    draw = ImageDraw.Draw(image)

    title_font = load_font(52, bold=True)
    subtitle_font = load_font(28)
    axis_font = load_font(25)
    label_font = load_font(27, bold=True)
    value_font = load_font(25)

    draw.text((margin, 82), "Day 3 PCAS vs Fixed-20", font=title_font, fill="#1f2328")
    draw.text((margin, 152), "Average inference time per image, no warm-up, 512x512 SANA-0.6B", font=subtitle_font, fill="#52616b")
    draw.text((margin, 194), "PCAS reallocates steps: 10-word prompts get 10 steps, 30-word prompts get 20 steps, 50-word prompts get 28 steps.", font=subtitle_font, fill="#52616b")

    max_value = max(
        max(float(row["pcas_time_no_warmup"]), float(row["fixed20_time_no_warmup"]))
        for row in rows
    )
    max_value *= 1.12
    for tick in range(6):
        value = max_value * tick / 5
        x = chart_x + int(chart_width * tick / 5)
        draw.line((x, chart_y, x, chart_y + chart_height), fill="#e0e5dd", width=2)
        draw.text((x - 26, chart_y + chart_height + 28), f"{value:.1f}s", font=axis_font, fill="#52616b")

    fixed_color = "#8a8f98"
    pcas_color = "#2f6f73"
    group_gap = 80
    bar_h = 58
    y = chart_y + 20
    for row in rows:
        group = row["group"]
        fixed_time = float(row["fixed20_time_no_warmup"])
        pcas_time = float(row["pcas_time_no_warmup"])
        fixed_w = int(chart_width * fixed_time / max_value)
        pcas_w = int(chart_width * pcas_time / max_value)
        draw.text((margin, y + 44), group, font=label_font, fill="#1f2328")
        draw.rounded_rectangle((chart_x, y, chart_x + fixed_w, y + bar_h), radius=10, fill=fixed_color)
        draw.rounded_rectangle((chart_x, y + bar_h + 12, chart_x + pcas_w, y + bar_h * 2 + 12), radius=10, fill=pcas_color)
        draw.text((chart_x + fixed_w + 20, y + 12), f"fixed-20 {fixed_time:.3f}s", font=value_font, fill="#1f2328")
        draw.text((chart_x + pcas_w + 20, y + bar_h + 24), f"PCAS {pcas_time:.3f}s", font=value_font, fill="#1f2328")
        draw.text(
            (chart_x, y + bar_h * 2 + 28),
            f"time saving vs fixed-20: {float(row['time_saving_percent_vs_fixed20']):.1f}% | step saving: {float(row['step_saving_percent_vs_fixed20']):.1f}%",
            font=axis_font,
            fill="#52616b",
        )
        y += bar_h * 2 + group_gap

    legend_y = height - 150
    draw.rounded_rectangle((margin, legend_y, margin + 40, legend_y + 40), radius=8, fill=fixed_color)
    draw.text((margin + 58, legend_y + 4), "Fixed-20", font=axis_font, fill="#1f2328")
    draw.rounded_rectangle((margin + 280, legend_y, margin + 320, legend_y + 40), radius=8, fill=pcas_color)
    draw.text((margin + 338, legend_y + 4), "PCAS", font=axis_font, fill="#1f2328")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def build_fixed20_index(day3_rows: list[dict]) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for row in day3_rows:
        if row["method"] == "fixed_20":
            index[row["prompt"]] = row
    return index


def grid_row_height(draw: ImageDraw.ImageDraw, prompt: str, prompt_font: ImageFont.ImageFont, prompt_width: int, thumb_size: int) -> int:
    lines = wrap_text(draw, prompt, prompt_font, prompt_width)
    text_height = 94 + len(lines) * 30
    return max(thumb_size + 36, text_height) + 24


def make_full_prompt_grid(day3_rows: list[dict], pcas_records: list[dict], output_path: Path) -> None:
    fixed_index = build_fixed20_index(day3_rows)
    margin = 56
    prompt_width = 1030
    thumb_size = 330
    metric_width = 330
    col_gap = 28
    header_height = 140
    row_gap = 30
    width = margin * 2 + prompt_width + thumb_size * 2 + metric_width + col_gap * 3

    title_font = load_font(42, bold=True)
    header_font = load_font(28, bold=True)
    prompt_font = load_font(24)
    meta_font = load_font(21)
    metric_font = load_font(23, bold=True)

    probe = Image.new("RGB", (width, 100), "white")
    probe_draw = ImageDraw.Draw(probe)
    row_heights = [grid_row_height(probe_draw, row["prompt"], prompt_font, prompt_width - 70, thumb_size) for row in pcas_records]
    height = margin * 2 + header_height + sum(row_heights) + row_gap * (len(pcas_records) - 1)

    image = Image.new("RGB", (width, height), "#f7f7f2")
    draw = ImageDraw.Draw(image)
    draw.text((margin, margin), "Day 3 PCAS vs Fixed-20: Full Prompt Comparison", font=title_font, fill="#1f2328")
    draw.text((margin, margin + 58), "Each prompt is shown in full. PCAS selects steps and guidance from the rule-based complexity policy.", font=meta_font, fill="#52616b")

    x_prompt = margin
    x_fixed = margin + prompt_width + col_gap
    x_pcas = x_fixed + thumb_size + col_gap
    x_metric = x_pcas + thumb_size + col_gap
    draw.text((x_fixed, margin + 88), "Fixed-20", font=header_font, fill="#1f2328")
    draw.text((x_pcas, margin + 88), "PCAS", font=header_font, fill="#1f2328")
    draw.text((x_metric, margin + 88), "PCAS Policy", font=header_font, fill="#1f2328")

    y = margin + header_height
    for index, pcas in enumerate(pcas_records, start=1):
        prompt = pcas["prompt"]
        fixed = fixed_index[prompt]
        row_height = row_heights[index - 1]
        fill = "#ffffff" if index % 2 else "#f0f2ee"
        draw.rounded_rectangle((margin - 18, y - 12, width - margin + 18, y + row_height - 12), radius=18, fill=fill, outline="#d8ded6", width=2)

        draw.text(
            (x_prompt, y + 8),
            f"{index:02d} | {pcas['complexity_label']} | {pcas['word_count']} words | score={float(pcas['complexity_score']):.3f}",
            font=metric_font,
            fill="#335c67",
        )
        draw_wrapped_text(draw, prompt, (x_prompt, y + 50), prompt_font, "#1f2328", prompt_width - 70, 30)

        fixed_tile = fit_image(Path(fixed["image_path"]), thumb_size)
        pcas_tile = fit_image(Path(pcas["image_path"]), thumb_size)
        image.paste(fixed_tile, (x_fixed, y + 8))
        image.paste(pcas_tile, (x_pcas, y + 8))
        draw.rectangle((x_fixed, y + 8, x_fixed + thumb_size, y + 8 + thumb_size), outline="#bcc6b8", width=2)
        draw.rectangle((x_pcas, y + 8, x_pcas + thumb_size, y + 8 + thumb_size), outline="#bcc6b8", width=2)

        metric_lines = [
            f"steps: {pcas['selected_steps']}",
            f"guidance: {float(pcas['selected_guidance_scale']):.1f}",
            f"time: {float(pcas['elapsed_seconds']):.3f}s",
            f"fixed20: {float(fixed['elapsed_seconds']):.3f}s",
        ]
        for offset, line in enumerate(metric_lines):
            draw.text((x_metric, y + 22 + offset * 42), line, font=metric_font, fill="#1f2328")
        y += row_height + row_gap

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Day 3 PCAS figures.")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--pcas-summary", default="outputs/day3_pcas/summary.json")
    parser.add_argument("--figures-dir", default="results/figures")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    figures_dir = Path(args.figures_dir)
    comparisons = read_csv(results_dir / "day3_pcas_vs_fixed20.csv")
    day3_rows = read_csv(results_dir / "day3_pcas_results.csv")
    pcas_records = read_pcas_summary(Path(args.pcas_summary))

    make_time_chart(comparisons, figures_dir / "day3_pcas_vs_fixed20_chart.png")
    make_full_prompt_grid(day3_rows, pcas_records, figures_dir / "day3_pcas_vs_fixed20_full_prompts.png")

    print(f"Wrote {figures_dir / 'day3_pcas_vs_fixed20_chart.png'}")
    print(f"Wrote {figures_dir / 'day3_pcas_vs_fixed20_full_prompts.png'}")


if __name__ == "__main__":
    main()
