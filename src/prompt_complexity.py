from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


RELATION_TERMS = [
    "next to",
    "beside",
    "behind",
    "in front of",
    "under",
    "above",
    "holding",
    "carrying",
    "near",
    "between",
]

STYLE_TERMS = [
    "cinematic",
    "watercolor",
    "cyberpunk",
    "fantasy",
    "steampunk",
    "realistic",
    "studio light",
    "golden light",
    "neon",
]

TEXT_TERMS = [
    "text",
    "says",
    "sign",
    "spelling",
    "poster",
    "chalkboard",
    "word",
    "letters",
]


DEFAULT_POLICY = {
    "short_max_words": 20,
    "medium_max_words": 40,
    "short": {"steps": 10, "guidance_scale": 4.0, "height": 512, "width": 512},
    "medium": {"steps": 20, "guidance_scale": 4.5, "height": 512, "width": 512},
    "long": {"steps": 28, "guidance_scale": 5.0, "height": 512, "width": 512},
}


@dataclass
class PromptComplexity:
    prompt: str
    word_count: int
    relation_count: int
    style_count: int
    text_rendering: bool
    length_score: float
    relation_score: float
    style_score: float
    text_score: float
    complexity_score: float
    complexity_label: str
    selected_steps: int
    selected_guidance_scale: float
    selected_height: int
    selected_width: int


def count_words(prompt: str) -> int:
    return len(prompt.split())


def count_terms(prompt: str, terms: list[str]) -> int:
    lowered = prompt.lower()
    return sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", lowered))


def merge_policy(policy: dict | None) -> dict:
    merged = {
        "short_max_words": DEFAULT_POLICY["short_max_words"],
        "medium_max_words": DEFAULT_POLICY["medium_max_words"],
        "short": dict(DEFAULT_POLICY["short"]),
        "medium": dict(DEFAULT_POLICY["medium"]),
        "long": dict(DEFAULT_POLICY["long"]),
    }
    if not policy:
        return merged
    for key, value in policy.items():
        if key in ("short", "medium", "long") and isinstance(value, dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def label_from_words(word_count: int, policy: dict) -> str:
    if word_count <= int(policy["short_max_words"]):
        return "short"
    if word_count <= int(policy["medium_max_words"]):
        return "medium"
    return "long"


def analyze_prompt(prompt: str, policy: dict | None = None) -> PromptComplexity:
    policy = merge_policy(policy)
    word_count = count_words(prompt)
    relation_count = count_terms(prompt, RELATION_TERMS)
    style_count = count_terms(prompt, STYLE_TERMS)
    text_count = count_terms(prompt, TEXT_TERMS)
    text_rendering = text_count > 0

    length_score = min(word_count / 50.0, 1.0)
    relation_score = min(relation_count / 3.0, 1.0)
    style_score = min(style_count / 3.0, 1.0)
    text_score = 1.0 if text_rendering else 0.0
    complexity_score = min(
        0.70 * length_score + 0.15 * relation_score + 0.10 * style_score + 0.05 * text_score,
        1.0,
    )

    label = label_from_words(word_count, policy)
    selected = policy[label]
    return PromptComplexity(
        prompt=prompt,
        word_count=word_count,
        relation_count=relation_count,
        style_count=style_count,
        text_rendering=text_rendering,
        length_score=length_score,
        relation_score=relation_score,
        style_score=style_score,
        text_score=text_score,
        complexity_score=complexity_score,
        complexity_label=label,
        selected_steps=int(selected["steps"]),
        selected_guidance_scale=float(selected["guidance_scale"]),
        selected_height=int(selected["height"]),
        selected_width=int(selected["width"]),
    )


def read_prompts(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def write_csv(path: Path, rows: list[PromptComplexity]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze prompt complexity for PCAS.")
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--prompt-file", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    args = parser.parse_args()

    prompts: list[str] = []
    if args.prompt:
        prompts.append(args.prompt)
    if args.prompt_file:
        prompts.extend(read_prompts(Path(args.prompt_file)))
    if not prompts:
        raise ValueError("Provide --prompt or --prompt-file.")

    rows = [analyze_prompt(prompt) for prompt in prompts]
    if args.output:
        output = Path(args.output)
        if args.format == "csv":
            write_csv(output, rows)
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps([asdict(row) for row in rows], indent=2), encoding="utf-8")
        print(f"Wrote {output}")
    else:
        print(json.dumps([asdict(row) for row in rows], indent=2))


if __name__ == "__main__":
    main()
