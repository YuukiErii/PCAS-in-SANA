from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

from prompt_complexity_deepseek import DEFAULT_DEEPSEEK_MODEL, load_api_key
from prompt_features import feature_row, read_prompts


SYSTEM_PROMPT = """
You are extracting structured features for a text-to-image inference scheduler.
Return valid JSON only. Do not include markdown.

For the given prompt, estimate these fields:
- object_count: number of distinct visible object/entity categories.
- attribute_count: number of explicit visual attributes such as color, material, lighting, era, mood, or size.
- relation_count: number of spatial/action/interaction relations.
- spatial_relation_count: count only spatial relations such as beside, behind, under, above, inside, across, near, between.
- action_count: count visible actions or interactions.
- style_constraint_count: number of style, rendering, lighting, genre, or medium constraints.
- text_rendering_flag: 1 if readable text/signs/letters/logos are requested, else 0.
- scene_density_score: float from 0 to 1 for visual clutter and number of entities.
- rare_concept_score: float from 0 to 1 for rare, hard, fictional, technical, or culturally specific concepts.
- estimated_difficulty: float from 0 to 1 for how many sampling steps may be needed to match a Fixed-20 quality target.
- difficulty_label: one of low, medium, high.
- reason: one short sentence.

Use this exact JSON shape:
{
  "object_count": 1,
  "attribute_count": 2,
  "relation_count": 0,
  "spatial_relation_count": 0,
  "action_count": 0,
  "style_constraint_count": 1,
  "text_rendering_flag": 0,
  "scene_density_score": 0.2,
  "rare_concept_score": 0.0,
  "estimated_difficulty": 0.25,
  "difficulty_label": "low",
  "reason": "single common object with few relations"
}
"""


OUTPUT_FIELDS = [
    "prompt_index",
    "prompt",
    "word_count",
    "content_word_count",
    "comma_count",
    "llm_object_count",
    "llm_attribute_count",
    "llm_relation_count",
    "llm_spatial_relation_count",
    "llm_action_count",
    "llm_style_constraint_count",
    "llm_text_rendering_flag",
    "llm_scene_density_score",
    "llm_rare_concept_score",
    "llm_estimated_difficulty",
    "llm_difficulty_label",
    "llm_reason",
    "llm_model",
    "source",
    "cache_hit",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
]


def prompt_cache_key(prompt: str, model: str) -> str:
    payload = json.dumps({"schema": "deepseek_prompt_features_v1", "model": model, "prompt": prompt}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def clamp_float(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def as_nonnegative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def normalize(raw: dict[str, Any]) -> dict[str, Any]:
    label = str(raw.get("difficulty_label", "medium")).strip().lower()
    if label not in {"low", "medium", "high"}:
        label = "medium"
    return {
        "llm_object_count": as_nonnegative_int(raw.get("object_count")),
        "llm_attribute_count": as_nonnegative_int(raw.get("attribute_count")),
        "llm_relation_count": as_nonnegative_int(raw.get("relation_count")),
        "llm_spatial_relation_count": as_nonnegative_int(raw.get("spatial_relation_count")),
        "llm_action_count": as_nonnegative_int(raw.get("action_count")),
        "llm_style_constraint_count": as_nonnegative_int(raw.get("style_constraint_count")),
        "llm_text_rendering_flag": 1 if bool(raw.get("text_rendering_flag", 0)) else 0,
        "llm_scene_density_score": clamp_float(raw.get("scene_density_score")),
        "llm_rare_concept_score": clamp_float(raw.get("rare_concept_score")),
        "llm_estimated_difficulty": clamp_float(raw.get("estimated_difficulty"), default=0.5),
        "llm_difficulty_label": label,
        "llm_reason": str(raw.get("reason", "")).strip()[:240],
    }


def fallback_features(prompt: str, model: str, reason: str) -> dict[str, Any]:
    rule = feature_row(prompt)
    return {
        "word_count": rule["word_count"],
        "content_word_count": rule["content_word_count"],
        "comma_count": rule["comma_count"],
        "llm_object_count": rule["object_count"],
        "llm_attribute_count": rule["attribute_count"],
        "llm_relation_count": rule["relation_count"],
        "llm_spatial_relation_count": rule["spatial_relation_count"],
        "llm_action_count": rule["action_count"],
        "llm_style_constraint_count": rule["style_constraint_count"],
        "llm_text_rendering_flag": rule["text_rendering_flag"],
        "llm_scene_density_score": rule["scene_density_score"],
        "llm_rare_concept_score": rule["rare_concept_score"],
        "llm_estimated_difficulty": rule["rule_complexity_score"],
        "llm_difficulty_label": "high" if rule["rule_complexity_score"] >= 0.66 else "medium" if rule["rule_complexity_score"] >= 0.33 else "low",
        "llm_reason": f"Fallback rule features: {reason}",
        "llm_model": model,
        "source": "fallback_rule",
        "cache_hit": False,
        "prompt_tokens": "",
        "completion_tokens": "",
        "total_tokens": "",
    }


def call_deepseek(prompt: str, model: str, api_key: str, max_tokens: int) -> tuple[dict[str, Any], dict[str, int | None]]:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract calibrated PCAS features for this prompt:\n{prompt}"},
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=max_tokens,
        stream=False,
        extra_body={"thinking": {"type": "disabled"}},
    )
    content = response.choices[0].message.content or "{}"
    usage = getattr(response, "usage", None)
    return json.loads(content), {
        "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
        "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
        "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
    }


def analyze_prompt_llm(
    prompt: str,
    prompt_index: int,
    model: str,
    api_key_file: str | None,
    cache_path: Path,
    refresh_cache: bool,
    max_tokens: int,
    max_retries: int,
) -> dict[str, Any]:
    rule = feature_row(prompt)
    cache = load_cache(cache_path)
    key = prompt_cache_key(prompt, model)
    if not refresh_cache and key in cache:
        normalized = normalize(cache[key]["features"])
        return {
            "prompt_index": prompt_index,
            "prompt": prompt,
            "word_count": rule["word_count"],
            "content_word_count": rule["content_word_count"],
            "comma_count": rule["comma_count"],
            **normalized,
            "llm_model": model,
            "source": "deepseek_cache",
            "cache_hit": True,
            **cache[key].get("usage", {}),
        }

    api_key = load_api_key(api_key_file)
    if not api_key:
        return {"prompt_index": prompt_index, "prompt": prompt, **fallback_features(prompt, model, "missing API key")}

    last_error = ""
    for attempt in range(max_retries + 1):
        try:
            raw, usage = call_deepseek(prompt, model, api_key, max_tokens)
            normalized = normalize(raw)
            cache[key] = {
                "model": model,
                "prompt": prompt,
                "features": raw,
                "normalized": normalized,
                "usage": usage,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            save_cache(cache_path, cache)
            return {
                "prompt_index": prompt_index,
                "prompt": prompt,
                "word_count": rule["word_count"],
                "content_word_count": rule["content_word_count"],
                "comma_count": rule["comma_count"],
                **normalized,
                "llm_model": model,
                "source": "deepseek_api",
                "cache_hit": False,
                **usage,
            }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < max_retries:
                time.sleep(1.5 * (attempt + 1))
    return {"prompt_index": prompt_index, "prompt": prompt, **fallback_features(prompt, model, last_error)}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract DeepSeek JSON prompt features for Calibrated PCAS.")
    parser.add_argument("--prompt-file", default="prompts/day2_benchmark_prompts.txt")
    parser.add_argument("--output", default="results/day6_deepseek_prompt_features.csv")
    parser.add_argument("--cache", default="results/day6_deepseek_prompt_feature_cache.json")
    parser.add_argument("--api-key-file", default="API_DEEPSEEK.txt")
    parser.add_argument("--model", default=DEFAULT_DEEPSEEK_MODEL)
    parser.add_argument("--refresh-cache", action="store_true")
    parser.add_argument("--max-tokens", type=int, default=500)
    parser.add_argument("--max-retries", type=int, default=2)
    args = parser.parse_args()

    prompts = read_prompts(Path(args.prompt_file))
    rows = [
        analyze_prompt_llm(
            prompt=prompt,
            prompt_index=index,
            model=args.model,
            api_key_file=args.api_key_file,
            cache_path=Path(args.cache),
            refresh_cache=args.refresh_cache,
            max_tokens=args.max_tokens,
            max_retries=args.max_retries,
        )
        for index, prompt in enumerate(prompts, start=1)
    ]
    write_csv(Path(args.output), rows)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
