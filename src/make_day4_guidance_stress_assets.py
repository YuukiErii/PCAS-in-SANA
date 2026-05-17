from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SUMMARY_PATH = Path("results/day4_guidance_ablation_summary.csv")
DETAIL_PATH = Path("results/day4_guidance_ablation_results.csv")
ANALYSIS_CSV = Path("results/day4_guidance_stress_analysis.csv")
ANALYSIS_MD = Path("results/day4_guidance_stress_analysis.md")
GRID_PATH = Path("results/figures/day4_guidance_stress_qualitative_grid.png")

GUIDANCE_VALUES = [1.5, 3.5, 4.5, 5.5, 6.5, 8.5]
GRID_PROMPTS = [1, 11, 18, 21, 26, 30]


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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
    for i, line in enumerate(wrap_text(draw, text, font, max_width)[:max_lines]):
        draw.text((xy[0], xy[1] + i * line_height), line, font=font, fill=fill)


def fit_image(path: Path, size: int) -> Image.Image:
    image = Image.open(path).convert("RGB")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), "white")
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    return canvas


def summary_index(rows: list[dict[str, str]]) -> dict[tuple[float, str], dict[str, str]]:
    return {(float(row["guidance_scale"]), row["prompt_length_group"]): row for row in rows}


def detail_index(rows: list[dict[str, str]]) -> dict[tuple[float, int], dict[str, str]]:
    return {(float(row["guidance_scale"]), int(row["prompt_index"])): row for row in rows}


def build_analysis(summary_rows: list[dict[str, str]]) -> list[dict]:
    index = summary_index(summary_rows)
    groups = ["all", "10_words", "30_words", "50_words"]
    rows: list[dict] = []
    for group in groups:
        baseline = float(index[(4.5, group)]["avg_clip_score"])
        normal_scores = [float(index[(guidance, group)]["avg_clip_score"]) for guidance in [3.5, 4.5, 5.5, 6.5]]
        full_scores = [float(index[(guidance, group)]["avg_clip_score"]) for guidance in GUIDANCE_VALUES]
        best_guidance = max(GUIDANCE_VALUES, key=lambda guidance: float(index[(guidance, group)]["avg_clip_score"]))
        worst_guidance = min(GUIDANCE_VALUES, key=lambda guidance: float(index[(guidance, group)]["avg_clip_score"]))
        rows.append(
            {
                "prompt_length_group": group,
                "clipscore_at_4_5": f"{baseline:.3f}",
                "clipscore_at_1_5": f"{float(index[(1.5, group)]['avg_clip_score']):.3f}",
                "delta_1_5_vs_4_5": f"{float(index[(1.5, group)]['avg_clip_score']) - baseline:.3f}",
                "clipscore_at_8_5": f"{float(index[(8.5, group)]['avg_clip_score']):.3f}",
                "delta_8_5_vs_4_5": f"{float(index[(8.5, group)]['avg_clip_score']) - baseline:.3f}",
                "normal_band_range_3_5_to_6_5": f"{max(normal_scores) - min(normal_scores):.3f}",
                "full_range_1_5_to_8_5": f"{max(full_scores) - min(full_scores):.3f}",
                "best_guidance_by_clipscore": f"{best_guidance:.1f}",
                "worst_guidance_by_clipscore": f"{worst_guidance:.1f}",
            }
        )
    return rows


def draw_centered(draw: ImageDraw.ImageDraw, x: int, y: int, width: int, text: str, font: ImageFont.ImageFont, fill: str) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((x + (width - (bbox[2] - bbox[0])) // 2, y), text, font=font, fill=fill)


def make_grid(detail_rows: list[dict[str, str]], output_path: Path) -> None:
    index = detail_index(detail_rows)
    title_font = load_font(34, bold=True)
    subtitle_font = load_font(18)
    header_font = load_font(16, bold=True)
    prompt_font = load_font(13)
    meta_font = load_font(12)

    margin = 28
    prompt_w = 300
    thumb = 150
    gap = 14
    header_h = 118
    row_h = 190
    width = margin * 2 + prompt_w + gap + len(GUIDANCE_VALUES) * thumb + (len(GUIDANCE_VALUES) - 1) * gap
    height = margin * 2 + header_h + len(GRID_PROMPTS) * row_h

    image = Image.new("RGB", (width, height), "#fbfaf6")
    draw = ImageDraw.Draw(image)
    draw.text((margin, 24), "Day 4 Guidance Stress-Test Qualitative Grid", font=title_font, fill="#202428")
    draw.text(
        (margin, 68),
        "Low guidance weakens prompt binding; the normal band is visually similar; high guidance can increase CLIPScore without proving better visual quality.",
        font=subtitle_font,
        fill="#50606a",
    )

    x0 = margin + prompt_w + gap
    for col_i, guidance in enumerate(GUIDANCE_VALUES):
        draw_centered(draw, x0 + col_i * (thumb + gap), 100, thumb, f"g={guidance:.1f}", header_font, "#202428")

    y = margin + header_h
    for row_i, prompt_index in enumerate(GRID_PROMPTS):
        fill = "#ffffff" if row_i % 2 == 0 else "#f0f2ee"
        draw.rounded_rectangle((margin - 10, y - 10, width - margin + 10, y + row_h - 14), radius=10, fill=fill, outline="#d8ddd4")
        prompt = index[(4.5, prompt_index)]["prompt"]
        group = index[(4.5, prompt_index)]["prompt_length_group"]
        draw.text((margin, y + 2), f"Prompt {prompt_index} ({group})", font=header_font, fill="#202428")
        draw_wrapped_text(draw, prompt, (margin, y + 30), prompt_font, "#343a40", prompt_w - 18, 17, max_lines=7)

        for col_i, guidance in enumerate(GUIDANCE_VALUES):
            row = index[(guidance, prompt_index)]
            x = x0 + col_i * (thumb + gap)
            tile = fit_image(Path(row["image_path"]), thumb)
            image.paste(tile, (x, y + 6))
            draw.rectangle((x, y + 6, x + thumb, y + 6 + thumb), outline="#b7c0b4")
            draw.text((x, y + thumb + 14), f"CLIP {float(row['clip_score']):.2f}", font=meta_font, fill="#52616b")
        y += row_h

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def write_markdown(rows: list[dict]) -> None:
    all_row = next(row for row in rows if row["prompt_length_group"] == "all")
    lines = [
        "# Day 4 Guidance Stress-Test Analysis",
        "",
        "The original guidance ablation only covered 3.5-6.5, where CLIPScore changes were small. This expanded analysis adds guidance 1.5 and 8.5 to separate normal-band robustness from low/high stress behavior.",
        "",
        "| Group | CLIP@4.5 | 1.5 delta | 8.5 delta | Normal-band range | Full range | Best guidance |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {group} | {base} | {low_delta} | {high_delta} | {normal_range} | {full_range} | {best} |".format(
                group=row["prompt_length_group"],
                base=row["clipscore_at_4_5"],
                low_delta=row["delta_1_5_vs_4_5"],
                high_delta=row["delta_8_5_vs_4_5"],
                normal_range=row["normal_band_range_3_5_to_6_5"],
                full_range=row["full_range_1_5_to_8_5"],
                best=row["best_guidance_by_clipscore"],
            )
        )
    lines.extend(
        [
            "",
            "Key finding:",
            "",
            f"- On all prompts, guidance 1.5 is {all_row['delta_1_5_vs_4_5']} CLIPScore points below guidance 4.5, so too-low guidance weakens prompt-image alignment.",
            f"- The normal 3.5-6.5 band has only {all_row['normal_band_range_3_5_to_6_5']} CLIPScore range on all prompts, so the original ablation was expected to look flat.",
            f"- Guidance 8.5 is {all_row['delta_8_5_vs_4_5']} above guidance 4.5 on all prompts, but the gain is small enough that it should be reported as a high-guidance CLIPScore preference, not a proven visual-quality improvement.",
            "- Recommended report wording: SANA-0.6B is robust to moderate guidance changes; avoid very low guidance; keep 4.5 as the default for fair comparison, or use 6.5-8.5 only as an optional higher-alignment setting with qualitative inspection.",
            "",
            "Files:",
            "",
            f"- Stress-test table: `{ANALYSIS_CSV}`",
            f"- Qualitative grid: `{GRID_PATH}`",
        ]
    )
    ANALYSIS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    summary_rows = read_csv(SUMMARY_PATH)
    detail_rows = read_csv(DETAIL_PATH)
    analysis_rows = build_analysis(summary_rows)
    write_csv(
        ANALYSIS_CSV,
        analysis_rows,
        [
            "prompt_length_group",
            "clipscore_at_4_5",
            "clipscore_at_1_5",
            "delta_1_5_vs_4_5",
            "clipscore_at_8_5",
            "delta_8_5_vs_4_5",
            "normal_band_range_3_5_to_6_5",
            "full_range_1_5_to_8_5",
            "best_guidance_by_clipscore",
            "worst_guidance_by_clipscore",
        ],
    )
    make_grid(detail_rows, GRID_PATH)
    write_markdown(analysis_rows)
    print("Wrote Day 4 guidance stress-test assets.")


if __name__ == "__main__":
    main()
