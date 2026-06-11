from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps


def make_square_image(image: Image.Image, size: int) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)

    background = image.resize((size, size), Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(radius=28))
    overlay = Image.new("RGB", (size, size), (245, 245, 245))
    background = Image.blend(background, overlay, alpha=0.35)

    x = (size - image.width) // 2
    y = (size - image.height) // 2
    background.paste(image, (x, y))
    return background


def prepare_dataset(input_dir: Path, output_dir: Path, size: int) -> list[dict[str, object]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    image_paths = sorted(
        path for path in input_dir.iterdir() if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )
    manifest: list[dict[str, object]] = []
    for index, image_path in enumerate(image_paths, start=1):
        with Image.open(image_path) as image:
            prepared = make_square_image(image, size)
        output_path = output_dir / f"{index:02d}_zzmearphone.jpg"
        prepared.save(output_path, quality=95)
        manifest.append(
            {
                "source": str(image_path),
                "prepared": str(output_path),
                "source_size": [image.size[0], image.size[1]],
                "prepared_size": [size, size],
            }
        )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare square DreamBooth images for SANA LoRA training.")
    parser.add_argument("--input-dir", default="data/raw/zzm_earphone")
    parser.add_argument("--output-dir", default="data/dreambooth/zzmearphone")
    parser.add_argument("--size", type=int, default=768)
    args = parser.parse_args()

    manifest = prepare_dataset(Path(args.input_dir), Path(args.output_dir), args.size)
    manifest_path = Path(args.output_dir) / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Prepared {len(manifest)} images in {args.output_dir}")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
