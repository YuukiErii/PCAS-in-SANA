from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from prompt_complexity import analyze_prompt


DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
DEFAULT_CACHE_PATH = "results/day3_deepseek_complexity_cache.json"

DEEPSEEK_POLICY = {
    "low": {"steps": 10, "guidance_scale": 4.0, "height": 512, "width": 512},
    "medium": {"steps": 20, "guidance_scale": 4.5, "height": 512, "width": 512},
    "high": {"steps": 28, "guidance_scale": 5.0, "height": 512, "width": 512},
}

SYSTEM_PROMPT = """
You are analyzing prompts for a text-to-image generation experiment.
Return valid json only. Do not include markdown.

For the prompt, estimate semantic generation complexity:
- num_objects: count distinct visible entities or object categories.
- num_relations: count spatial, action, ownership, or interaction relations.
- style_constraints: count explicit style, lighting, era, material, mood, or rendering constraints.
- text_rendering: true if the image should contain readable text, letters, signs, labels, posters, logos, or written words.
- complexity: one of "low", "medium", "high".
- reason: one short sentence explaining the classification.

Use this exact json shape:
{
  "num_objects": 0,
  "num_relations": 0,
  "style_constraints": 0,
  "text_rendering": false,
  "complexity": "low",
  "reason": "single object with few constraints"
}
"""


@dataclass
class DeepSeekComplexity:
    prompt: str
    word_count: int
    num_objects: int
    num_relations: int
    style_constraints: int
    text_rendering: bool
    complexity: str
    complexity_score: float
    reason: str
    selected_steps: int
    selected_guidance_scale: float
    selected_height: int
    selected_width: int
    model: str
    source: str
    cache_hit: bool
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


def load_api_key(api_key_file: str | None = "API_DEEPSEEK.txt") -> str | None:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key.strip()
    if not api_key_file:
        return None
    path = Path(api_key_file)
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    if "=" in text and "\n" not in text:
        return text.split("=", 1)[1].strip().strip('"').strip("'")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            return line.split("=", 1)[1].strip().strip('"').strip("'")
        return line
    return None


def prompt_cache_key(prompt: str, model: str) -> str:
    payload = json.dumps({"model": model, "prompt": prompt}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def as_int(value: Any, default: int = 0) -> int:
    try:
        return max(int(value), 0)
    except (TypeError, ValueError):
        return default


def normalize_analysis(data: dict[str, Any]) -> dict[str, Any]:
    complexity = str(data.get("complexity", "medium")).lower().strip()
    if complexity not in DEEPSEEK_POLICY:
        complexity = "medium"
    return {
        "num_objects": as_int(data.get("num_objects")),
        "num_relations": as_int(data.get("num_relations")),
        "style_constraints": as_int(data.get("style_constraints")),
        "text_rendering": bool(data.get("text_rendering", False)),
        "complexity": complexity,
        "reason": str(data.get("reason", "")).strip()[:240],
    }


def complexity_score(analysis: dict[str, Any], word_count: int) -> float:
    base = {"low": 0.2, "medium": 0.55, "high": 0.85}[analysis["complexity"]]
    lexical_bonus = min(word_count / 50.0, 1.0) * 0.08
    relation_bonus = min(analysis["num_relations"] / 3.0, 1.0) * 0.04
    text_bonus = 0.03 if analysis["text_rendering"] else 0.0
    return min(base + lexical_bonus + relation_bonus + text_bonus, 1.0)


def policy_for_complexity(complexity: str, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = {key: dict(value) for key, value in DEEPSEEK_POLICY.items()}
    if policy:
        for key, value in policy.items():
            if key in merged and isinstance(value, dict):
                merged[key].update(value)
    return merged[complexity]


def fallback_analysis(prompt: str, model: str, reason: str) -> DeepSeekComplexity:
    rule = analyze_prompt(prompt)
    complexity = {"short": "low", "medium": "medium", "long": "high"}[rule.complexity_label]
    selected = policy_for_complexity(complexity)
    return DeepSeekComplexity(
        prompt=prompt,
        word_count=rule.word_count,
        num_objects=0,
        num_relations=rule.relation_count,
        style_constraints=rule.style_count,
        text_rendering=rule.text_rendering,
        complexity=complexity,
        complexity_score=rule.complexity_score,
        reason=f"Fallback rule-based analysis: {reason}",
        selected_steps=int(selected["steps"]),
        selected_guidance_scale=float(selected["guidance_scale"]),
        selected_height=int(selected["height"]),
        selected_width=int(selected["width"]),
        model=model,
        source="fallback_rule",
        cache_hit=False,
    )


def call_deepseek(prompt: str, model: str, api_key: str, max_tokens: int = 350) -> tuple[dict[str, Any], dict[str, int | None]]:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze this text-to-image prompt and output json:\n{prompt}"},
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=max_tokens,
        stream=False,
        extra_body={"thinking": {"type": "disabled"}},
    )
    content = response.choices[0].message.content or ""
    usage = getattr(response, "usage", None)
    usage_dict = {
        "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
        "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
        "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
    }
    return json.loads(content), usage_dict


def analyze_prompt_deepseek(
    prompt: str,
    model: str = DEFAULT_DEEPSEEK_MODEL,
    api_key_file: str | None = "API_DEEPSEEK.txt",
    cache_path: str | Path = DEFAULT_CACHE_PATH,
    policy: dict[str, Any] | None = None,
    refresh_cache: bool = False,
    max_retries: int = 2,
) -> DeepSeekComplexity:
    cache_file = Path(cache_path)
    cache = load_cache(cache_file)
    key = prompt_cache_key(prompt, model)
    if not refresh_cache and key in cache:
        cached = cache[key]
        analysis = normalize_analysis(cached["analysis"])
        selected = policy_for_complexity(analysis["complexity"], policy)
        return DeepSeekComplexity(
            prompt=prompt,
            word_count=len(prompt.split()),
            complexity_score=complexity_score(analysis, len(prompt.split())),
            selected_steps=int(selected["steps"]),
            selected_guidance_scale=float(selected["guidance_scale"]),
            selected_height=int(selected["height"]),
            selected_width=int(selected["width"]),
            model=model,
            source="deepseek_cache",
            cache_hit=True,
            prompt_tokens=cached.get("usage", {}).get("prompt_tokens"),
            completion_tokens=cached.get("usage", {}).get("completion_tokens"),
            total_tokens=cached.get("usage", {}).get("total_tokens"),
            **analysis,
        )

    api_key = load_api_key(api_key_file)
    if not api_key:
        return fallback_analysis(prompt, model, "missing DEEPSEEK_API_KEY and API key file")

    last_error = ""
    for attempt in range(max_retries + 1):
        try:
            raw_analysis, usage = call_deepseek(prompt, model, api_key)
            analysis = normalize_analysis(raw_analysis)
            selected = policy_for_complexity(analysis["complexity"], policy)
            cache[key] = {
                "model": model,
                "prompt": prompt,
                "analysis": analysis,
                "usage": usage,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            save_cache(cache_file, cache)
            return DeepSeekComplexity(
                prompt=prompt,
                word_count=len(prompt.split()),
                complexity_score=complexity_score(analysis, len(prompt.split())),
                selected_steps=int(selected["steps"]),
                selected_guidance_scale=float(selected["guidance_scale"]),
                selected_height=int(selected["height"]),
                selected_width=int(selected["width"]),
                model=model,
                source="deepseek_api",
                cache_hit=False,
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
                **analysis,
            )
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < max_retries:
                time.sleep(1.5 * (attempt + 1))
    return fallback_analysis(prompt, model, last_error)


def read_prompts(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def write_csv(path: Path, rows: list[DeepSeekComplexity]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze prompt complexity with DeepSeek JSON Output.")
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--prompt-file", default=None)
    parser.add_argument("--output", default="results/day3_deepseek_prompt_complexity.csv")
    parser.add_argument("--cache", default=DEFAULT_CACHE_PATH)
    parser.add_argument("--api-key-file", default="API_DEEPSEEK.txt")
    parser.add_argument("--model", default=DEFAULT_DEEPSEEK_MODEL)
    parser.add_argument("--refresh-cache", action="store_true")
    parser.add_argument("--format", choices=["csv", "json"], default="csv")
    args = parser.parse_args()

    prompts: list[str] = []
    if args.prompt:
        prompts.append(args.prompt)
    if args.prompt_file:
        prompts.extend(read_prompts(Path(args.prompt_file)))
    if not prompts:
        raise ValueError("Provide --prompt or --prompt-file.")

    rows = [
        analyze_prompt_deepseek(
            prompt,
            model=args.model,
            api_key_file=args.api_key_file,
            cache_path=args.cache,
            refresh_cache=args.refresh_cache,
        )
        for prompt in prompts
    ]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "json":
        output.write_text(json.dumps([asdict(row) for row in rows], indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        write_csv(output, rows)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
