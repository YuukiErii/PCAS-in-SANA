from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import torch
from PIL import Image, ImageDraw, ImageFont
from transformers import CLIPModel, CLIPProcessor


REFERENCE_DIR = Path("data/dreambooth/zzmearphone")
SUMMARIES = [
    ("base", Path("outputs/day5_lora_subject_validation_base/summary.json")),
    ("original_lora_scale_2", Path("outputs/day5_lora_subject_validation_original_scale2/summary.json")),
    ("enhanced_lora_scale_1_5", Path("outputs/day5_lora_subject_validation_enhanced_scale1_5/summary.json")),
    ("enhanced_lora_scale_2", Path("outputs/day5_lora_subject_validation_enhanced_scale2/summary.json")),
    ("clean_captioned_lora_scale_1_25", Path("outputs/day5_lora_subject_validation_clean_captioned_scale1_25/summary.json")),
    ("clean_captioned_lora_scale_1_5", Path("outputs/day5_lora_subject_validation_clean_captioned_scale1_5/summary.json")),
    ("clean_captioned_lora_scale_1_75", Path("outputs/day5_lora_subject_validation_clean_captioned_scale1_75/summary.json")),
]
METHOD_LABELS = {
    "base": "Base",
    "original_lora_scale_2": "Original LoRA x2",
    "enhanced_lora_scale_1_5": "Enhanced LoRA x1.5",
    "enhanced_lora_scale_2": "Enhanced LoRA x2",
    "clean_captioned_lora_scale_1_25": "Clean-caption x1.25",
    "clean_captioned_lora_scale_1_5": "Clean-caption x1.5",
    "clean_captioned_lora_scale_1_75": "Clean-caption x1.75",
}
SUBJECT_CANONICAL_PROMPT = (
    "a photo of black over-ear headphones with large oval ear cups, "
    "a padded headband, and black leather ear cushions"
)
RESULTS_CSV = Path("results/day5_lora_subject_consistency_results.csv")
SUMMARY_CSV = Path("results/day5_lora_subject_consistency_summary.csv")
SUMMARY_MD = Path("results/day5_lora_subject_consistency_summary.md")
GRID_PATH = Path("results/figures/day5_lora_subject_consistency_grid.png")


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


def feature_tensor(features: Any) -> torch.Tensor:
    if isinstance(features, torch.Tensor):
        return features
    for name in ("image_embeds", "text_embeds", "pooler_output"):
        value = getattr(features, name, None)
        if isinstance(value, torch.Tensor):
            return value
    if isinstance(features, (tuple, list)) and features and isinstance(features[0], torch.Tensor):
        return features[0]
    raise TypeError(f"Cannot extract tensor from {type(features).__name__}.")


def load_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for method, path in SUMMARIES:
        records = json.loads(path.read_text(encoding="utf-8"))
        for prompt_index, record in enumerate(records, start=1):
            row = dict(record)
            row["method"] = method
            row["prompt_index"] = prompt_index
            rows.append(row)
    return rows


def load_image(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def encode_images(model: CLIPModel, processor: CLIPProcessor, paths: list[Path], device: str) -> torch.Tensor:
    images = [load_image(path) for path in paths]
    inputs = processor(images=images, return_tensors="pt").to(device)
    with torch.no_grad():
        features = feature_tensor(model.get_image_features(**inputs))
    return torch.nn.functional.normalize(features, dim=-1)


def encode_texts(model: CLIPModel, processor: CLIPProcessor, texts: list[str], device: str) -> torch.Tensor:
    inputs = processor(text=texts, padding=True, truncation=True, return_tensors="pt").to(device)
    with torch.no_grad():
        features = feature_tensor(model.get_text_features(**inputs))
    return torch.nn.functional.normalize(features, dim=-1)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def compute_metrics(model_id: str = "openai/clip-vit-base-patch32", device: str = "cuda") -> list[dict[str, Any]]:
    records = load_records()
    reference_paths = sorted(REFERENCE_DIR.glob("*.jpg"))
    if not reference_paths:
        raise ValueError(f"No reference images found under {REFERENCE_DIR}")

    model = CLIPModel.from_pretrained(model_id).to(device)
    processor = CLIPProcessor.from_pretrained(model_id)
    model.eval()

    reference_features = encode_images(model, processor, reference_paths, device)
    reference_centroid = torch.nn.functional.normalize(reference_features.mean(dim=0, keepdim=True), dim=-1)
    image_features = encode_images(model, processor, [Path(row["image_path"]) for row in records], device)
    prompt_features = encode_texts(model, processor, [row["prompt"] for row in records], device)
    subject_features = encode_texts(model, processor, [SUBJECT_CANONICAL_PROMPT] * len(records), device)

    rows: list[dict[str, Any]] = []
    for row, image_feature, prompt_feature, subject_feature in zip(records, image_features, prompt_features, subject_features):
        rows.append(
            {
                "prompt_index": row["prompt_index"],
                "method": row["method"],
                "prompt": row["prompt"],
                "image_path": row["image_path"],
                "elapsed_seconds": float(row["elapsed_seconds"]),
                "peak_vram_gb": float(row["peak_vram_gb"]),
                "reference_clip_similarity": float((image_feature.unsqueeze(0) @ reference_centroid.T).item() * 100.0),
                "prompt_clipscore": float((image_feature @ prompt_feature).item() * 100.0),
                "subject_prompt_clipscore": float((image_feature @ subject_feature).item() * 100.0),
            }
        )

    base_by_prompt = {row["prompt_index"]: row for row in rows if row["method"] == "base"}
    for row in rows:
        base = base_by_prompt[row["prompt_index"]]
        row["delta_reference_vs_base"] = row["reference_clip_similarity"] - base["reference_clip_similarity"]
        row["delta_subject_prompt_vs_base"] = row["subject_prompt_clipscore"] - base["subject_prompt_clipscore"]
    return rows


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for method, _ in SUMMARIES:
        method_rows = [row for row in rows if row["method"] == method]
        no_warmup = method_rows[1:] if len(method_rows) > 1 else method_rows
        deltas = [row["delta_reference_vs_base"] for row in method_rows]
        subject_deltas = [row["delta_subject_prompt_vs_base"] for row in method_rows]
        summary.append(
            {
                "method": method,
                "images": len(method_rows),
                "avg_time_no_warmup_seconds": mean(row["elapsed_seconds"] for row in no_warmup),
                "avg_peak_vram_gb": mean(row["peak_vram_gb"] for row in method_rows),
                "avg_reference_clip_similarity": mean(row["reference_clip_similarity"] for row in method_rows),
                "std_reference_clip_similarity": pstdev(row["reference_clip_similarity"] for row in method_rows),
                "avg_reference_delta_vs_base": mean(deltas),
                "reference_wins_vs_base": sum(1 for value in deltas if value > 0),
                "avg_prompt_clipscore": mean(row["prompt_clipscore"] for row in method_rows),
                "avg_subject_prompt_clipscore": mean(row["subject_prompt_clipscore"] for row in method_rows),
                "avg_subject_prompt_delta_vs_base": mean(subject_deltas),
                "subject_prompt_wins_vs_base": sum(1 for value in subject_deltas if value > 0),
            }
        )
    return summary


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_markdown(summary_rows: list[dict[str, Any]]) -> None:
    best = max(
        [row for row in summary_rows if row["method"] != "base"],
        key=lambda row: (row["avg_subject_prompt_delta_vs_base"], row["avg_reference_delta_vs_base"]),
    )
    clean_best = max(
        [row for row in summary_rows if row["method"].startswith("clean_captioned")],
        key=lambda row: (row["avg_reference_delta_vs_base"], row["avg_subject_prompt_delta_vs_base"]),
    )
    lines = [
        "# Day 5 LoRA Subject Consistency Summary",
        "",
        "This follow-up evaluates subject-focused prompts that keep the headphones centered and unobstructed. It compares the original 200-step LoRA, an enhanced 500-step rank-16 LoRA, and a clean-captioned 400-step rank-16 LoRA trained on a cleaner 7-image subset with per-image captions.",
        "",
        "| Method | Images | Ref similarity | Ref delta vs Base | Ref wins | Subject CLIP | Subject delta vs Base | Subject wins | Prompt CLIPScore |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        lines.append(
            "| {method} | {images} | {ref} | {ref_delta} | {ref_wins}/{images} | {subject} | {subject_delta} | {subject_wins}/{images} | {prompt} |".format(
                method=METHOD_LABELS[row["method"]],
                images=row["images"],
                ref=fmt(row["avg_reference_clip_similarity"]),
                ref_delta=fmt(row["avg_reference_delta_vs_base"]),
                ref_wins=row["reference_wins_vs_base"],
                subject=fmt(row["avg_subject_prompt_clipscore"]),
                subject_delta=fmt(row["avg_subject_prompt_delta_vs_base"]),
                subject_wins=row["subject_prompt_wins_vs_base"],
                prompt=fmt(row["avg_prompt_clipscore"]),
            )
        )
    lines.extend(
        [
            "",
            "Key finding:",
            "",
            f"- Best automatic subject-consistency setting: `{METHOD_LABELS[best['method']]}`.",
            f"- Best clean-captioned compromise setting: `{METHOD_LABELS[clean_best['method']]}`.",
            "- The enhanced and clean-captioned LoRA variants use more explicit prompts, rank 16, and longer training than the original 200-step run.",
            "- The clean-captioned variant removes the most ambiguous training views and gives each remaining image a specific caption, so it tests whether better data/caption quality can reduce subject instability.",
            "- Clean-caption x1.25 is more conservative than the enhanced x1.5 setting: it does not win the automatic subject-prompt metric, but it keeps reference similarity close to Base and avoids the stronger scale collapse seen at x1.75/x2.",
            "- This is enough for the Day 5 conclusion; extra photos would mainly improve visual polish and product-identity robustness rather than unblock the current result.",
            "- The validation prompts avoid occlusion-heavy scenes; this better measures whether the adapter can preserve the learned headphone identity.",
            "- CLIP-based identity metrics remain proxies, so the qualitative grid should be used together with this table.",
            "",
            "Files:",
            "",
            f"- Detailed metrics: `{RESULTS_CSV}`",
            f"- Visual grid: `{GRID_PATH}`",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


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


def fit_image(path: Path, size: int) -> Image.Image:
    image = Image.open(path).convert("RGB")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), "white")
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    return canvas


def make_grid(rows: list[dict[str, Any]]) -> None:
    by_key = {(row["method"], row["prompt_index"]): row for row in rows}
    prompt_indices = sorted({row["prompt_index"] for row in rows})
    methods = [method for method, _ in SUMMARIES]

    title_font = load_font(32, bold=True)
    subtitle_font = load_font(17)
    header_font = load_font(16, bold=True)
    prompt_font = load_font(12)
    meta_font = load_font(11)

    margin = 28
    prompt_w = 330
    thumb = 160
    gap = 14
    header_h = 118
    row_h = 202
    width = margin * 2 + prompt_w + gap + len(methods) * thumb + (len(methods) - 1) * gap
    height = margin * 2 + header_h + len(prompt_indices) * row_h
    image = Image.new("RGB", (width, height), "#fbfaf6")
    draw = ImageDraw.Draw(image)

    draw.text((margin, 24), "Day 5 LoRA Subject Consistency", font=title_font, fill="#202428")
    draw.text(
        (margin, 66),
        "Subject-focused prompts: centered, unobstructed black over-ear headphones. Metrics show reference similarity and subject-prompt CLIP.",
        font=subtitle_font,
        fill="#50606a",
    )

    x0 = margin + prompt_w + gap
    for col_i, method in enumerate(methods):
        x = x0 + col_i * (thumb + gap)
        label = METHOD_LABELS[method]
        bbox = draw.textbbox((0, 0), label, font=header_font)
        draw.text((x + (thumb - (bbox[2] - bbox[0])) // 2, 98), label, font=header_font, fill="#202428")

    y = margin + header_h
    for row_i, prompt_index in enumerate(prompt_indices):
        fill = "#ffffff" if row_i % 2 == 0 else "#f0f2ee"
        draw.rounded_rectangle((margin - 10, y - 8, width - margin + 10, y + row_h - 14), radius=10, fill=fill, outline="#d8ddd4")
        base = by_key[("base", prompt_index)]
        draw.text((margin, y + 2), f"Prompt {prompt_index}", font=header_font, fill="#202428")
        for line_i, line in enumerate(wrap_text(draw, base["prompt"], prompt_font, prompt_w - 18)[:7]):
            draw.text((margin, y + 28 + line_i * 16), line, font=prompt_font, fill="#343a40")

        for col_i, method in enumerate(methods):
            row = by_key[(method, prompt_index)]
            x = x0 + col_i * (thumb + gap)
            tile = fit_image(Path(row["image_path"]), thumb)
            image.paste(tile, (x, y + 6))
            draw.rectangle((x, y + 6, x + thumb, y + 6 + thumb), outline="#b7c0b4")
            meta = "Ref {ref:.1f} | Subj {subj:.1f}".format(
                ref=row["reference_clip_similarity"],
                subj=row["subject_prompt_clipscore"],
            )
            draw.text((x, y + thumb + 12), meta, font=meta_font, fill="#52616b")
        y += row_h

    GRID_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(GRID_PATH, quality=95)


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rows = compute_metrics(device=device)
    result_fields = [
        "prompt_index",
        "method",
        "prompt",
        "image_path",
        "elapsed_seconds",
        "peak_vram_gb",
        "reference_clip_similarity",
        "prompt_clipscore",
        "subject_prompt_clipscore",
        "delta_reference_vs_base",
        "delta_subject_prompt_vs_base",
    ]
    write_csv(RESULTS_CSV, rows, result_fields)
    summary_rows = summarize(rows)
    summary_fields = [
        "method",
        "images",
        "avg_time_no_warmup_seconds",
        "avg_peak_vram_gb",
        "avg_reference_clip_similarity",
        "std_reference_clip_similarity",
        "avg_reference_delta_vs_base",
        "reference_wins_vs_base",
        "avg_prompt_clipscore",
        "avg_subject_prompt_clipscore",
        "avg_subject_prompt_delta_vs_base",
        "subject_prompt_wins_vs_base",
    ]
    write_csv(SUMMARY_CSV, summary_rows, summary_fields)
    write_markdown(summary_rows)
    make_grid(rows)
    print("Wrote Day 5 LoRA subject consistency assets.")


if __name__ == "__main__":
    main()
