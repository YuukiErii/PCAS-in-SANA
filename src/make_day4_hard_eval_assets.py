from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean

from PIL import Image, ImageDraw, ImageFont


HARD_PROMPT_INDICES = [18, 19, 21, 22, 23, 26, 28, 30]
METHODS = [
    "fixed_20",
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
def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
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


def row_index(rows: list[dict[str, str]]) -> dict[tuple[str, int], dict[str, str]]:
    return {(row["method"], int(row["prompt_index"])): row for row in rows}


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
    max_lines: int | None = None,
) -> int:
    lines = wrap_text(draw, text, font, max_width)
    if max_lines is not None:
        lines = lines[:max_lines]
    y = xy[1]
    for line in lines:
        draw.text((xy[0], y), line, font=font, fill=fill)
        y += line_height
    return y


def fit_image(path: Path, size: int) -> Image.Image:
    image = Image.open(path).convert("RGB")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), "white")
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    return canvas


def hard_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row["method"] in METHODS and int(row["prompt_index"]) in HARD_PROMPT_INDICES
    ]


def summarize_clipscore(rows: list[dict[str, str]]) -> list[dict]:
    result: list[dict] = []
    for method in METHODS:
        method_rows = [row for row in rows if row["method"] == method]
        no_warmup = [row for row in method_rows if row["is_first_prompt"].lower() != "true"]
        elapsed_rows = no_warmup if no_warmup else method_rows
        result.append(
            {
                "method": method,
                "num_images": len(method_rows),
                "avg_steps": mean(float(row["selected_steps"]) for row in method_rows),
                "avg_time_no_warmup": mean(float(row["elapsed_seconds"]) for row in elapsed_rows),
                "avg_clip_score": mean(float(row["clip_score"]) for row in method_rows),
                "min_clip_score": min(float(row["clip_score"]) for row in method_rows),
                "max_clip_score": max(float(row["clip_score"]) for row in method_rows),
            }
        )
    return result


def make_grid(rows: list[dict[str, str]], output_path: Path) -> None:
    index = row_index(rows)
    title_font = load_font(34, bold=True)
    subtitle_font = load_font(20)
    header_font = load_font(20, bold=True)
    prompt_font = load_font(16)
    meta_font = load_font(14)

    margin = 34
    prompt_w = 420
    thumb = 210
    gap = 16
    header_h = 122
    row_h = 290
    width = margin * 2 + prompt_w + gap + len(METHODS) * thumb + (len(METHODS) - 1) * gap
    height = margin * 2 + header_h + len(HARD_PROMPT_INDICES) * row_h

    image = Image.new("RGB", (width, height), "#f8f8f4")
    draw = ImageDraw.Draw(image)
    draw.text((margin, 26), "Day 4 Hard Prompt Qualitative Evaluation", font=title_font, fill="#1f2328")
    draw.text(
        (margin, 70),
        "Hard subset for visual tie analysis: multi-object scenes, relations, text rendering, and dense composition.",
        font=subtitle_font,
        fill="#52616b",
    )

    x0 = margin + prompt_w + gap
    for i, method in enumerate(METHODS):
        draw.text((x0 + i * (thumb + gap), 102), METHOD_LABELS[method], font=header_font, fill="#1f2328")

    y = margin + header_h
    for row_i, prompt_index in enumerate(HARD_PROMPT_INDICES):
        fill = "#ffffff" if row_i % 2 == 0 else "#f0f2ee"
        draw.rounded_rectangle((margin - 12, y - 10, width - margin + 12, y + row_h - 22), radius=14, fill=fill, outline="#d8ded6", width=1)

        prompt = index[(METHODS[0], prompt_index)]["prompt"]
        draw.text((margin, y + 8), f"Prompt {prompt_index}", font=header_font, fill="#1f2328")
        draw_wrapped_text(draw, prompt, (margin, y + 38), prompt_font, "#333333", prompt_w - 18, 21, max_lines=7)

        for col_i, method in enumerate(METHODS):
            row = index[(method, prompt_index)]
            x = x0 + col_i * (thumb + gap)
            tile = fit_image(Path(row["image_path"]), thumb)
            image.paste(tile, (x, y + 8))
            draw.rectangle((x, y + 8, x + thumb, y + 8 + thumb), outline="#bcc6b8", width=1)
            meta = f"{float(row['selected_steps']):.0f} steps | CLIP {float(row['clip_score']):.2f}"
            draw.text((x, y + thumb + 18), meta, font=meta_font, fill="#52616b")
        y += row_h

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=95)


def write_report_draft(path: Path, summary_rows: list[dict]) -> None:
    lines = [
        "# DAY4 补充：Hard Prompt 定性评价与视觉打平结论",
        "",
        "## 动机",
        "",
        "DAY4 的 CLIPScore 结果显示，各种采样策略的平均文本-图像对齐分数非常接近。进一步观察 hard prompt 对照图后，不同策略在语义内容、主体完整性和整体构图上也很难分出稳定优劣。因此本项目不再强行加入人工 1-5 分评分，而是把“多数结果视觉上基本打平”作为更稳妥的定性结论。",
        "",
        "## Hard Prompt 子集",
        "",
        "本子集从原 30 条 benchmark 中选出 8 条更困难的 prompt，覆盖复杂场景、多主体、多关系、文字生成和密集构图。对应 prompt index 为：18、19、21、22、23、26、28、30。",
        "",
        "比较方法包括 Fixed-20、Fixed-28、Rule-PCAS、Balanced-PCAS 和 DeepSeek-Balanced。",
        "",
        "## Hard Subset CLIPScore",
        "",
        "| Method | Images | Avg steps | Avg time no-warmup | Avg CLIPScore |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            "| {method} | {n} | {steps:.3f} | {time:.3f}s | {score:.3f} |".format(
                method=row["method"],
                n=row["num_images"],
                steps=float(row["avg_steps"]),
                time=float(row["avg_time_no_warmup"]),
                score=float(row["avg_clip_score"]),
            )
        )
    lines.extend(
        [
            "",
            "从 hard subset 的自动指标看，各方法仍然处在很窄的 CLIPScore 区间内。结合对照图观察，差异主要体现在纹理、光照、边缘和局部小物体细节，而不是语义、构图或关系表达的明显改善。",
            "",
            "## 结论写法",
            "",
            "Day4 不应声称 PCAS 显著提升图像质量。更准确的结论是：PCAS / Balanced-PCAS 在减少推理步数和时间的同时，基本保持了与 Fixed-20 相当的 CLIPScore 和肉眼观感。因此，方法的主要价值是改善效率-质量权衡，而不是提升质量上限。",
            "",
            "## 图表引用",
            "",
            "- Hard prompt 对比图：`results/figures/day4_hard_prompt_qualitative_grid.png`",
            "- Hard subset CLIPScore 表：`results/day4_hard_prompt_clipscore_summary.csv`",
            "- 与 Fixed-20 的视觉差异热图：`results/figures/day4_hard_prompt_difference_heatmap_vs_fixed20.png`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    source = Path("results/day3_pcas_all_balanced_clipscore_results.csv")
    rows = hard_rows(read_csv(source))

    summary_rows = summarize_clipscore(rows)
    write_csv(
        Path("results/day4_hard_prompt_clipscore_summary.csv"),
        summary_rows,
        ["method", "num_images", "avg_steps", "avg_time_no_warmup", "avg_clip_score", "min_clip_score", "max_clip_score"],
    )

    make_grid(rows, Path("results/figures/day4_hard_prompt_qualitative_grid.png"))
    write_report_draft(Path("report/day4_hard_prompt_evaluation_draft.md"), summary_rows)
    print("Wrote Day 4 hard prompt evaluation assets.")


if __name__ == "__main__":
    main()
