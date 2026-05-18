from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9'-]*")

STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "has",
    "in",
    "inside",
    "into",
    "is",
    "near",
    "of",
    "on",
    "over",
    "past",
    "the",
    "through",
    "to",
    "toward",
    "under",
    "where",
    "while",
    "with",
}

OBJECT_TERMS = {
    "apple",
    "astronaut",
    "awning",
    "backpack",
    "bag",
    "ball",
    "balloon",
    "bench",
    "bicycle",
    "bird",
    "book",
    "bookstore",
    "bridge",
    "cabin",
    "cafe",
    "camera",
    "car",
    "case",
    "castle",
    "cat",
    "chair",
    "chalkboard",
    "child",
    "city",
    "classroom",
    "clock",
    "cloud",
    "coffee",
    "coin",
    "counter",
    "desk",
    "detective",
    "dog",
    "dragon",
    "drone",
    "engine",
    "engineer",
    "festival",
    "file",
    "flag",
    "fork",
    "fountain",
    "gear",
    "globe",
    "grass",
    "headphones",
    "helmet",
    "horse",
    "inventor",
    "kite",
    "kitchen",
    "lake",
    "lamp",
    "lantern",
    "library",
    "locker",
    "map",
    "market",
    "moon",
    "mountain",
    "mug",
    "napkin",
    "notebook",
    "painter",
    "park",
    "pedestrian",
    "photo",
    "plant",
    "plate",
    "poster",
    "prompt",
    "rain",
    "river",
    "robot",
    "rocket",
    "road",
    "rover",
    "sailboat",
    "sandwich",
    "shelf",
    "ship",
    "shoe",
    "sign",
    "sneaker",
    "spaceport",
    "staircase",
    "station",
    "student",
    "table",
    "taxi",
    "teacher",
    "telescope",
    "train",
    "tree",
    "umbrella",
    "vase",
    "wall",
    "window",
    "wizard",
    "workshop",
}

ATTRIBUTE_TERMS = {
    "black",
    "blue",
    "brass",
    "bright",
    "broken",
    "busy",
    "calm",
    "clear",
    "colorful",
    "crowded",
    "curious",
    "dark",
    "distant",
    "dusty",
    "empty",
    "flickering",
    "floating",
    "folded",
    "fresh",
    "gentle",
    "glass",
    "glowing",
    "golden",
    "green",
    "handwritten",
    "heavy",
    "hovering",
    "large",
    "leafy",
    "modern",
    "narrow",
    "orange",
    "pale",
    "purple",
    "rainy",
    "red",
    "shimmer",
    "silver",
    "small",
    "smoky",
    "snowy",
    "soft",
    "striped",
    "sunny",
    "tiny",
    "vintage",
    "warm",
    "wet",
    "white",
    "wooden",
}

SPATIAL_RELATION_TERMS = [
    "above",
    "across",
    "behind",
    "beneath",
    "beside",
    "between",
    "in front of",
    "inside",
    "near",
    "next to",
    "under",
]

ACTION_TERMS = {
    "adjusting",
    "arriving",
    "building",
    "carry",
    "carrying",
    "cast",
    "casting",
    "circle",
    "cooks",
    "crossing",
    "dancing",
    "defend",
    "drifting",
    "flies",
    "fly",
    "glows",
    "guide",
    "hanging",
    "holds",
    "hover",
    "hovering",
    "lean",
    "leaning",
    "playing",
    "pour",
    "repair",
    "rising",
    "sitting",
    "sleeping",
    "spelling",
    "tightening",
    "wait",
    "waiting",
    "walking",
    "watching",
}

STYLE_TERMS = [
    "cinematic",
    "cyberpunk",
    "fantasy",
    "golden light",
    "holographic",
    "medieval",
    "neon",
    "realistic",
    "soft studio light",
    "steampunk",
    "studio light",
    "watercolor",
]

TEXT_TERMS = [
    "chalkboard",
    "letters",
    "logo",
    "poster",
    "says",
    "sign",
    "spelling",
    "text",
    "word",
]

RARE_CONCEPT_TERMS = {
    "alien",
    "cyberpunk",
    "dragon",
    "drone",
    "holographic",
    "kanji",
    "maglev",
    "rover",
    "sana",
    "spaceport",
    "steampunk",
    "wizard",
}


@dataclass
class PromptFeatures:
    prompt: str
    word_count: int
    content_word_count: int
    comma_count: int
    object_count: int
    attribute_count: int
    relation_count: int
    spatial_relation_count: int
    action_count: int
    style_constraint_count: int
    text_rendering_flag: int
    scene_density_score: float
    rare_concept_score: float
    lexical_complexity_score: float
    rule_complexity_score: float


def tokenize(prompt: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(prompt)]


def count_phrase_matches(prompt: str, phrases: list[str] | set[str]) -> int:
    lowered = prompt.lower()
    return sum(1 for phrase in phrases if re.search(rf"\b{re.escape(phrase)}\b", lowered))


def estimate_object_count(tokens: list[str]) -> int:
    direct_matches = [token for token in tokens if token in OBJECT_TERMS]
    if direct_matches:
        return len(set(direct_matches))
    content_tokens = [token for token in tokens if token not in STOPWORDS]
    return max(1, min(8, round(len(content_tokens) / 5)))


def extract_prompt_features(prompt: str) -> PromptFeatures:
    tokens = tokenize(prompt)
    content_tokens = [token for token in tokens if token not in STOPWORDS]
    word_count = len(prompt.split())
    object_count = estimate_object_count(tokens)
    attribute_count = sum(1 for token in tokens if token in ATTRIBUTE_TERMS)
    spatial_relation_count = count_phrase_matches(prompt, SPATIAL_RELATION_TERMS)
    action_count = sum(1 for token in tokens if token in ACTION_TERMS)
    style_constraint_count = count_phrase_matches(prompt, STYLE_TERMS)
    text_rendering_flag = 1 if count_phrase_matches(prompt, TEXT_TERMS) > 0 else 0
    relation_count = spatial_relation_count + action_count
    rare_hits = sum(1 for token in set(tokens) if token in RARE_CONCEPT_TERMS)
    long_rare_tokens = sum(1 for token in set(content_tokens) if len(token) >= 11 and token not in OBJECT_TERMS)
    rare_concept_score = min((rare_hits + 0.5 * long_rare_tokens) / 4.0, 1.0)
    scene_density_score = min(
        (object_count + 0.5 * attribute_count + relation_count + 1.5 * style_constraint_count) / 18.0,
        1.0,
    )
    lexical_complexity_score = min((word_count / 50.0) * 0.8 + (len(set(content_tokens)) / 45.0) * 0.2, 1.0)
    rule_complexity_score = min(
        0.35 * lexical_complexity_score
        + 0.25 * scene_density_score
        + 0.15 * min(relation_count / 6.0, 1.0)
        + 0.10 * min(style_constraint_count / 3.0, 1.0)
        + 0.10 * text_rendering_flag
        + 0.05 * rare_concept_score,
        1.0,
    )
    return PromptFeatures(
        prompt=prompt,
        word_count=word_count,
        content_word_count=len(content_tokens),
        comma_count=prompt.count(","),
        object_count=object_count,
        attribute_count=attribute_count,
        relation_count=relation_count,
        spatial_relation_count=spatial_relation_count,
        action_count=action_count,
        style_constraint_count=style_constraint_count,
        text_rendering_flag=text_rendering_flag,
        scene_density_score=scene_density_score,
        rare_concept_score=rare_concept_score,
        lexical_complexity_score=lexical_complexity_score,
        rule_complexity_score=rule_complexity_score,
    )


def feature_row(prompt: str) -> dict:
    return asdict(extract_prompt_features(prompt))


def read_prompts(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract rule-based prompt complexity features.")
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--prompt-file", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--format", choices=["json", "csv"], default="csv")
    args = parser.parse_args()

    prompts: list[str] = []
    if args.prompt:
        prompts.append(args.prompt)
    if args.prompt_file:
        prompts.extend(read_prompts(Path(args.prompt_file)))
    if not prompts:
        raise ValueError("Provide --prompt or --prompt-file.")

    rows = [feature_row(prompt) for prompt in prompts]
    if not args.output:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "json":
        output.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        write_csv(output, rows)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
