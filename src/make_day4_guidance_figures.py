from __future__ import annotations

import argparse
import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


GROUP_ORDER = ["all", "10_words", "30_words", "50_words"]
GROUP_LABELS = {
    "all": "All prompts",
    "10_words": "10-word prompts",
    "30_words": "30-word prompts",
    "50_words": "50-word prompts",
}
GROUP_COLORS = {
    "all": "#1f2328",
    "10_words": "#4c78a8",
    "30_words": "#2f6f73",
    "50_words": "#d9903d",
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


def read_summary(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def index_rows(rows: list[dict[str, str]]) -> dict[tuple[float, str], dict[str, str]]:
    return {(float(row["guidance_scale"]), row["prompt_length_group"]): row for row in rows}


def draw_guidance_clipscore_chart(rows: list[dict[str, str]], output_path: Path) -> None:
    index = index_rows(rows)
    guidance_values = sorted({float(row["guidance_scale"]) for row in rows})
    scores = [float(row["avg_clip_score"]) for row in rows]
    y_min = min(scores) - 0.35
    y_max = max(scores) + 0.35

    width, height = 2800, 1700
    margin = 130
    chart = (330, 320, width - 220, height - 300)
    image = Image.new("RGB", (width, height), "#fbfbf7")
    draw = ImageDraw.Draw(image)

    title_font = load_font(56, bold=True)
    subtitle_font = load_font(28)
    axis_font = load_font(24)
    label_font = load_font(25, bold=True)
    value_font = load_font(22)

    draw.text((margin, 82), "Day 4 Guidance Scale Ablation", font=title_font, fill="#1f2328")
    guidance_label = ", ".join(f"{value:.1f}" for value in guidance_values)
    draw.text((margin, 154), f"20-step SANA runs with guidance {guidance_label}; quality measured by CLIPScore.", font=subtitle_font, fill="#52616b")
    draw.text((margin, 196), "The normal 3.5-6.5 band is narrow; 1.5 and 8.5 stress-test low/high guidance behavior.", font=subtitle_font, fill="#52616b")

    x0, y0, x1, y1 = chart
    draw.line((x0, y1, x1, y1), fill="#27323a", width=3)
    draw.line((x0, y0, x0, y1), fill="#27323a", width=3)

    y_ticks = [round(y_min + (y_max - y_min) * i / 4, 1) for i in range(5)]
    for tick in y_ticks:
        y = y1 - int((tick - y_min) / (y_max - y_min) * (y1 - y0))
        draw.line((x0, y, x1, y), fill="#e0e5dd", width=2)
        draw.text((x0 - 82, y - 14), f"{tick:.1f}", font=axis_font, fill="#52616b")

    x_positions: dict[float, int] = {}
    for i, guidance in enumerate(guidance_values):
        x = x0 + int(i / (len(guidance_values) - 1) * (x1 - x0))
        x_positions[guidance] = x
        draw.line((x, y1, x, y1 + 12), fill="#27323a", width=3)
        draw.text((x - 32, y1 + 32), f"{guidance:.1f}", font=axis_font, fill="#1f2328")

    draw.text((x0 + 840, height - 200), "Guidance scale", font=axis_font, fill="#1f2328")
    draw.text((margin - 6, y0 - 48), "Avg CLIPScore", font=axis_font, fill="#1f2328")

    for group in GROUP_ORDER:
        points: list[tuple[int, int, float]] = []
        for guidance in guidance_values:
            score = float(index[(guidance, group)]["avg_clip_score"])
            x = x_positions[guidance]
            y = y1 - int((score - y_min) / (y_max - y_min) * (y1 - y0))
            points.append((x, y, score))
        for left, right in zip(points, points[1:]):
            draw.line((left[0], left[1], right[0], right[1]), fill=GROUP_COLORS[group], width=6)
        for x, y, score in points:
            radius = 15 if group != "all" else 19
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=GROUP_COLORS[group], outline="#fbfbf7", width=4)
            offset_y = -50 if group in {"all", "30_words"} else 20
            draw.text((x - 36, y + offset_y), f"{score:.2f}", font=value_font, fill=GROUP_COLORS[group])

    legend_x = margin
    legend_y = height - 130
    for group in GROUP_ORDER:
        draw.line((legend_x, legend_y + 18, legend_x + 58, legend_y + 18), fill=GROUP_COLORS[group], width=7)
        draw.ellipse((legend_x + 20, legend_y + 6, legend_x + 36, legend_y + 22), fill=GROUP_COLORS[group])
        draw.text((legend_x + 76, legend_y + 2), GROUP_LABELS[group], font=label_font, fill="#1f2328")
        legend_x += 560

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Day 4 guidance ablation figures.")
    parser.add_argument("--summary", default="results/day4_guidance_ablation_summary.csv")
    parser.add_argument("--figures-dir", default="results/figures")
    args = parser.parse_args()

    rows = read_summary(Path(args.summary))
    figures_dir = Path(args.figures_dir)
    draw_guidance_clipscore_chart(rows, figures_dir / "day4_guidance_ablation_clipscore.png")
    print(f"Wrote {figures_dir / 'day4_guidance_ablation_clipscore.png'}")


if __name__ == "__main__":
    main()
