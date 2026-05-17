from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


GROUP_ORDER = ["all", "10_words", "30_words", "50_words"]
METHODS = ["fixed_20", "rule_pcas_7_2", "deepseek_pcas_7_3"]
METHOD_LABELS = {
    "fixed_20": "Fixed-20",
    "rule_pcas_7_2": "Rule-PCAS 7.2",
    "deepseek_pcas_7_3": "DeepSeek-PCAS 7.3",
}
COLORS = {
    "fixed_20": "#8a8f98",
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


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
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


def draw_wrapped_text(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], font: ImageFont.ImageFont, fill: str, max_width: int, line_height: int) -> int:
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


def make_time_step_chart(summary_rows: list[dict], output_path: Path) -> None:
    index = {(row["method"], row["prompt_length_group"]): row for row in summary_rows}
    width = 2800
    height = 1800
    margin = 120
    title_font = load_font(54, bold=True)
    subtitle_font = load_font(28)
    axis_font = load_font(24)
    label_font = load_font(26, bold=True)
    value_font = load_font(23)
    image = Image.new("RGB", (width, height), "#fbfbf7")
    draw = ImageDraw.Draw(image)

    draw.text((margin, 78), "Day 3: Rule-PCAS 7.2 vs DeepSeek-PCAS 7.3", font=title_font, fill="#1f2328")
    draw.text((margin, 148), "No-warm-up runtime and average denoising steps by prompt length group", font=subtitle_font, fill="#52616b")
    draw.text((margin, 190), "DeepSeek is semantic and more conservative; it assigns higher steps to prompts with objects, relations, style, or text constraints.", font=subtitle_font, fill="#52616b")

    chart_x = 500
    chart_y = 310
    chart_width = width - chart_x - margin
    row_h = 88
    row_gap = 58
    max_time = max(float(index[(method, group)]["avg_elapsed_seconds_no_warmup"]) for method in METHODS for group in GROUP_ORDER)
    max_steps = max(float(index[(method, group)]["avg_steps"]) for method in METHODS for group in GROUP_ORDER)

    y = chart_y
    for group in GROUP_ORDER:
        draw.text((margin, y + 72), group, font=label_font, fill="#1f2328")
        for method_index, method in enumerate(METHODS):
            row = index[(method, group)]
            time_value = float(row["avg_elapsed_seconds_no_warmup"])
            step_value = float(row["avg_steps"])
            bar_y = y + method_index * row_h
            time_w = int(chart_width * time_value / (max_time * 1.15))
            step_marker_x = chart_x + int(chart_width * step_value / (max_steps * 1.15))
            draw.rounded_rectangle((chart_x, bar_y, chart_x + time_w, bar_y + 38), radius=8, fill=COLORS[method])
            draw.line((step_marker_x, bar_y - 4, step_marker_x, bar_y + 48), fill="#1f2328", width=4)
            draw.text((chart_x + time_w + 18, bar_y + 3), f"{METHOD_LABELS[method]}  {time_value:.3f}s  |  {step_value:.1f} steps", font=value_font, fill="#1f2328")
        y += row_h * len(METHODS) + row_gap

    legend_y = height - 150
    x = margin
    for method in METHODS:
        draw.rounded_rectangle((x, legend_y, x + 40, legend_y + 40), radius=8, fill=COLORS[method])
        draw.text((x + 58, legend_y + 4), METHOD_LABELS[method], font=axis_font, fill="#1f2328")
        x += 420
    draw.text((x + 40, legend_y + 4), "black tick = average steps", font=axis_font, fill="#1f2328")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def row_height(draw: ImageDraw.ImageDraw, prompt: str, prompt_font: ImageFont.ImageFont, prompt_width: int, thumb_size: int) -> int:
    lines = wrap_text(draw, prompt, prompt_font, prompt_width)
    return max(thumb_size + 44, 110 + len(lines) * 30) + 24


def fixed20_index(rows: list[dict]) -> dict[str, dict]:
    return {row["prompt"]: row for row in rows if row["method"] == "fixed_20"}


def make_full_grid(rows: list[dict], rule_records: list[dict], deepseek_records: list[dict], output_path: Path) -> None:
    fixed = fixed20_index(rows)
    rule = {row["prompt"]: row for row in rule_records}
    deepseek = {row["prompt"]: row for row in deepseek_records}

    margin = 56
    prompt_width = 950
    thumb_size = 300
    metric_width = 430
    col_gap = 24
    header_height = 142
    row_gap = 28
    width = margin * 2 + prompt_width + thumb_size * 3 + metric_width + col_gap * 4

    title_font = load_font(42, bold=True)
    header_font = load_font(27, bold=True)
    prompt_font = load_font(23)
    meta_font = load_font(20)
    metric_font = load_font(22, bold=True)

    probe = Image.new("RGB", (width, 100), "white")
    probe_draw = ImageDraw.Draw(probe)
    row_heights = [row_height(probe_draw, row["prompt"], prompt_font, prompt_width - 60, thumb_size) for row in rule_records]
    height = margin * 2 + header_height + sum(row_heights) + row_gap * (len(row_heights) - 1)
    image = Image.new("RGB", (width, height), "#f7f7f2")
    draw = ImageDraw.Draw(image)

    draw.text((margin, margin), "Day 3 Full Prompt Grid: Fixed-20 vs 7.2 vs 7.3", font=title_font, fill="#1f2328")
    draw.text((margin, margin + 58), "Full prompts are shown without truncation. DeepSeek-PCAS uses semantic JSON analysis from the cached API output.", font=meta_font, fill="#52616b")

    x_prompt = margin
    x_fixed = margin + prompt_width + col_gap
    x_rule = x_fixed + thumb_size + col_gap
    x_deepseek = x_rule + thumb_size + col_gap
    x_metric = x_deepseek + thumb_size + col_gap
    for x, label in [(x_fixed, "Fixed-20"), (x_rule, "Rule 7.2"), (x_deepseek, "DeepSeek 7.3"), (x_metric, "Policy")]:
        draw.text((x, margin + 88), label, font=header_font, fill="#1f2328")

    y = margin + header_height
    for index, rule_row in enumerate(rule_records, start=1):
        prompt = rule_row["prompt"]
        fixed_row = fixed[prompt]
        deep_row = deepseek[prompt]
        h = row_heights[index - 1]
        fill = "#ffffff" if index % 2 else "#f0f2ee"
        draw.rounded_rectangle((margin - 18, y - 12, width - margin + 18, y + h - 12), radius=18, fill=fill, outline="#d8ded6", width=2)
        draw.text((x_prompt, y + 8), f"{index:02d} | {rule_row['word_count']} words", font=metric_font, fill="#335c67")
        draw_wrapped_text(draw, prompt, (x_prompt, y + 48), prompt_font, "#1f2328", prompt_width - 60, 30)

        for x, path in [
            (x_fixed, Path(fixed_row["image_path"])),
            (x_rule, Path(rule_row["image_path"])),
            (x_deepseek, Path(deep_row["image_path"])),
        ]:
            tile = fit_image(path, thumb_size)
            image.paste(tile, (x, y + 8))
            draw.rectangle((x, y + 8, x + thumb_size, y + 8 + thumb_size), outline="#bcc6b8", width=2)

        metric_lines = [
            f"Rule: {rule_row['complexity_label']} | {rule_row['selected_steps']} steps",
            f"DS: {deep_row['complexity']} | {deep_row['selected_steps']} steps",
            f"DS objects: {deep_row['num_objects']}",
            f"DS relations: {deep_row['num_relations']}",
            f"DS style: {deep_row['style_constraints']}",
        ]
        for offset, line in enumerate(metric_lines):
            draw.text((x_metric, y + 18 + offset * 38), line, font=metric_font, fill="#1f2328")
        y += h + row_gap

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create figures comparing 7.2 Rule-PCAS and 7.3 DeepSeek-PCAS.")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--rule-pcas-summary", default="outputs/day3_pcas/summary.json")
    parser.add_argument("--deepseek-pcas-summary", default="outputs/day3_pcas_deepseek/summary.json")
    parser.add_argument("--figures-dir", default="results/figures")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    figures_dir = Path(args.figures_dir)
    summary_rows = read_csv(results_dir / "day3_7_2_7_3_summary.csv")
    result_rows = read_csv(results_dir / "day3_7_2_7_3_results.csv")
    rule_records = read_json(Path(args.rule_pcas_summary))
    deepseek_records = read_json(Path(args.deepseek_pcas_summary))

    make_time_step_chart(summary_rows, figures_dir / "day3_7_2_vs_7_3_time_steps_chart.png")
    make_full_grid(result_rows, rule_records, deepseek_records, figures_dir / "day3_7_2_vs_7_3_full_prompts.png")

    print(f"Wrote {figures_dir / 'day3_7_2_vs_7_3_time_steps_chart.png'}")
    print(f"Wrote {figures_dir / 'day3_7_2_vs_7_3_full_prompts.png'}")


if __name__ == "__main__":
    main()
