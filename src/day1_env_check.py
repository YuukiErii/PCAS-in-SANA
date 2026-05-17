from __future__ import annotations

import argparse
import datetime as dt
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path


PACKAGES = [
    "torch",
    "torchvision",
    "diffusers",
    "transformers",
    "accelerate",
    "safetensors",
    "sentencepiece",
    "Pillow",
    "pandas",
    "pyyaml",
]


def package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def run_command(command: list[str]) -> str:
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return f"{command[0]} not found"
    return completed.stdout.strip()


def torch_report() -> list[str]:
    try:
        import torch
    except Exception as exc:
        return [f"- Torch import: failed ({type(exc).__name__}: {exc})"]

    lines = [
        f"- Torch version: `{torch.__version__}`",
        f"- CUDA available: `{torch.cuda.is_available()}`",
        f"- Torch CUDA version: `{torch.version.cuda}`",
    ]
    if torch.cuda.is_available():
        index = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(index)
        total_gb = props.total_memory / 1024**3
        lines.extend(
            [
                f"- CUDA device: `{torch.cuda.get_device_name(index)}`",
                f"- CUDA capability: `{props.major}.{props.minor}`",
                f"- Total VRAM: `{total_gb:.2f} GB`",
            ]
        )
    return lines


def build_report() -> str:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Day 1 Environment Report",
        "",
        f"- Generated at: `{now}`",
        f"- Python executable: `{sys.executable}`",
        f"- Python version: `{platform.python_version()}`",
        f"- Platform: `{platform.platform()}`",
        "",
        "## Packages",
        "",
    ]
    lines.extend([f"- {name}: `{package_version(name)}`" for name in PACKAGES])
    lines.extend(["", "## CUDA / GPU", ""])
    lines.extend(torch_report())
    lines.extend(["", "## nvidia-smi", "", "```text"])
    lines.append(run_command(["nvidia-smi"]))
    lines.extend(["```", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a Day 1 reproducibility report.")
    parser.add_argument("--output", default="results/day1_environment.md")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_report(), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
