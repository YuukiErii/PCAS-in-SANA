from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


METHODS = [
    ("fixed_10", 10, "10 steps"),
    ("fixed_20", 20, "20 steps"),
    ("fixed_28", 28, "28 steps"),
]

PROMPT_GROUPS = [
    ("10_words", 10, "day2_10word_prompts.txt"),
    ("30_words", 30, "day2_30word_prompts.txt"),
    ("50_words", 50, "day2_50word_prompts.txt"),
]


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


def read_prompts(prompt_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for label, target_words, filename in PROMPT_GROUPS:
        path = prompt_dir / filename
        for line in path.read_text(encoding="utf-8").splitlines():
            prompt = line.strip()
            if prompt and not prompt.startswith("#"):
                rows.append(
                    {
                        "prompt_length_group": label,
                        "target_words": target_words,
                        "actual_words": len(prompt.split()),
                        "prompt": prompt,
                    }
                )
    return rows


def load_image_index(outputs_dir: Path) -> dict[tuple[int, str], Path]:
    index: dict[tuple[int, str], Path] = {}
    for _, steps, _ in METHODS:
        summary_path = outputs_dir / f"day2_baseline_{steps}steps" / "summary.json"
        records = json.loads(summary_path.read_text(encoding="utf-8"))
        for record in records:
            index[(steps, record["prompt"])] = Path(record["image_path"])
    return index


def load_speed_summary(results_dir: Path) -> list[dict]:
    path = results_dir / "day2_speed_summary.csv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def fit_image(path: Path, size: int) -> Image.Image:
    image = Image.open(path).convert("RGB")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), "white")
    x = (size - image.width) // 2
    y = (size - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


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


def grid_row_height(draw: ImageDraw.ImageDraw, prompt: str, prompt_font: ImageFont.ImageFont, prompt_width: int, thumb_size: int) -> int:
    lines = wrap_text(draw, prompt, prompt_font, prompt_width)
    text_height = 38 + len(lines) * 30
    return max(thumb_size + 34, text_height) + 24


def make_full_prompt_grid(
    prompts: list[dict],
    image_index: dict[tuple[int, str], Path],
    output_path: Path,
    title: str,
    thumb_size: int = 360,
) -> None:
    margin = 56
    prompt_width = 1120
    col_gap = 28
    row_gap = 30
    header_height = 124
    width = margin * 2 + prompt_width + len(METHODS) * thumb_size + (len(METHODS) - 1) * col_gap

    title_font = load_font(42, bold=True)
    header_font = load_font(30, bold=True)
    label_font = load_font(25, bold=True)
    prompt_font = load_font(24)
    meta_font = load_font(21)
    probe = Image.new("RGB", (width, 100), "white")
    probe_draw = ImageDraw.Draw(probe)
    row_heights = [grid_row_height(probe_draw, row["prompt"], prompt_font, prompt_width - 80, thumb_size) for row in prompts]
    height = margin * 2 + header_height + sum(row_heights) + row_gap * (len(prompts) - 1)

    image = Image.new("RGB", (width, height), "#f7f7f2")
    draw = ImageDraw.Draw(image)
    draw.text((margin, margin), title, font=title_font, fill="#1f2328")
    draw.text((margin, margin + 58), "Full prompts are shown without truncation.", font=meta_font, fill="#52616b")

    x0 = margin + prompt_width
    for col, (_, _, label) in enumerate(METHODS):
        x = x0 + col * (thumb_size + col_gap)
        draw.text((x, margin + 78), label, font=header_font, fill="#1f2328")

    y = margin + header_height
    for index, row in enumerate(prompts, start=1):
        row_height = row_heights[index - 1]
        group = row["prompt_length_group"]
        target_words = row["target_words"]
        prompt = row["prompt"]

        fill = "#ffffff" if index % 2 else "#f0f2ee"
        draw.rounded_rectangle((margin - 18, y - 12, width - margin + 18, y + row_height - 12), radius=18, fill=fill, outline="#d8ded6", width=2)
        draw.text((margin, y + 8), f"{index:02d} | {group} | target={target_words} words", font=label_font, fill="#335c67")
        draw_wrapped_text(draw, prompt, (margin, y + 48), prompt_font, "#1f2328", prompt_width - 80, 30)

        for col, (_, steps, _) in enumerate(METHODS):
            x = x0 + col * (thumb_size + col_gap)
            tile = fit_image(image_index[(steps, prompt)], thumb_size)
            image.paste(tile, (x, y + 8))
            draw.rectangle((x, y + 8, x + thumb_size, y + 8 + thumb_size), outline="#bcc6b8", width=2)
        y += row_height + row_gap

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def make_speed_chart(summary_rows: list[dict], output_path: Path) -> None:
    rows = [
        row
        for row in summary_rows
        if row["prompt_length_group"] in {"10_words", "30_words", "50_words"}
    ]
    rows.sort(key=lambda row: (int(row["steps"]), int(float(row["avg_words"]))))

    width = 2400
    height = 1500
    margin = 120
    chart_x = 460
    chart_y = 260
    chart_width = width - chart_x - margin
    chart_height = height - chart_y - 180
    image = Image.new("RGB", (width, height), "#fbfbf7")
    draw = ImageDraw.Draw(image)
    title_font = load_font(48, bold=True)
    axis_font = load_font(26)
    label_font = load_font(25, bold=True)
    value_font = load_font(24)

    draw.text((margin, 84), "Day 2 Fixed-Step Baseline Speed by Prompt Length", font=title_font, fill="#1f2328")
    draw.text((margin, 148), "512x512 SANA-0.6B, average seconds per image, no warm-up", font=axis_font, fill="#52616b")

    max_value = max(float(row["avg_elapsed_seconds_no_warmup"]) for row in rows)
    tick_count = 6
    for tick in range(tick_count + 1):
        value = max_value * tick / tick_count
        x = chart_x + int(chart_width * tick / tick_count)
        draw.line((x, chart_y, x, chart_y + chart_height), fill="#e0e5dd", width=2)
        draw.text((x - 24, chart_y + chart_height + 24), f"{value:.1f}", font=axis_font, fill="#52616b")

    colors = {"10_words": "#2f6f73", "30_words": "#d9903d", "50_words": "#7f5f9f"}
    bar_h = 44
    row_gap = 26
    y = chart_y + 20
    for row in rows:
        group = row["prompt_length_group"]
        label = f"{row['method']} | {group}"
        value = float(row["avg_elapsed_seconds_no_warmup"])
        bar_w = int(chart_width * value / max_value)
        draw.text((margin, y + 6), label, font=label_font, fill="#1f2328")
        draw.rounded_rectangle((chart_x, y, chart_x + bar_w, y + bar_h), radius=8, fill=colors[group])
        draw.text((chart_x + bar_w + 18, y + 6), f"{value:.3f}s", font=value_font, fill="#1f2328")
        y += bar_h + row_gap

    legend_x = margin
    legend_y = height - 130
    for group, color in colors.items():
        draw.rounded_rectangle((legend_x, legend_y, legend_x + 38, legend_y + 38), radius=7, fill=color)
        draw.text((legend_x + 52, legend_y + 3), group, font=axis_font, fill="#1f2328")
        legend_x += 260

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create high-resolution Day 2 summary figures.")
    parser.add_argument("--outputs-dir", default="outputs")
    parser.add_argument("--prompts-dir", default="prompts")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--figures-dir", default="results/figures")
    args = parser.parse_args()

    outputs_dir = Path(args.outputs_dir)
    prompts = read_prompts(Path(args.prompts_dir))
    image_index = load_image_index(outputs_dir)
    figures_dir = Path(args.figures_dir)
    summary_rows = load_speed_summary(Path(args.results_dir))

    make_full_prompt_grid(
        prompts,
        image_index,
        figures_dir / "day2_baseline_grid_full_prompts.png",
        "Day 2 SANA Fixed-Step Baselines: 10 / 30 / 50 Word Prompts",
    )
    for group, _, _ in PROMPT_GROUPS:
        subset = [row for row in prompts if row["prompt_length_group"] == group]
        make_full_prompt_grid(
            subset,
            image_index,
            figures_dir / f"day2_baseline_grid_{group}_full_prompts.png",
            f"Day 2 SANA Baselines: {group} Prompts",
        )
    make_speed_chart(summary_rows, figures_dir / "day2_speed_summary_chart.png")

    print(f"Wrote {figures_dir / 'day2_baseline_grid_full_prompts.png'}")
    print(f"Wrote {figures_dir / 'day2_baseline_grid_10_words_full_prompts.png'}")
    print(f"Wrote {figures_dir / 'day2_baseline_grid_30_words_full_prompts.png'}")
    print(f"Wrote {figures_dir / 'day2_baseline_grid_50_words_full_prompts.png'}")
    print(f"Wrote {figures_dir / 'day2_speed_summary_chart.png'}")


if __name__ == "__main__":
    main()
